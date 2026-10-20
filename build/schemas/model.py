"""A model's parameter counts, with the evidence for them."""

from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import Discriminator, Field, Tag, with_config

from build.schemas.common import RECORD, NonEmptyStr, Slug
from build.schemas.evidence import Evidence

Billions = Annotated[float, Field(gt=0)]


@with_config(RECORD)
class ParamRange(TypedDict):
    min: Billions
    max: Billions


def _params_form(value: object) -> str:
    return "Range" if isinstance(value, dict) else "Number"


# The form is read from the value, so an error describes the form written, not both.
Params = Annotated[
    Annotated[Billions, Tag("Number")] | Annotated[ParamRange, Tag("Range")],
    Discriminator(_params_form),
    Field(description="Billions of parameters: a number, or {min, max} when only a range is published"),
]


@with_config(RECORD)
class Model(TypedDict):
    """A model's parameter counts and the evidence they rest on: the developer's own publications, or, where the
    developer has not released the architecture, EcoLogits' estimate in its catalogue."""

    name: Annotated[Slug, Field(description="The model id routes use in `model:`; must equal the filename stem.")]
    display_name: NotRequired[NonEmptyStr]
    architecture: Literal["dense", "moe"]
    active_b: Params
    total_b: Params
    evidence: Annotated[list[Evidence], Field(min_length=1)]
    comments: NotRequired[str]
