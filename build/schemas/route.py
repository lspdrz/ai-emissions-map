"""A route: one organization serving one model, by default or in a region the customer chooses, and where its
electricity comes from, as precisely as its evidence establishes."""

from typing import Annotated, NotRequired, TypedDict
from urllib.parse import urlparse

from pydantic import AfterValidator, Field, with_config

from build.schemas.carbon_intensity import CarbonIntensity
from build.schemas.common import RECORD, IsoDate, NonEmptyStr, Slug
from build.schemas.disclosure_rating import DisclosureRating
from build.schemas.evidence import Evidence, has_primary


Candidate = Annotated[str, Field(pattern=r"^(grid:[a-z0-9]+(-[a-z0-9]+)*|cloud:[a-z0-9-]+:[A-Za-z0-9-]+)$")]


@with_config(RECORD)
class FacilityPue(TypedDict):
    """A facility's Power Usage Effectiveness, as its operator or the provider publishes it: measured over a year,
    never a design figure, a best month or an average across facilities."""

    value: Annotated[float, Field(ge=1, description="Total facility energy over IT energy, over twelve months")]
    period_end: Annotated[IsoDate, Field(description="The last day of the twelve months the value covers")]
    evidence: Annotated[list[Evidence], Field(min_length=1)]


@with_config(RECORD)
class Facility(TypedDict):
    """A building the evidence names, and its published PUE when there is one."""

    name: Annotated[str, Field(min_length=1, description="The building, in words (e.g. 'Example Geneva 1, Geneva')")]
    pue: NotRequired[
        Annotated[
            FacilityPue,
            Field(description="Its published PUE; the route uses it only when every candidate has one"),
        ]
    ]


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
            list[Facility],
            Field(min_length=1, description="The buildings the evidence names"),
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
    for facility in location.get("facilities", []):
        if "pue" in facility and not has_primary(facility["pue"]["evidence"]):
            raise ValueError(f"{facility['name']!r}: its PUE needs at least one primary source")
    return location


# Location with its rules that span fields: a disclosed location, and a facility's PUE, rest on primary evidence.
CheckedLocation = Annotated[Location, AfterValidator(_established_by_its_evidence)]


@with_config(RECORD)
class Speed(TypedDict):
    """How fast the route's service generates, as measured: from the provider's own publications, or OpenRouter's
    providers page (the one third party that may set it, from its own traffic)."""

    tokens_per_second: Annotated[float, Field(gt=0, description="Output tokens per second, while generating")]
    time_to_first_token_s: Annotated[
        float, Field(ge=0, description="Seconds from the request to the first output token")
    ]
    evidence: Annotated[list[Evidence], Field(min_length=1)]


def _from_the_provider_or_openrouter(speed: Speed) -> Speed:
    for evidence in speed["evidence"]:
        if evidence["kind"] == "corroborating" and urlparse(evidence["url"]).hostname != "openrouter.ai":
            raise ValueError("a third party's speed must come from openrouter.ai")
    return speed


# Speed with its rule on its sources: the provider's own, or OpenRouter's.
CheckedSpeed = Annotated[Speed, AfterValidator(_from_the_provider_or_openrouter)]


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
    speed: NotRequired[
        Annotated[
            CheckedSpeed,
            Field(description="Its service's measured generation speed; without it, EcoLogits estimates one"),
        ]
    ]
    comments: NotRequired[str]
    disclosure_rating: NotRequired[
        Annotated[
            DisclosureRating,
            Field(description="Written by `python -m build score` from the location above it; part of curation"),
        ]
    ]
    carbon_intensity: NotRequired[
        Annotated[
            CarbonIntensity,
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
