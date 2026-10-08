"""Load sources/ and validate it: schemas, identity (filename stem = slug), rosters and aliases."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

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


def validate_sources(data: dict, *, root: Path = ROOT) -> list[str]:
    """Every problem in the corpus, one message per problem, each naming the file it is in."""
    schemas = _load_schemas(root)
    errors = [f"{path}: only <slug>.yaml files belong in sources/{path.split('/')[0]}/"
              for path in data.get("stray_files", [])]
    valid: dict = {}
    for dirname, schema_name in _SCHEMA_FOR_DIR.items():
        errs, valid[dirname] = _check_identity(dirname, data.get(dirname) or {}, schemas[schema_name])
        errors += errs
        errors += _check_aliases(dirname, valid[dirname])
    errors += _check_rosters(valid["organizations"], data.get("routes") or {})
    return errors


if __name__ == "__main__":
    errs = validate_sources(load_sources(ROOT))
    for e in errs:
        print("ERROR:", e)
    print(f"{len(errs)} error(s)")
    sys.exit(1 if errs else 0)
