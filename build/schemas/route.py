"""A route: one organization serving one model, by default or in a region the customer chooses, and where its
electricity comes from, as precisely as its evidence establishes."""

from typing import Annotated, NotRequired, TypedDict

from pydantic import AfterValidator, Field, with_config

from build.schemas.carbon_score import CarbonScore
from build.schemas.common import RECORD, NonEmptyStr, Slug
from build.schemas.disclosure_rating import DisclosureRating
from build.schemas.evidence import Evidence, has_primary


Candidate = Annotated[str, Field(pattern=r"^(grid:[a-z0-9]+(-[a-z0-9]+)*|cloud:[a-z0-9-]+:[A-Za-z0-9-]+)$")]


@with_config(RECORD)
class Location(TypedDict):
    label: NotRequired[
        Annotated[
            str,
            Field(
                min_length=1,
                description="Where the route runs, in words for readers (e.g. 'United States (9 regions)'). "
                "Optional; the site falls back to a count of grids.",
            ),
        ]
    ]
    facilities: NotRequired[
        Annotated[
            list[NonEmptyStr],
            Field(
                min_length=1, description="The buildings the evidence names, in words (e.g. 'Infomaniak D4, Geneva')"
            ),
        ]
    ]
    candidates: Annotated[
        list[Candidate],
        Field(
            description="The grids the route may draw from: grid:<slug>, or cloud:<vendor>:<region>. Empty when the "
            "location is not disclosed"
        ),
    ]
    evidence: list[Evidence]


def _established_by_its_evidence(location: Location) -> Location:
    if location.get("facilities") and not location["candidates"]:
        raise ValueError("facilities need the grid they draw from as a candidate")
    if (location["candidates"] or location.get("facilities")) and not has_primary(location["evidence"]):
        raise ValueError("candidates and facilities need at least one primary source")
    return location


# Location with its rules that span fields: a disclosed location rests on primary evidence.
CheckedLocation = Annotated[Location, AfterValidator(_established_by_its_evidence)]


@with_config(RECORD)
class Route(TypedDict):
    name: Annotated[Slug, Field(description="The slug, '<org>-<model>'; must equal the filename stem")]
    org: Annotated[
        Slug, Field(description="The slug of the organization that serves this route; the route's slug starts with it")
    ]
    model: NonEmptyStr
    served_as: NotRequired[str]
    served_model_evidence: NotRequired[list[Evidence]]
    default: NotRequired[
        Annotated[
            bool,
            Field(
                description="Where the service runs unless the customer chooses otherwise. Marks one route per organization "
                "and model when the customer can choose among several locations; a label only, every route "
                "counts in the organization's rating."
            ),
        ]
    ]
    location: CheckedLocation
    comments: NotRequired[str]
    disclosure_rating: NotRequired[
        Annotated[
            DisclosureRating,
            Field(description="Written by `python -m build score` from the location above it; part of curation"),
        ]
    ]
    carbon_score: NotRequired[
        Annotated[
            CarbonScore,
            Field(description="Written by `python -m build score` from the facts above it; part of curation"),
        ]
    ]


def _consistent(route: Route) -> Route:
    served_as = route.get("served_as")
    if served_as and served_as != route["model"] and not route.get("served_model_evidence"):
        raise ValueError(f"served_as {served_as!r} differs from model {route['model']!r}; add served_model_evidence")
    return route


# Route with its rules that span fields: what build checks a route file against.
CheckedRoute = Annotated[Route, AfterValidator(_consistent)]
