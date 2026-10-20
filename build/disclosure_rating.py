"""Location disclosure ratings: a letter per route, and their average per organization."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping

from build.constants.config import DISCLOSURE_POINTS
from build.schemas.disclosure_rating import DisclosureRating, Letter
from build.schemas.evidence import has_primary
from build.schemas.grid import Grid
from build.schemas.route import Location
from build.schemas.score import OrgRating


# What each letter below A lacks, for the site. Proposed wording: the maintainer may rename.
GAPS: dict[Letter, str | None] = {
    "A": None,
    "B": "The grid is disclosed, not the facility.",
    "C": "The grid is not determined: several are possible.",
    "D": "Location not disclosed by the provider.",
}


def _disclosure_letter(location: Location, grids: list[Grid]) -> Letter:
    """How precisely the location's primary evidence determines where its electricity comes from.
    `grids` are the distinct grids its candidates resolve to."""
    if not location["candidates"] or not has_primary(location["evidence"]):
        return "D"  # nothing disclosed
    if location.get("facilities"):
        return "A"  # the facilities are named: their own supply can be checked
    if len(grids) == 1 and not grids[0].get("subdivided"):
        return "B"  # one grid, not subdivided
    return "C"  # several grids, or one subdivided grid


def _summary(letter: Letter, spread: dict[Letter, int]) -> str:
    parts = [f"{n} route{'s' if n != 1 else ''} at {grade}" for grade, n in sorted(spread.items())]
    return f"{letter} ({', '.join(parts)})"


def disclosure_rating(location: Location, grids: Mapping[str, Grid]) -> DisclosureRating:
    """A route's location disclosure letter and what it lacks, from its location and the grid files its candidates
    resolve to."""
    letter = _disclosure_letter(location, list(grids.values()))
    return DisclosureRating(letter=letter, gap=GAPS[letter])


def organization_rating(letters: list[Letter]) -> OrgRating:
    """An organization's location disclosure rating from its routes' letters, as its disclosure_rating: field stores
    it: their average letter (ties rounding down), the mean (rounded to 6 places), how many routes have each letter,
    and a summary in words."""
    if not letters:
        return OrgRating(letter=None, mean=None, spread={}, summary="Not rated (no routes)")
    mean = sum(DISCLOSURE_POINTS[route_letter] for route_letter in letters) / len(letters)
    nearest = math.ceil(mean - 0.5)  # the nearest point, ties rounding down
    letter: Letter = next(candidate for candidate, points in DISCLOSURE_POINTS.items() if points == nearest)
    spread = dict(Counter(letters))
    return OrgRating(
        letter=letter,
        mean=round(mean, 6),
        spread=spread,
        summary=_summary(letter, spread),
    )
