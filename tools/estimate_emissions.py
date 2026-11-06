"""A model's emissions, from the release in data/data.json."""

import json
import re
from functools import cache
from pathlib import Path

from tools.types import (
    Estimate,
    Range,
    RouteSummary,
    PublishedData,
    PublishedModel,
    PublishedOrganization,
    PublishedRoute,
)

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "data.json"


@cache
def published_data() -> PublishedData:
    """The release in data/data.json, whatever its schema version: read on first use, then kept."""
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _normalized(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _scaled(value: Range, factor: float) -> Range:
    return {"low": round(value["low"] * factor, 6), "high": round(value["high"] * factor, 6)}


def _midpoint(value: Range | None) -> float:
    return 0.0 if value is None else (value["low"] + value["high"]) / 2


def _organization(route: PublishedRoute) -> PublishedOrganization:
    return next(org for org in published_data()["organizations"] if org["slug"] == route["org"])


def _summary(route: PublishedRoute, output_tokens: int) -> RouteSummary:
    # data.json's figures are per its functional unit: so many output tokens, stated in meta.
    factor = output_tokens / published_data()["meta"]["functional_unit"]["output_tokens"]
    return {
        "route": route["slug"],
        "organization": _organization(route)["display_name"],
        "where": route["label"],
        "rating": route["letter"],
        "gap": route["gap"],
        "served_as": route["served_as"],
        "energy_wh": _scaled(route["energy"], factor),
        # Without a grid there is no carbon figure, embodied emissions included: energy only.
        "embodied_g": None if route["sci"] is None else _scaled(route["embodied"], factor),
        "co2e_g": None if route["sci"] is None else _scaled(route["sci"], factor),
    }


def find_model(name: str) -> PublishedModel:
    """The model a name means: its slug, its display name or a name a route serves it as, in any case or punctuation."""
    data = published_data()
    if not data["models"]:
        raise LookupError("There are no models on the map yet.")
    wanted = _normalized(name)
    for model in data["models"]:
        names = [model["slug"], model["display_name"]]
        names += [
            route["served_as"] for route in data["routes"] if route["model"] == model["slug"] and route["served_as"]
        ]
        if wanted in {_normalized(n) for n in names}:
            return model
    models = ", ".join(model["display_name"] for model in data["models"])
    raise LookupError(f"No model on the map matches '{name}'. Models: {models}.")


def estimate(model: str, output_tokens: int) -> Estimate:
    """A response's energy, embodied emissions and carbon on every route of its model, lowest carbon first and routes
    without a grid last."""
    if output_tokens < 1:
        raise ValueError(f"output_tokens must be at least 1, not {output_tokens}.")
    data = published_data()
    found = find_model(model)
    routes = [route for route in data["routes"] if route["model"] == found["slug"]]
    routes.sort(key=lambda route: (route["sci"] is None, _midpoint(route["sci"])))
    meta = data["meta"]
    return {
        "model": found["display_name"],
        "output_tokens": output_tokens,
        "routes": [_summary(route, output_tokens) for route in routes],
        "release": {
            "release_date": meta["release_date"],
            "methodology_version": meta["methodology_version"],
            "ecologits_version": meta["ecologits_version"],
            "draft": meta["draft"],
        },
    }
