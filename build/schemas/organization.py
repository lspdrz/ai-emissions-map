"""An organization that serves AI models."""

from typing import Annotated, Any, Literal, NotRequired, TypedDict

from pydantic import Field, with_config

from build.schemas.common import RECORD, NonEmptyStr, Slug
from build.schemas.score import OrgRating


@with_config(RECORD)
class Ids(TypedDict, total=False):
    ossd: str | None
    hf_provider: str | None
    openrouter: str | None


@with_config(RECORD)
class Contact(TypedDict, total=False):
    url: str


@with_config(RECORD)
class Organization(TypedDict):
    name: Annotated[Slug, Field(description="The slug; must equal the filename stem")]
    display_name: NonEmptyStr
    description: NotRequired[
        Annotated[
            str,
            Field(
                min_length=1,
                description="One or two plain sentences for the site: what the organization discloses about "
                "where it serves models.",
            ),
        ]
    ]
    type: Literal["model_lab", "inference_host", "cloud", "public_compute"]
    homepage: NonEmptyStr
    disclosure_url: NotRequired[
        Annotated[
            str,
            Field(pattern=r"^https://", description="The organization's serving-locations file, if it publishes one"),
        ]
    ]
    country: NotRequired[Annotated[str, Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")]]
    ids: Ids
    contact: NotRequired[Contact]
    responses: NotRequired[list[Any]]
    comments: NotRequired[str]
    disclosure_rating: NotRequired[
        Annotated[
            OrgRating,
            Field(description="Written by `python -m build score` from the organization's routes; part of curation"),
        ]
    ]
