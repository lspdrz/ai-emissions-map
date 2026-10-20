"""A route's location disclosure rating, as `build.disclosure_rating.disclosure_rating` computes it and a route's
`disclosure_rating:` field stores it."""

from typing import Literal, TypedDict

Letter = Literal["A", "B", "C", "D"]


class DisclosureRating(TypedDict):
    """A route's location disclosure letter."""

    letter: Letter
    gap: str | None  # what the disclosure lacks, for the site
