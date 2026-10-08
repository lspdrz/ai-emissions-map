"""Load sources/ and validate it: schemas, identity (filename stem = slug), rosters and aliases."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

import jsonschema
import yaml

from build.evidence import location_established

ROOT = Path(__file__).resolve().parents[1]

# Maps each sources/ subdir to its docs/schemas/<name>.schema.json basename.
_SCHEMA_FOR_DIR = {
    "organizations": "organization",
    "facilities": "facility",
    "routes": "route",
    "models": "model",
}
_SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def _schema_msg(e: jsonschema.ValidationError) -> str:
    """Prefix a schema error with the path of the offending field ("location.evidence[0].shows: ...")."""
    path = e.json_path[2:] if e.json_path.startswith("$.") else ""
    return f"{path}: {e.message}" if path else e.message


def _load_schemas(root: Path) -> dict:
    schema_dir = root / "docs" / "schemas"
    return {
        name: json.loads((schema_dir / f"{name}.schema.json").read_text())
        for name in set(_SCHEMA_FOR_DIR.values())
    }


def load_sources(root: Path) -> dict:
    """Every sources/<dir>/<slug>.yaml keyed by its filename stem, plus anything that is not one.

    `stray_files` lists entries that would otherwise be skipped silently (a .yml file, a subfolder),
    so validate_sources can report them. Dotfiles such as .DS_Store are ignored.
    """
    sources = root / "sources"
    data: dict = {"stray_files": []}
    for name in _SCHEMA_FOR_DIR:
        records = {}
        directory = sources / name
        for p in sorted(directory.iterdir()) if directory.is_dir() else []:
            if p.name.startswith("."):
                continue
            if p.is_file() and p.suffix == ".yaml":
                records[p.stem] = yaml.safe_load(p.read_text(encoding="utf-8"))
            else:
                data["stray_files"].append(p.relative_to(sources).as_posix())
        data[name] = records
    return data


def route_owners(orgs: dict) -> dict[str, str]:
    """Route slug -> the organization whose `routes:` roster lists it."""
    owners: dict[str, str] = {}
    for org, d in orgs.items():
        for route in d.get("routes") or []:
            owners.setdefault(route, org)
    return owners


def _check_identity(dirname: str, records: dict, schema: dict) -> tuple[list[str], dict]:
    """Schema and filename checks for one directory. Returns the errors and the records that passed."""
    errors: list[str] = []
    valid: dict = {}
    for stem, rec in records.items():
        where = f"{dirname}/{stem}.yaml"
        if not _SLUG.fullmatch(stem):
            errors.append(f"{where}: filename must be a lowercase kebab-case slug")
            continue
        schema_errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(rec), key=lambda e: e.json_path)
        if schema_errors:
            errors += [f"{where}: {_schema_msg(e)}" for e in schema_errors]
            continue
        if rec["name"] != stem:
            errors.append(f"{where}: name {rec['name']!r} does not match the filename stem {stem!r}")
            continue
        valid[stem] = rec
    return errors, valid


def _check_aliases(dirname: str, records: dict) -> list[str]:
    """An alias may not be a live slug, and no two records may claim the same alias."""
    errors: list[str] = []
    claimed: dict[str, str] = {}
    for stem, rec in records.items():
        for alias in rec.get("aliases") or []:
            if alias in records:
                errors.append(f"{dirname}/{stem}.yaml: alias {alias!r} is the live slug of {dirname}/{alias}.yaml")
            elif alias in claimed:
                errors.append(f"{dirname}/{stem}.yaml: alias {alias!r} is also claimed by {dirname}/{claimed[alias]}.yaml")
            else:
                claimed[alias] = stem
    return errors


def _check_rosters(orgs: dict, routes: dict) -> list[str]:
    """Every route is on exactly one organization's roster, and its slug starts with '<org>-'."""
    errors: list[str] = []
    owners: dict[str, str] = {}
    for org, d in orgs.items():
        for route in d["routes"]:
            if route not in routes:
                errors.append(f"organizations/{org}.yaml: roster lists {route!r}, which has no routes/{route}.yaml")
            elif route in owners:
                errors.append(f"routes/{route}.yaml: on the rosters of both {owners[route]!r} and {org!r}; "
                              "a route belongs to exactly one organization")
            else:
                owners[route] = org
    for route in routes:
        org = owners.get(route)
        if org is None:
            errors.append(f"routes/{route}.yaml: on no organization's roster")
        elif not route.startswith(f"{org}-"):
            errors.append(f"routes/{route}.yaml: name must start with {org + '-'!r}, its organization's slug")
    return errors


def _primary(items: list | None) -> bool:
    return any(e["kind"] == "primary" for e in items or [])


def _check_route_shape(routes: dict) -> list[str]:
    errors = []
    for name, r in routes.items():
        if r.get("location") is None and not r.get("upstreams"):
            errors.append(f"routes/{name}.yaml: route needs either a location or upstreams")
        if r.get("location") is not None and r.get("upstreams"):
            errors.append(f"routes/{name}.yaml: route cannot have both a location and upstreams")
    return errors


def _check_references(facilities: dict, routes: dict, all_routes: dict, grid_zones: set[str] | None,
                      cloud_regions: dict[tuple[str, str], str] | None) -> list[str]:
    errors = []
    for name, f in facilities.items():
        if grid_zones is not None and f["grid_zone"] not in grid_zones:
            errors.append(f"facilities/{name}.yaml: grid zone {f['grid_zone']!r} is not in the grid data")
    for name, r in routes.items():
        where = f"routes/{name}.yaml"
        for u in r.get("upstreams") or []:
            if u["route"] not in all_routes:
                errors.append(f"{where}: upstream route {u['route']!r} has no routes/{u['route']}.yaml")
            elif u["route"] in routes and routes[u["route"]]["model"] != r["model"]:
                errors.append(f"{where}: upstream route {u['route']!r} serves model "
                              f"{routes[u['route']]['model']!r}, not {r['model']!r}")
        for cand in (r.get("location") or {}).get("candidates", []):
            kind, _, rest = cand.partition(":")
            if kind == "facility" and rest not in facilities:
                errors.append(f"{where}: facility {rest!r} has no facilities/{rest}.yaml")
            elif kind == "cloud":
                vendor, _, region = rest.partition(":")
                if cloud_regions is None:
                    continue
                if (vendor, region) not in cloud_regions:
                    errors.append(f"{where}: cloud region {vendor}:{region} is not in the cloud-region data")
                elif grid_zones is not None and cloud_regions[(vendor, region)] not in grid_zones:
                    errors.append(f"{where}: cloud region {vendor}:{region} maps to grid zone "
                                  f"{cloud_regions[(vendor, region)]!r}, which is not in the grid data")
            elif kind == "zone" and grid_zones is not None and rest not in grid_zones:
                errors.append(f"{where}: grid zone {rest!r} is not in the grid data")
    return errors


def _check_evidence(facilities: dict, routes: dict) -> list[str]:
    errors = []
    for name, r in routes.items():
        where = f"routes/{name}.yaml"
        loc = r.get("location")
        if loc and loc["confidence"] != "unknown":
            if not _primary(loc["evidence"]):
                errors.append(f"{where}: confidence {loc['confidence']!r} needs at least one primary source")
            if not loc["candidates"]:
                errors.append(f"{where}: confidence {loc['confidence']!r} needs at least one candidate")
            errors += _check_confidence_supported(where, loc)
        if r.get("upstreams") and not _primary(r.get("upstream_evidence")):
            errors.append(f"{where}: upstream weights need a primary source")
    for name, f in facilities.items():
        if not _primary(f["location_evidence"]):
            errors.append(f"facilities/{name}.yaml: facility location needs a primary source")
    return errors


# The precision a candidate kind can support: a confidence may not claim more than its candidates show.
_CANDIDATES_FOR = {"facility": ("facility",), "region": ("facility", "cloud")}


def _check_confidence_supported(where: str, loc: dict) -> list[str]:
    allowed = _CANDIDATES_FOR.get(loc["confidence"])
    if allowed is None or all(c.partition(":")[0] in allowed for c in loc["candidates"]):
        return []
    kinds = " or ".join(f"{k}:" for k in allowed)
    return [f"{where}: confidence {loc['confidence']!r} needs every candidate to be a {kinds} candidate"]


def _check_models(routes: dict, model_ids: set[str] | None) -> list[str]:
    errors = []
    for name, r in routes.items():
        where = f"routes/{name}.yaml"
        if model_ids is not None and r["model"] not in model_ids:
            errors.append(f"{where}: model {r['model']!r} is not in EcoLogits or sources/models/")
        if r.get("served_as") and r["served_as"] != r["model"] and not r.get("served_model_evidence"):
            errors.append(f"{where}: served_as {r['served_as']!r} differs from model {r['model']!r}; "
                          "add served_model_evidence")
    return errors


def _check_upstream_cycles(routes: dict) -> list[str]:
    errors: list[str] = []
    state: dict[str, str] = {}

    def visit(name: str, path: list[str]) -> None:
        if state.get(name) == "done":
            return
        if state.get(name) == "active":
            loop = path[path.index(name):] + [name]
            errors.append(f"routes/{name}.yaml: upstream cycle {' -> '.join(loop)}")
            return
        state[name] = "active"
        for u in routes[name].get("upstreams") or []:
            if u["route"] in routes:
                visit(u["route"], path + [name])
        state[name] = "done"

    for name in sorted(routes):
        visit(name, [])
    return errors


def _check_gap_map_ids(orgs: dict, gap_map_orgs: set[str]) -> list[str]:
    return [f"organizations/{name}.yaml: ids.gap_map {o['ids']['gap_map']!r} is not in the pinned os-ai-map release"
            for name, o in orgs.items()
            if o["ids"].get("gap_map") and o["ids"]["gap_map"] not in gap_map_orgs]


def validate_sources(data: dict, *, model_ids: set[str] | None = None, grid_zones: set[str] | None = None,
                     cloud_regions: dict[tuple[str, str], str] | None = None, gap_map_orgs: set[str] | None = None,
                     root: Path = ROOT) -> list[str]:
    """Every problem in the corpus, one message per problem, each naming the file it is in.

    The optional sets switch on the checks against outside data: model_ids (EcoLogits plus sources/models/),
    grid_zones (the grid snapshot), cloud_regions ((vendor, region) -> grid zone) and gap_map_orgs (the pinned os-ai-map release).
    """
    schemas = _load_schemas(root)
    errors = [f"{path}: only <slug>.yaml files belong in sources/{path.split('/')[0]}/"
              for path in data.get("stray_files", [])]
    valid: dict = {}
    for dirname, schema_name in _SCHEMA_FOR_DIR.items():
        errs, valid[dirname] = _check_identity(dirname, data.get(dirname) or {}, schemas[schema_name])
        errors += errs
        errors += _check_aliases(dirname, valid[dirname])
    errors += _check_rosters(valid["organizations"], data.get("routes") or {})
    # Cross-file checks read only records that passed their schema, so a malformed file is reported once.
    facilities, routes = valid["facilities"], valid["routes"]
    errors += _check_route_shape(routes)
    errors += _check_references(facilities, routes, data.get("routes") or {}, grid_zones, cloud_regions)
    errors += _check_evidence(facilities, routes)
    errors += _check_models(routes, model_ids)
    errors += _check_upstream_cycles(routes)
    if gap_map_orgs is not None:
        errors += _check_gap_map_ids(valid["organizations"], gap_map_orgs)
    return errors


def validation_warnings(data: dict, release_date: date | None = None) -> list[str]:
    """Problems that do not stop a release. Call on data that validate_sources passed."""
    warnings = [f"organizations/{name}.yaml: has no routes and will not be rated"
                for name, o in sorted(data["organizations"].items()) if not o["routes"]]
    if release_date is not None:
        warnings += [f"routes/{name}.yaml: no primary location evidence verified within the window for "
                     f"{release_date.isoformat()}; the route will be treated as unknown"
                     for name, r in sorted(data["routes"].items())
                     if r.get("location") and r["location"]["confidence"] != "unknown"
                     and not location_established(r["location"], release_date)]
    return warnings


def _csv_values(path: Path, *columns: str) -> set:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(columns) == 1:
        return {row[columns[0]] for row in rows}
    return {tuple(row[c] for c in columns) for row in rows}


def main(argv: list[str] | None = None) -> int:
    from build.grid import load_cloud_regions
    from build.models import model_ids

    parser = argparse.ArgumentParser(prog="python -m build.validate", description="Validate sources/.")
    parser.add_argument("--release-date", type=date.fromisoformat, help="also warn about stale location evidence")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    root = args.root
    data = load_sources(root)
    snapshots = root / "sources" / "snapshots"
    grid_path = max((snapshots / "grid").glob("*.csv"), default=None)
    cloud_path = root / "sources" / "cloud_regions.csv"
    pin_path = snapshots / "os-ai-map.pin.json"
    errs = validate_sources(
        data,
        model_ids=model_ids(data.get("models")),
        grid_zones=_csv_values(grid_path, "zone") if grid_path else None,
        cloud_regions=load_cloud_regions(cloud_path) if cloud_path.exists() else None,
        gap_map_orgs=set(json.loads(pin_path.read_text())["org_slugs"]) if pin_path.exists() else None,
        root=root,
    )
    for e in errs:
        print("ERROR:", e)
    warns = [] if errs else validation_warnings(data, args.release_date)
    for w in warns:
        print("WARNING:", w)
    print(f"{len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
