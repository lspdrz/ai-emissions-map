"""sources/ -> web/data/data.json and web/data/methodology.md: everything the website is built from.

The data file holds only what the website displays (ruling R-2026-10-12-b): per-route results, ratings,
evidence quotes, model facts and release metadata. Never grid intensities or the zone table. It is
committed, and flagged as a mock while the grid data is one.

Usage:
    uv run python -m build.export --release-date 2026-10-12 --grid sources/snapshots/grid/2025.MOCK.csv
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from build.config import CARBON_BAND_UPPER
from build.energy import EcoLogitsEnergyModel, EnergyModel
from build.grid import latest_grid
from build.serialize import _publish, compute_release, route_record
from build.validate import ROOT

SCHEMA = "aem-data/1"
_QUOTED = re.compile(r'"([^"]{8,})"')
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.S)


class ExportError(Exception):
    pass


# The contract: every field the data file may hold, and nothing else (ruling R-2026-10-12-b). The
# export refuses to write anything outside it, and a repository test checks the committed file against
# it, so no grid value can reach the repository or the website by accident.
ALLOWED_KEYS = {
    "": {"schema", "meta", "organizations", "models", "routes"},
    "meta": {"release_date", "methodology_version", "ecologits_version", "pue", "band_upper", "grid", "counts",
             "intensity_spread", "featured_model"},
    "meta.grid": {"year", "mock", "attribution"},
    "meta.counts": {"organizations", "routes", "models", "zones", "scored"},
    "organizations[]": {"slug", "display_name", "type", "country", "homepage", "description", "notified", "rating",
                        "routes", "evidence"},
    "organizations[].rating": {"letter", "mean", "spread", "summary"},
    "organizations[].evidence[]": {"url", "quotes", "accessed", "routes"},
    "models[]": {"slug", "display_name", "source", "architecture", "active_b", "total_b"},
    "routes[]": {"slug", "org", "model", "label", "default", "scored", "level", "letter", "gap", "score", "embodied",
                 "band", "served_as"},
}


def check_contract(data: dict) -> list[str]:
    """Every field outside ALLOWED_KEYS, one message each; empty when the data keeps to the contract."""
    problems: list[str] = []

    def check(obj, where: str) -> None:
        if not isinstance(obj, dict):
            return
        extra = sorted(set(obj) - ALLOWED_KEYS[where])
        problems.extend(f"{where or 'top level'}: field {k!r} is not in the contract" for k in extra)

    check(data, "")
    meta = data.get("meta", {})
    check(meta, "meta")
    check(meta.get("grid"), "meta.grid")
    check(meta.get("counts"), "meta.counts")
    for org in data.get("organizations", []):
        check(org, "organizations[]")
        check(org.get("rating"), "organizations[].rating")
        for e in org.get("evidence", []):
            check(e, "organizations[].evidence[]")
    for m in data.get("models", []):
        check(m, "models[]")
    for r in data.get("routes", []):
        check(r, "routes[]")
    return problems


def _grid_meta(grid_path: Path) -> dict:
    prov_path = grid_path.with_name(f"{grid_path.stem}.provenance.json")
    prov = json.loads(prov_path.read_text(encoding="utf-8")) if prov_path.exists() else {}
    return {"year": prov.get("year"), "mock": bool(prov.get("mock")) or ".MOCK" in grid_path.name,
            "attribution": prov.get("attribution")}


def _label(route: dict, record: dict) -> str:
    location = route.get("location")
    if location is None:
        return f"Through {len(route.get('upstreams', []))} other providers"
    if location.get("label"):
        return location["label"]
    if location["confidence"] == "unknown" or not record["zones"]:
        return "Not disclosed"
    n = len(record["zones"])
    return f"{n} grid zone" if n == 1 else f"{n} grid zones"


def _evidence(data: dict, routes: list[str]) -> list[dict]:
    by_url: dict[str, dict] = {}
    for name in routes:
        for e in (data["routes"][name].get("location") or {}).get("evidence", []):
            if e["kind"] != "primary":
                continue
            item = by_url.setdefault(e["url"], {"url": e["url"], "quotes": [], "accessed": e["accessed"], "routes": []})
            item["quotes"] += [q for q in _QUOTED.findall(e["shows"]) if q not in item["quotes"]]
            item["accessed"] = max(item["accessed"], e["accessed"])
            if name not in item["routes"]:
                item["routes"].append(name)
    return [by_url[url] for url in sorted(by_url)]


def build_data(rel: dict, grid_path: Path) -> dict:
    data, results, meta = rel["data"], rel["results"], rel["meta"]
    records = {name: route_record(results[name], rel["route_ratings"][name]) for name in sorted(results)}
    routes = []
    for name, rec in records.items():
        r = data["routes"][name]
        routes.append({
            "slug": name, "org": rec["org"], "model": rec["model"], "label": _label(r, rec),
            "default": bool(r.get("default")), "scored": rec["scored"], "level": rec["rating"]["level"],
            "letter": rec["rating"]["letter"], "gap": rec["rating"]["gap"],
            "score": rec["score_direct_g_per_1k_tokens"], "embodied": rec["embodied_g_per_1k_tokens"],
            "band": rec["band"], "served_as": rec.get("served_as"),
        })
    orgs = []
    for slug in sorted(data["organizations"]):
        o, rating = data["organizations"][slug], rel["org_ratings"][slug]
        orgs.append({
            "slug": slug, "display_name": o["display_name"], "type": o["type"], "country": o.get("country"),
            "homepage": o["homepage"], "description": o.get("description"),
            "notified": (o.get("contact") or {}).get("notified"),
            "rating": _publish({k: rating[k] for k in ("letter", "mean", "spread", "summary")}),
            "routes": rating["routes"], "evidence": _evidence(data, rating["routes"]),
        })
    used = Counter(r["model"] for r in routes)
    models = [{"slug": m, "display_name": data["models"].get(m, {}).get("display_name", m),
               "source": data["models"].get(m, {}).get("source"),
               "architecture": data["models"].get(m, {}).get("architecture"),
               "active_b": data["models"].get(m, {}).get("active_b"),
               "total_b": data["models"].get(m, {}).get("total_b")} for m in sorted(used)]
    scored = [rec for rec in records.values() if rec["scored"]]
    lows = [rec["intensity_direct_g_per_kwh"]["low"] for rec in scored]
    highs = [rec["intensity_direct_g_per_kwh"]["high"] for rec in scored]
    spread = round(max(highs) / min(lows)) if scored and min(lows) > 0 else None
    return {
        "schema": SCHEMA,
        "meta": {
            "release_date": meta["release_date"], "methodology_version": meta["methodology_version"],
            "ecologits_version": meta["ecologits_version"], "pue": meta["pue"],
            "band_upper": list(CARBON_BAND_UPPER), "grid": _grid_meta(grid_path),
            "counts": {"organizations": len(orgs), "routes": len(routes), "models": len(models),
                       "zones": len({z for rec in records.values() for z in rec["zones"]}),
                       "scored": len(scored)},
            "intensity_spread": spread,
            "featured_model": min(used, key=lambda m: (-used[m], m)) if used else None,
        },
        "organizations": orgs, "models": models, "routes": routes,
    }


def fill_methodology(text: str, values: dict) -> str:
    """Strip the authoring comment and fill every {placeholder}; an unknown one is an error."""
    body = _COMMENT.sub("", text, count=1)
    unknown = sorted({p for p in _PLACEHOLDER.findall(body) if p not in values})
    if unknown:
        raise ExportError(f"docs/methodology.md uses placeholders the export does not fill: {', '.join(unknown)}")
    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), body)


def _methodology_values(map_data: dict) -> dict:
    meta, routes = map_data["meta"], map_data["routes"]
    return {
        "release_date": meta["release_date"], "methodology_version": meta["methodology_version"],
        "ecologits_version": meta["ecologits_version"], "grid_year": meta["grid"]["year"] or "the latest year",
        "n_orgs": meta["counts"]["organizations"], "n_routes": meta["counts"]["routes"],
        "n_models": meta["counts"]["models"], "n_scored": meta["counts"]["scored"],
        "n_unscored": meta["counts"]["routes"] - meta["counts"]["scored"],
        "n_rated_a_or_b": sum(1 for o in map_data["organizations"] if o["rating"]["letter"] in ("A", "B")),
    }


def export(root: Path, release: date, out_dir: Path, energy_model: EnergyModel, grid_path: Path,
                cloud_path: Path, methodology_path: Path, ecologits_models: list[dict] | None = None) -> int:
    """Validate, compute and write the website's data. Returns the number of validation errors; 0 means written."""
    errors, rel = compute_release(root, release, energy_model, grid_path, cloud_path, ecologits_models)
    if errors:
        return errors
    map_data = build_data(rel, grid_path)
    problems = check_contract(map_data)
    if problems:
        raise ExportError("the data file would leave its contract: " + "; ".join(problems))
    methodology = fill_methodology(methodology_path.read_text(encoding="utf-8"), _methodology_values(map_data))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data.json").write_text(json.dumps(map_data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    (out_dir / "methodology.md").write_text(methodology, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.export", description=__doc__.splitlines()[0])
    parser.add_argument("--release-date", type=date.fromisoformat, required=True)
    parser.add_argument("--grid", type=Path, help="grid CSV (default: newest sources/snapshots/grid/<year>.csv)")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    grid = args.grid or latest_grid(args.root / "sources" / "snapshots" / "grid")
    if grid is None:
        print("no grid snapshot: import one with build.import_grid, or pass --grid")
        return 1
    try:
        errors = export(args.root, args.release_date, args.root / "web" / "data", EcoLogitsEnergyModel(), grid,
                             args.root / "sources" / "snapshots" / "cloud_regions.csv",
                             args.root / "docs" / "methodology.md")
    except ExportError as e:
        print(f"ERROR: {e}")
        return 1
    if errors:
        print(f"stopped: {errors} validation error(s)")
        return 1
    note = " (MOCK grid data: the website will show its draft bar)" if _grid_meta(grid)["mock"] else ""
    print(f"wrote web/data/data.json and web/data/methodology.md{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
