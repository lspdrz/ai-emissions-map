"""Location disclosure ratings: per route, and averaged per organization (spec §9)."""

from __future__ import annotations

from collections import Counter

from build.compute import NOT_VERIFIED, UPSTREAM_UNSCORED
from build.config import LOCATION_PRECISION_SCORE, VERIFICATION_WINDOW
from build.utils import average_level_score, score_to_letter

_GAP_MESSAGES = {
    "region": "Location disclosed to a region, not a specific facility.",
    "country": "Location disclosed only to a country.",
    "country_set": "Location disclosed only as a set of possible countries.",
    "unknown": "Location not disclosed by the provider.",
}
_PRESS_ONLY = "Reported in press, not disclosed by the provider."
# A route that is unscored for a reason other than non-disclosure must not be published as undisclosed.
_GAP_FOR_REASON = {
    NOT_VERIFIED: f"Location evidence not re-verified within {VERIFICATION_WINDOW} days of the release.",
    UPSTREAM_UNSCORED: "An upstream route's location is undisclosed or unverified.",
}


def rate_routes(data: dict, results: dict[str, dict]) -> dict[str, dict]:
    """Route slug -> {"level", "score": 0-4, "letter": A-E, "gap": what is missing, or None}."""
    ratings: dict[str, dict] = {}
    for name in sorted(results):
        level, reason = results[name]["level"], results[name]["reason"]
        location = data["routes"][name].get("location")
        gap = _GAP_FOR_REASON.get(reason) or _GAP_MESSAGES.get(level)
        if (location and location["confidence"] == "unknown"
                and any(e["kind"] == "corroborating" for e in location["evidence"])):
            gap = _PRESS_ONLY
        score = LOCATION_PRECISION_SCORE[level]
        ratings[name] = {"level": level, "score": score, "letter": score_to_letter(score), "gap": gap}
    return ratings


def _summary(letter: str | None, spread: dict[str, int], pinned: int) -> str:
    if letter is None:
        return "Not rated (no default routes)" if pinned else "Not rated (no routes)"
    parts = [f"{n} route{'s' if n != 1 else ''} at {grade}" for grade, n in sorted(spread.items())]
    if pinned:
        parts = [", ".join(parts) + f"; {pinned} pinned route{'s' if pinned != 1 else ''} not counted"]
    return f"{letter} ({', '.join(parts)})"


def rate_orgs(data: dict, route_ratings: dict[str, dict]) -> dict[str, dict]:
    """Org slug -> {"letter", "mean", "spread": {letter: count}, "routes", "pinned_routes", "summary"}.

    The rating averages the routes the organization serves by default. Pinned routes (locations a customer must
    choose) are rated individually and listed, but not averaged, so many pinnable regions cannot outweigh the default.
    """
    orgs: dict[str, dict] = {}
    for name in sorted(data["organizations"]):
        roster = sorted(r for r in data["organizations"][name]["routes"] if r in route_ratings)
        pinned = [r for r in roster if data["routes"][r].get("pinned")]
        routes = [r for r in roster if r not in pinned]
        scores = [route_ratings[r]["score"] for r in routes]
        rounded = average_level_score(scores)
        letter = score_to_letter(rounded) if rounded is not None else None
        spread = dict(Counter(route_ratings[r]["letter"] for r in routes))
        orgs[name] = {"letter": letter, "mean": sum(scores) / len(scores) if scores else None, "spread": spread,
                      "routes": routes, "pinned_routes": pinned, "summary": _summary(letter, spread, len(pinned))}
    return orgs
