"""The fields `python -m build score` writes, at the end of each file: a grid's `intensity:`
(build/schemas/grid.py), a route's `disclosure_rating:` and `carbon_intensity:` (build/schemas/disclosure_rating.py,
build/schemas/carbon_intensity.py), an organization's `disclosure_rating:`.

Validated with their record, strictly (a whole number is accepted as a float). The CI gates check every stored value
against what `python -m build score` computes. `python -m build release` copies the routes' and organizations' into
web/data/data.json."""

from typing import TypedDict

from build.schemas.carbon_intensity import CarbonIntensity
from build.schemas.disclosure_rating import DisclosureRating, Letter


class RouteScore(TypedDict):
    """The two fields score writes in a route's file."""

    disclosure_rating: DisclosureRating
    carbon_intensity: CarbonIntensity


class OrgRating(TypedDict):
    """An organization's location disclosure rating: the average of its routes' letters."""

    letter: Letter | None
    mean: float | None
    spread: dict[Letter, int]  # letter -> number of routes
    summary: str
