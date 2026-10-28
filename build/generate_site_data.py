"""The website's data: web/data/data.json, copied from the fields `python -m build score` writes in sources/, under
its contract.

The data file holds only what the site displays: per-route results (each carbon intensity with its energy E, grid intensity I
and embodied part M), ratings, evidence quotes, model facts and release metadata.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from datetime import date
from importlib.metadata import version
from typing import Any

from build.constants.config import CARBON_BAND_UPPER, DRAFT, GRID_YEAR, METHODOLOGY_VERSION, FALLBACK_PUE


SCHEMA = "aem-data/4"

# A passage quoted in an evidence entry's `shows`: double quotes around at least 8 characters.
_QUOTED = re.compile(r'"([^"]{8,})"')


# The contract: every field the data file may hold, and nothing else. The release refuses to write anything
# outside it, and the CI gate check-site-data checks the committed file against it.
ALLOWED_KEYS = {
    "": {"schema", "meta", "organizations", "models", "routes"},
    "meta": {
        "release_date",
        "inputs_sha",
        "methodology_version",
        "ecologits_version",
        "pue",
        "band_upper",
        "draft",
        "grid",
        "counts",
        "grid_intensity_spread",
        "featured_model",
    },
    "meta.grid": {"source", "year"},
    "meta.counts": {"organizations", "routes", "models", "grids"},
    "organizations[]": {
        "slug",
        "display_name",
        "type",
        "country",
        "homepage",
        "description",
        "rating",
        "routes",
        "evidence",
    },
    "organizations[].rating": {"letter", "mean", "spread", "summary"},
    "organizations[].evidence[]": {"url", "quotes", "accessed", "routes"},
    "models[]": {"slug", "display_name", "architecture", "active_b", "total_b"},
    "routes[]": {
        "slug",
        "org",
        "model",
        "label",
        "default",
        "letter",
        "gap",
        "sci",
        "energy",
        "grid_intensity",
        "embodied",
        "band",
        "served_as",
    },
}


def check_contract(data: dict) -> list[str]:
    """Every field outside ALLOWED_KEYS, one message each; empty when the data keeps to the contract."""
    problems: list[str] = []

    def check(obj, where: str) -> None:
        if not isinstance(obj, dict):
            return
        extra = sorted(set(obj) - ALLOWED_KEYS[where])
        problems.extend(f"{where or 'top level'}: field {key!r} is not in the contract" for key in extra)

    check(data, "")
    meta = data.get("meta", {})
    check(meta, "meta")
    check(meta.get("grid"), "meta.grid")
    check(meta.get("counts"), "meta.counts")
    for org in data.get("organizations", []):
        check(org, "organizations[]")
        check(org.get("rating"), "organizations[].rating")
        for evidence in org.get("evidence", []):
            check(evidence, "organizations[].evidence[]")
    for model in data.get("models", []):
        check(model, "models[]")
    for route in data.get("routes", []):
        check(route, "routes[]")
    return problems


# Each entry of data.json.


def route_label(location: Mapping[str, Any], grids: list[str]) -> str:
    """Where a route runs, in words: its location's label, else a count of its grids, else "Not disclosed"."""
    if location.get("label"):
        return location["label"]
    if not grids:
        return "Not disclosed"
    return "1 grid" if len(grids) == 1 else f"{len(grids)} grids"


def route_entry(name: str, route: Mapping[str, Any]) -> dict:
    """A route as the site shows it: its two ratings and how it is labelled."""
    disclosure, carbon = route["disclosure_rating"], route["carbon_intensity"]
    return {
        "slug": name,
        "org": route["org"],
        "model": route["model"],
        "label": route_label(route["location"], carbon["grids"]),
        "default": bool(route.get("default")),
        "letter": disclosure["letter"],
        "gap": disclosure["gap"],
        "sci": carbon["sci_g"],
        "energy": carbon["energy_wh"],
        "grid_intensity": carbon["grid_intensity_g_per_kwh"],
        "embodied": carbon["embodied_g"],
        "band": carbon["band"],
        "served_as": route.get("served_as"),
    }


def organization_evidence(routes: Mapping[str, Any], served: list[str]) -> list[dict]:
    """The primary sources behind an organization's routes, one entry per page (sorted by URL): the passages quoted
    from it, when it was last read, and the routes it supports."""
    by_url: dict[str, dict] = {}
    for name in served:
        for evidence in routes[name]["location"]["evidence"]:
            if evidence["kind"] != "primary":
                continue
            entry = by_url.setdefault(
                evidence["url"], {"url": evidence["url"], "quotes": [], "accessed": evidence["accessed"], "routes": []}
            )
            entry["quotes"] += [quote for quote in _QUOTED.findall(evidence["shows"]) if quote not in entry["quotes"]]
            entry["accessed"] = max(entry["accessed"], evidence["accessed"])
            if name not in entry["routes"]:
                entry["routes"].append(name)
    return [by_url[url] for url in sorted(by_url)]


def organization_entry(slug: str, org: Mapping[str, Any], routes: Mapping[str, Any]) -> dict:
    """An organization as the site shows it: who it is, its rating, its routes and the sources behind them."""
    served = sorted(name for name, route in routes.items() if route["org"] == slug)
    return {
        "slug": slug,
        "display_name": org["display_name"],
        "type": org["type"],
        "country": org.get("country"),
        "homepage": org["homepage"],
        "description": org.get("description"),
        "rating": org["disclosure_rating"],
        "routes": served,
        "evidence": organization_evidence(routes, served),
    }


def model_entry(slug: str, model: Mapping[str, Any]) -> dict:
    """A model as the site shows it: its name and parameter counts."""
    return {
        "slug": slug,
        "display_name": model.get("display_name", slug),
        "architecture": model["architecture"],
        "active_b": model["active_b"],
        "total_b": model["total_b"],
    }


# data.json.


def build_data(data: Mapping[str, Any], release_date: date) -> dict:
    """data.json's content, from sources/ as the release passes it: every record valid, every field score writes
    present."""
    routes = data["routes"]
    route_entries = [route_entry(name, routes[name]) for name in sorted(routes)]
    org_entries = [
        organization_entry(slug, data["organizations"][slug], routes) for slug in sorted(data["organizations"])
    ]
    routes_per_model = Counter(route["model"] for route in routes.values())
    model_entries = [model_entry(slug, data["models"][slug]) for slug in sorted(routes_per_model)]

    calculated = [
        route["carbon_intensity"] for route in routes.values() if route["carbon_intensity"]["sci_g"] is not None
    ]
    lowest = min((carbon["grid_intensity_g_per_kwh"]["low"] for carbon in calculated), default=None)
    highest = max((carbon["grid_intensity_g_per_kwh"]["high"] for carbon in calculated), default=None)
    return {
        "schema": SCHEMA,
        "meta": {
            "release_date": release_date.isoformat(),
            "methodology_version": METHODOLOGY_VERSION,
            "ecologits_version": version("ecologits"),
            "pue": list(FALLBACK_PUE),
            "band_upper": list(CARBON_BAND_UPPER),
            "draft": DRAFT,
            "grid": {"source": "Ember", "year": GRID_YEAR},
            "counts": {
                "organizations": len(org_entries),
                "routes": len(route_entries),
                "models": len(model_entries),
                "grids": len({grid for route in routes.values() for grid in route["carbon_intensity"]["grids"]}),
            },
            # How many times the highest grid intensity is the lowest, across the routes with a carbon intensity.
            "grid_intensity_spread": round(highest / lowest) if lowest and highest is not None else None,
            # The model most routes serve; on a tie, the first by name.
            "featured_model": min(routes_per_model, key=lambda slug: (-routes_per_model[slug], slug), default=None),
        },
        "organizations": org_entries,
        "models": model_entries,
        "routes": route_entries,
    }
