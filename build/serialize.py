"""sources/ -> build/routes.json and build/organizations.json: validate, compute, rate, write.

Usage: uv run python -m build.serialize --release-date 2026-10-08
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from datetime import date
from pathlib import Path

from build.compute import compute_routes
from build.config import METHODOLOGY_VERSION, PUE
from build.energy import EcoLogitsEnergyModel, EnergyModel
from build.grid import latest_grid, load_cloud_regions, load_grid
from build.models import model_ids, model_specs
from build.ranges import Range
from build.rate import rate_orgs, rate_routes
from build.validate import ROOT, load_sources, validate_sources, validation_warnings

# Internal result field -> published field, which carries its unit.
_PUBLISHED_NAMES = {
    "energy_wh": "energy_wh_per_1k_tokens",
    "embodied_g": "embodied_g_per_1k_tokens",
    "operational_direct": "operational_direct_g_per_1k_tokens",
    "operational_lifecycle": "operational_lifecycle_g_per_1k_tokens",
    "score_direct": "score_direct_g_per_1k_tokens",
    "score_lifecycle": "score_lifecycle_g_per_1k_tokens",
    "intensity_direct": "intensity_direct_g_per_kwh",
    "intensity_lifecycle": "intensity_lifecycle_g_per_kwh",
}


def _publish(value):
    """Ranges become {low, high}, tuples become lists, floats are rounded to 6 places."""
    if isinstance(value, Range):
        return _publish(value.to_dict())
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _publish(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_publish(v) for v in value]
    return value


def route_record(result: dict, rating: dict) -> dict:
    record = {_PUBLISHED_NAMES.get(k, k): v for k, v in result.items()}
    record["sort_key"] = result["score_direct"].sort_key() if result["score_direct"] else None
    record["rating"] = rating
    return _publish(record)


def write_outputs(out_dir: Path, results: dict[str, dict], route_ratings: dict[str, dict],
                  org_ratings: dict[str, dict], meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    routes = [route_record(results[name], route_ratings[name]) for name in sorted(results)]
    orgs = [_publish({"org": name, **org_ratings[name]}) for name in sorted(org_ratings)]
    (out_dir / "routes.json").write_text(
        json.dumps({"meta": meta, "routes": routes}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "organizations.json").write_text(
        json.dumps({"meta": meta, "organizations": orgs}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _provenance(data_path: Path, *keys: str) -> dict | None:
    """The named fields of the provenance file written beside an imported snapshot, if there is one."""
    path = data_path.with_name(f"{data_path.stem}.provenance.json")
    if not path.exists():
        return None
    provenance = json.loads(path.read_text(encoding="utf-8"))
    return {k: provenance[k] for k in keys if k in provenance}


def serialize(root: Path, release: date, out_dir: Path, energy_model: EnergyModel, grid_path: Path, cloud_path: Path,
              ecologits_models: list[dict] | None = None, grid_zones_override: set[str] | None = None) -> int:
    """Validate, then compute and write. Returns the number of validation errors; 0 means outputs were written."""
    data = load_sources(root)
    grid = load_grid(grid_path)
    cloud = load_cloud_regions(cloud_path)
    zones = grid_zones_override if grid_zones_override is not None else set(grid)
    errs = validate_sources(data, model_ids=model_ids(data.get("models"), ecologits_models), grid_zones=zones,
                            cloud_regions=cloud)
    for e in errs:
        print("ERROR:", e)
    if errs:
        return len(errs)
    for w in validation_warnings(data, release):
        print("WARNING:", w)
    models = model_specs(data.get("models"), ecologits_models)  # parameters are read only once validated
    results = compute_routes(data, models, grid, cloud, energy_model, release)
    route_ratings = rate_routes(data, results)
    org_ratings = rate_orgs(data, route_ratings)
    meta = {
        "release_date": release.isoformat(),
        "methodology_version": METHODOLOGY_VERSION,
        "ecologits_version": importlib.metadata.version("ecologits"),
        "pue": list(PUE),
        "grid_file": grid_path.name,
        "grid_data": _provenance(grid_path, "year", "retrieved", "licence", "attribution"),
        "cloud_regions": _provenance(cloud_path, "repository", "commit", "retrieved"),
        "score_basis": "Full SCI, (E x I) + M per 1,000 output tokens; E and M from EcoLogits, "
                       "I consumption-based direct factors from Electricity Maps",
    }
    write_outputs(out_dir, results, route_ratings, org_ratings, meta)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.serialize", description="Compute route scores and ratings.")
    parser.add_argument("--release-date", type=date.fromisoformat, required=True)
    parser.add_argument("--grid", type=Path, help="grid CSV (default: newest sources/snapshots/grid/<year>.csv)")
    parser.add_argument("--cloud", type=Path, help="default: sources/snapshots/cloud_regions.csv")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    grid_dir = args.root / "sources" / "snapshots" / "grid"
    grid = args.grid or latest_grid(grid_dir)
    if grid is None:
        print(f"no grid snapshot in {grid_dir}: import one with build.import_grid, or pass --grid "
              "(a mock file is used only when named with --grid)")
        return 1
    if ".MOCK" in grid.name:
        print(f"WARNING: {grid.name} is mock data; nothing built from it may be published")
    cloud = args.cloud or args.root / "sources" / "snapshots" / "cloud_regions.csv"
    errors = serialize(args.root, args.release_date, args.root / "build", EcoLogitsEnergyModel(), grid, cloud)
    print("wrote build/routes.json and build/organizations.json" if errors == 0
          else f"stopped: {errors} validation error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
