"""Every check on sources/: each record against its schema (build/schemas/), the records against each other, and
against the cloud-region data. One message per problem, each naming its file. Nothing here reads a file."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from pydantic import TypeAdapter, ValidationError

from build.load_sources import SOURCE_DIRS
from build.schemas.grid import CheckedGrid
from build.schemas.model import Model
from build.schemas.organization import Organization
from build.schemas.route import CheckedRoute


# What the records in each sources/ folder must look like (build/schemas/), in SOURCE_DIRS order.
_RECORD_TYPES: dict[str, TypeAdapter] = {
    "organizations": TypeAdapter(Organization),
    "grids": TypeAdapter(CheckedGrid),
    "routes": TypeAdapter(CheckedRoute),
    "models": TypeAdapter(Model),
}

_SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")  # a filename stem: lowercase kebab-case
_FIELD = re.compile(r"[a-z_][a-z0-9_]*|\d{4}")  # a field name, or a year keying a grid's values

_RUN_SCORE = "run `python -m build score`"


# Each record: its filename and its schema.


def messages(error: ValidationError) -> list[str]:
    """One message per problem, prefixed with the path of the offending field ("location.evidence[0].shows: ...")."""
    messages = []
    for problem in error.errors():
        path = ""
        for part in problem["loc"]:
            if isinstance(part, int):
                path += f"[{part}]"
            elif _FIELD.fullmatch(part):  # other parts are Pydantic's labels for a union's forms, not fields
                path += f".{part}" if path else part
        message = problem["msg"].removeprefix("Value error, ")
        messages.append(f"{path}: {message}" if path else message)
    return messages


def check_identity(dirname: str, records: dict, record_type: TypeAdapter) -> tuple[list[str], dict]:
    """Each record of one folder has a slug for a filename, passes its schema and names itself by that slug. The
    errors, and the records that passed."""
    errors: list[str] = []
    valid: dict = {}
    for stem, record in records.items():
        where = f"{dirname}/{stem}.yaml"
        if not _SLUG.fullmatch(stem):
            errors.append(f"{where}: filename must be a lowercase kebab-case slug")
            continue
        try:
            record_type.validate_python(record)
        except ValidationError as error:
            errors += [f"{where}: {message}" for message in messages(error)]
            continue
        if record["name"] != stem:
            errors.append(f"{where}: name {record['name']!r} does not match the filename stem {stem!r}")
            continue
        valid[stem] = record
    return errors, valid


# The organizations and models routes name.


def check_orgs(orgs: dict, routes: dict) -> list[str]:
    """Every route names an organization that has a file, and its slug starts with '<org>-'."""
    errors: list[str] = []
    for name, route in routes.items():
        org = route["org"]
        if org not in orgs:
            errors.append(f"routes/{name}.yaml: organization {org!r} has no organizations/{org}.yaml")
        elif not name.startswith(f"{org}-"):
            errors.append(f"routes/{name}.yaml: name must start with {org + '-'!r}, its organization's slug")
    return errors


def check_models(routes: dict, models: dict) -> list[str]:
    """Every route names a model that has a file."""
    return [
        f"routes/{name}.yaml: model {route['model']!r} has no sources/models/{route['model']}.yaml; "
        "add one (docs/workflows/add-model.md)"
        for name, route in routes.items()
        if route["model"] not in models
    ]


# Grids: one file per zone, each with its intensity written, each used by a route.


def check_zones(grids: dict) -> list[str]:
    """No two grid files claim one zone code."""
    errors: list[str] = []
    claimed: dict[str, str] = {}
    for name, grid in sorted(grids.items()):
        if "zone" not in grid:
            continue
        zone = grid["zone"]
        if zone in claimed:
            errors.append(f"grids/{name}.yaml: zone {zone!r} is also claimed by grids/{claimed[zone]}.yaml")
        else:
            claimed[zone] = name
    return errors


def check_grid_intensities(grids: dict) -> list[str]:
    """Every grid has its intensity:, written at curation time by `python -m build grid-emissions`
    (build/grid_emissions.py; CI runs grid-emissions without --write to check each against Ember's table)."""
    return [
        f"grids/{name}.yaml: has no intensity; run `python -m build grid-emissions --write {name}`"
        for name, grid in sorted(grids.items())
        if "intensity" not in grid
    ]


def check_unused_grids(grids: dict, used: set[str]) -> list[str]:
    """Every grid file is one a route uses."""
    return [f"grids/{name}.yaml: no route uses this grid; remove it" for name in sorted(grids) if name not in used]


# Routes: their candidates resolve to grid files; one default per organization and model.


def check_candidates(
    routes: dict, all_grids: dict, cloud_regions: Mapping[tuple[str, str], list[str]] | None
) -> tuple[list[str], set[str]]:
    """Every route's candidates resolve to grid files that exist (valid or not, so an invalid file is reported only
    once): a grid: candidate to its file, a cloud: candidate through the cloud-region data and its zones (checked only
    with that data). One message per candidate that does not resolve, and the grids the others resolve to."""
    errors: list[str] = []
    used: set[str] = set()
    # Every grid file that names a zone, valid or not: a malformed grid file is reported once, by its schema check.
    zones = {
        grid["zone"]: name
        for name, grid in all_grids.items()
        if isinstance(grid, Mapping) and isinstance(grid.get("zone"), str)
    }
    for name, route in routes.items():
        where = f"routes/{name}.yaml"
        for candidate in route["location"]["candidates"]:
            kind, _, rest = candidate.partition(":")
            if kind == "grid":
                if rest in all_grids:
                    used.add(rest)
                else:
                    errors.append(f"{where}: grid {rest!r} has no grids/{rest}.yaml")
            elif cloud_regions is not None:
                vendor, _, region = rest.partition(":")
                if (vendor, region) not in cloud_regions:
                    errors.append(f"{where}: cloud region {vendor}:{region} is not in the cloud-region data")
                    continue
                for zone in cloud_regions[(vendor, region)]:
                    if zone in zones:
                        used.add(zones[zone])
                    else:
                        errors.append(
                            f"{where}: cloud region {vendor}:{region} maps to zone {zone!r}, which has no "
                            "grid file; add one (docs/workflows/add-grid.md)"
                        )
    return errors, used


def check_defaults(routes: dict) -> list[str]:
    """At most one route per organization and model is marked default."""
    errors: list[str] = []
    first_default: dict[tuple[str, str], str] = {}
    for name, route in sorted(routes.items()):
        if not route.get("default"):
            continue
        key = (route["org"], route["model"])
        if key in first_default:
            errors.append(
                f"organizations/{route['org']}.yaml: routes {first_default[key]} and {name} are both marked "
                f"default for model {route['model']!r}"
            )
        else:
            first_default[key] = name
    return errors


# The two entry points.


def validate_sources(
    data: Mapping[str, Any],
    *,
    cloud_regions: Mapping[tuple[str, str], list[str]] | None = None,
) -> list[str]:
    """Every problem in the corpus, one message per problem, each naming the file it is in.

    The optional cloud_regions ((vendor, region) -> zone codes, which grid files claim) switches on the check against
    outside data: with it, an unused grid file is an error.
    """
    errors = [
        f"{path}: only <slug>.yaml files belong in sources/{path.split('/')[0]}/"
        for path in data.get("stray_files", [])
    ]
    valid: dict = {}
    for dirname in SOURCE_DIRS:
        identity_errors, valid[dirname] = check_identity(dirname, data.get(dirname) or {}, _RECORD_TYPES[dirname])
        errors += identity_errors

    # Cross-file checks read only records that passed their schema, so a malformed file is reported once; the files
    # they look up (organizations, grids, models) count whether valid or not, for the same reason.
    grids, routes = valid["grids"], valid["routes"]
    errors += check_orgs(data.get("organizations") or {}, routes)
    errors += check_models(routes, data.get("models") or {})
    errors += check_zones(grids)
    errors += check_grid_intensities(grids)
    candidate_errors, used = check_candidates(routes, data.get("grids") or {}, cloud_regions)
    errors += candidate_errors
    errors += check_defaults(routes)
    if cloud_regions is not None and len(routes) == len(data.get("routes") or {}):
        # Only when every route passed its schema: a malformed route would make its grid look unused.
        errors += check_unused_grids(grids, used)
    return errors


def check_stored_scores(data: Mapping[str, Any]) -> list[str]:
    """Every organization has its disclosure_rating: and every route its disclosure_rating: and carbon_score:, the
    fields `python -m build score` writes. Call on data validate_sources passed: their shape is checked there."""
    return [
        f"organizations/{name}.yaml: is missing the disclosure_rating field; {_RUN_SCORE}"
        for name, org in sorted(data["organizations"].items())
        if "disclosure_rating" not in org
    ] + [
        f"routes/{name}.yaml: is missing the {key} field; {_RUN_SCORE}"
        for name, route in sorted(data["routes"].items())
        for key in ("disclosure_rating", "carbon_score")
        if key not in route
    ]
