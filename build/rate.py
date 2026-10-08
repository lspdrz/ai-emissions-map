"""Location disclosure ratings: per route, and averaged per organization (spec §9)."""

from __future__ import annotations

from collections import Counter

from build.config import LOCATION_PRECISION_SCORE
from build.utils import average_level_score, score_to_letter

_GAP_MESSAGES = {
    "region": "Location disclosed to a region, not a specific facility.",
    "country": "Location disclosed only to a country.",
    "country_set": "Location disclosed only as a set of possible countries.",
    "unknown": "Location not disclosed by the provider.",
}
_PRESS_ONLY = "Reported in press, not disclosed by the provider."


def rate_routes(data: dict, results: dict[str, dict]) -> dict[str, dict]:
    """Route slug -> {"level", "score": 0-4, "letter": A-E, "gap": what is missing, or None}."""
    ratings: dict[str, dict] = {}
    for name in sorted(results):
        level = results[name]["level"]
        location = data["routes"][name].get("location")
        gap = _GAP_MESSAGES.get(level)
        if level == "unknown" and location and any(e["kind"] == "corroborating" for e in location["evidence"]):
            gap = _PRESS_ONLY
        score = LOCATION_PRECISION_SCORE[level]
        ratings[name] = {"level": level, "score": score, "letter": score_to_letter(score), "gap": gap}
    return ratings


def _summary(letter: str | None, spread: dict[str, int]) -> str:
    if letter is None:
        return "Not rated (no routes)"
    parts = [f"{n} route{'s' if n != 1 else ''} at {grade}" for grade, n in sorted(spread.items())]
    return f"{letter} ({', '.join(parts)})"


def rate_orgs(data: dict, route_ratings: dict[str, dict]) -> dict[str, dict]:
    """Org slug -> {"letter", "mean", "spread": {letter: count}, "routes", "summary"}, from the org's roster."""
    orgs: dict[str, dict] = {}
    for name in sorted(data["organizations"]):
        routes = sorted(r for r in data["organizations"][name]["routes"] if r in route_ratings)
        scores = [route_ratings[r]["score"] for r in routes]
        rounded = average_level_score(scores)
        letter = score_to_letter(rounded) if rounded is not None else None
        spread = dict(Counter(route_ratings[r]["letter"] for r in routes))
        orgs[name] = {"letter": letter, "mean": sum(scores) / len(scores) if scores else None, "spread": spread,
                      "routes": routes, "summary": _summary(letter, spread)}
    return orgs
