"""Read an organization's serving-locations file (ai-emissions-map/serving-locations/v1).

Checks the file against docs/schemas/serving-locations.v1.schema.json, works out the location level
each model's default routing discloses, and compares that with the routes curated for the organization.
It proposes; it never edits sources/. A curator who accepts a proposal cites the file as primary
evidence on the route, like any other page.

Level per model (the least precise entry decides):
  every entry names a facility with its operator and city  -> facility (A)
  every entry names at least a region                       -> region (B)
  every entry names at least a country, all the same one    -> country (C)
  entries name several countries without regions/facilities -> country_set (D)
  an entry names nothing, the model is absent, or the file has expired -> unknown (E)

Usage:
    uv run python -m build.disclosure https://example.ai/.well-known/ai-serving-locations.json
    uv run python -m build.disclosure saved-file.json --org multihost
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import jsonschema

from build.config import LOCATION_PRECISION_SCORE
from build.validate import ROOT, _schema_msg, load_sources

SCHEMA = ROOT / "docs" / "schemas" / "serving-locations.v1.schema.json"


class DisclosureError(Exception):
    pass


def _models(doc: dict):
    for i, service in enumerate(doc["services"]):
        for j, model in enumerate(service["models"]):
            yield f"services[{i}].models[{j}]", model


def check_disclosure(doc: dict, today: date) -> list[str]:
    """Every problem with the file, one message each. An expired file is a problem: it rates nothing."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = [_schema_msg(e) if e.json_path != "$" else f"(root): {e.message}"
              for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: e.json_path)]
    if errors:
        return errors
    if doc["valid_until"] < doc["published"]:
        errors.append(f"valid_until {doc['valid_until']} is before published {doc['published']}")
    elif date.fromisoformat(doc["valid_until"]) < today:
        errors.append(f"valid_until {doc['valid_until']} has passed")
    for where, model in _models(doc):
        share = sum(e.get("share_of_traffic", 0) for e in model["default_routing"])
        if share > 1 + 1e-9:
            errors.append(f"{where} ({model['model']}): share_of_traffic adds up to {round(share, 6)}")
    return errors


def _entry_level(entry: dict) -> str:
    if entry.get("facility") and entry.get("operator") and entry.get("city"):
        return "facility"
    if entry.get("region"):
        return "region"
    if entry.get("country"):
        return "country"
    return "unknown"


def model_levels(doc: dict, today: date) -> dict[str, dict]:
    """Model -> {"level", "zones", "served_as"} for each model the file lists; empty once it has expired."""
    if date.fromisoformat(doc["valid_until"]) < today:
        return {}
    levels = {}
    for _, model in _models(doc):
        routing = model["default_routing"]
        level = min((_entry_level(e) for e in routing), key=LOCATION_PRECISION_SCORE.get)
        if level == "country" and len({e["country"] for e in routing if e.get("country")}) > 1:
            level = "country_set"
        levels[model["model"]] = {"level": level, "zones": sorted({e["grid_zone"] for e in routing if e.get("grid_zone")}),
                                  "served_as": model.get("served_as")}
    return levels


def compare_with_routes(doc: dict, today: date, org: str, data: dict) -> list[dict]:
    """For each of the organization's located routes: the curated confidence next to what the file discloses."""
    levels = model_levels(doc, today)
    by_label = {}
    for model, info in levels.items():
        by_label[model] = info
        if info["served_as"]:
            by_label[info["served_as"]] = info
    if org not in data["organizations"]:
        raise DisclosureError(f"no organization {org!r} in sources/organizations/")
    rows = []
    for name in data["organizations"][org]["routes"]:
        route = data["routes"][name]
        if not route.get("location"):
            continue
        info = by_label.get(route.get("served_as") or route["model"]) or by_label.get(route["model"])
        rows.append({"route": name, "model": route["model"], "curated": route["location"]["confidence"],
                     "disclosed": info["level"] if info else "unknown", "disclosed_zones": info["zones"] if info else []})
    return rows


def _load(source: str) -> dict:
    """The file at a URL or path, parsed. Anything that is not a JSON object is a DisclosureError."""
    if source.startswith("https://") or source.startswith("http://"):
        import requests

        from build.fetch_source import USER_AGENT

        try:
            response = requests.get(source, headers={"User-Agent": USER_AGENT}, timeout=30)
        except requests.RequestException as err:
            raise DisclosureError(f"{source}: {type(err).__name__}: {err}") from None
        if response.status_code >= 400:
            raise DisclosureError(f"{source}: HTTP {response.status_code}")
        text = response.text
    else:
        text = Path(source).read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as err:
        raise DisclosureError(f"{source}: not a JSON document ({err})") from None
    if not isinstance(doc, dict):
        raise DisclosureError(f"{source}: not a JSON object")
    return doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.disclosure", description=__doc__.splitlines()[0])
    parser.add_argument("source", help="a URL or a saved copy of a serving-locations file")
    parser.add_argument("--org", help="compare with this organization's curated routes")
    args = parser.parse_args(argv)
    try:
        doc = _load(args.source)
    except DisclosureError as err:
        print("ERROR:", err)
        return 1
    today = date.today()
    errors = check_disclosure(doc, today)
    for e in errors:
        print("ERROR:", e)
    if errors and not doc.get("services"):
        return 1
    for model, info in sorted(model_levels(doc, today).items()):
        print(f"{model}: {info['level']}  zones={','.join(info['zones']) or '-'}")
    if args.org:
        try:
            rows = compare_with_routes(doc, today, args.org, load_sources(ROOT))
        except DisclosureError as err:
            print("ERROR:", err)
            return 1
        for row in rows:
            flag = "" if row["disclosed"] == row["curated"] else "   <- differs"
            print(f"{row['route']}: curated {row['curated']}, file says {row['disclosed']}{flag}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
