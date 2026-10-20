"""The fields `python -m build score` writes, at the end of each file: a route's `disclosure_rating:` and
`carbon_score:` (build/schemas/disclosure_rating.py, build/schemas/carbon_score.py), an organization's
`disclosure_rating:`.

Validated with their record, strictly (a whole number is accepted as a float). The CI gates check every stored value
against what `python -m build score` computes. `python -m build release` copies them into web/data/data.json."""

from typing import TypedDict

from build.schemas.carbon_score import CarbonScore
from build.schemas.disclosure_rating import DisclosureRating, Letter


class RouteScore(TypedDict):
    """The two fields score writes in a route's file."""

    disclosure_rating: DisclosureRating
    carbon_score: CarbonScore


class OrgRating(TypedDict):
    """An organization's location disclosure rating: the average of its routes' letters."""

    letter: Letter | None
    mean: float | None
    spread: dict[Letter, int]  # letter -> number of routes
    summary: str
