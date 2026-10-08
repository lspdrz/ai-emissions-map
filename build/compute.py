"""Route carbon scores: full SCI, (E x I) + M per 1k output tokens, with its parts kept separately (spec §8).

A result is a dict per route. Ranges stay `Range` objects here; build.serialize writes them as {low, high}.
"""

from __future__ import annotations

from datetime import date

from build.config import LOCATION_PRECISION_SCORE, VERIFICATION_WINDOW
from build.energy import EnergyModel
from build.evidence import location_established
from build.grid import intensity_range, resolve_zones
from build.ranges import Range
from build.utils import band_span
from build.validate import route_owners


class ComputeError(Exception):
    pass


# Why a route is not scored. build.rate turns each into the gap it publishes.
UNDISCLOSED = "location undisclosed"
NOT_VERIFIED = f"location evidence not verified within {VERIFICATION_WINDOW} days"
UPSTREAM_UNSCORED = "an upstream route's location is undisclosed or unverified"


def _result(name: str, org: str, r: dict, energy: Range, embodied: Range, **fields) -> dict:
    """A route result. Unscored unless the caller passes the scored fields."""
    result = {
        "name": name, "org": org, "model": r["model"], "served_as": r.get("served_as"),
        "level": "unknown",  # effective location confidence after the verification window
        "scored": False, "reason": None,  # why not scored
        "zones": [],
        "energy_wh": energy,  # E, Wh per 1k output tokens (model property)
        "embodied_g": embodied,  # M, gCO2e per 1k output tokens (model property), part of the score
        "intensity_direct": None, "intensity_lifecycle": None,
        "operational_direct": None,  # E x I, gCO2e per 1k output tokens (kept for the v2 operational-only toggle)
        "operational_lifecycle": None,
        "score_direct": None,  # the carbon score: operational_direct + M
        "score_lifecycle": None,  # operational_lifecycle + M, shown alongside
        "band": None,  # (lowest band, highest band) of score_direct
        "fallback_zones": [],
        "label_mismatch": bool(r.get("served_as") and r["served_as"] != r["model"]),
        "upstream_weights": [{"route": u["route"], "weight": float(u["weight"])} for u in r.get("upstreams") or []],
    }
    result.update(fields)
    return result


def compute_routes(data: dict, models: dict, grid: dict, cloud_regions: dict[tuple[str, str], str],
                   energy_model: EnergyModel, release: date) -> dict[str, dict]:
    """Route slug -> result, for every route in data (as load_sources returns it, after validate_sources)."""
    routes, owners = data["routes"], route_owners(data["organizations"])
    results: dict[str, dict] = {}

    def get(name: str, stack: tuple[str, ...]) -> dict:
        if name in stack:
            raise ComputeError("upstream cycle: " + " -> ".join(stack + (name,)))
        if name in results:
            return results[name]
        r = routes[name]
        if r.get("upstreams"):
            ups = [get(u["route"], stack + (name,)) for u in r["upstreams"]]
            energy = Range.union(u["energy_wh"] for u in ups)
            embodied = Range.union(u["embodied_g"] for u in ups)
            if not all(u["scored"] for u in ups):
                res = _result(name, owners[name], r, energy, embodied, reason=UPSTREAM_UNSCORED,
                              label_mismatch=bool(r.get("served_as") and r["served_as"] != r["model"])
                              or any(u["label_mismatch"] for u in ups))
            else:
                score = Range.union(u["score_direct"] for u in ups)
                res = _result(
                    name, owners[name], r, energy, embodied, scored=True,
                    level=min((u["level"] for u in ups), key=LOCATION_PRECISION_SCORE.get),
                    zones=sorted({z for u in ups for z in u["zones"]}),
                    intensity_direct=Range.union(u["intensity_direct"] for u in ups),
                    intensity_lifecycle=Range.union(u["intensity_lifecycle"] for u in ups),
                    operational_direct=Range.union(u["operational_direct"] for u in ups),
                    operational_lifecycle=Range.union(u["operational_lifecycle"] for u in ups),
                    score_direct=score, score_lifecycle=Range.union(u["score_lifecycle"] for u in ups),
                    band=band_span(score), fallback_zones=sorted({z for u in ups for z in u["fallback_zones"]}),
                    label_mismatch=bool(r.get("served_as") and r["served_as"] != r["model"])
                    or any(u["label_mismatch"] for u in ups),
                )
        else:
            energy, embodied = energy_model.estimate(r["model"], models[r["model"]])
            loc = r["location"]
            if loc["confidence"] == "unknown":
                res = _result(name, owners[name], r, energy, embodied, reason=UNDISCLOSED)
            elif not location_established(loc, release):
                res = _result(name, owners[name], r, energy, embodied, reason=NOT_VERIFIED)
            else:
                zones = resolve_zones(loc, data["facilities"], cloud_regions)
                direct = intensity_range(zones, grid, "direct")
                lifecycle = intensity_range(zones, grid, "lifecycle")
                op_direct = energy.times(direct).scale(1 / 1000)  # Wh x g/kWh / 1000 = g
                op_lifecycle = energy.times(lifecycle).scale(1 / 1000)
                score = op_direct.plus(embodied)
                res = _result(
                    name, owners[name], r, energy, embodied, scored=True, level=loc["confidence"], zones=zones,
                    intensity_direct=direct, intensity_lifecycle=lifecycle,
                    operational_direct=op_direct, operational_lifecycle=op_lifecycle,
                    score_direct=score, score_lifecycle=op_lifecycle.plus(embodied), band=band_span(score),
                    fallback_zones=[z for z in zones if grid[z]["fallback"]],
                )
        results[name] = res
        return res

    for name in sorted(routes):
        get(name, ())
    return results
