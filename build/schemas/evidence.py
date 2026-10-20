"""A source a claim rests on: where it is, what it says, when it was read."""

from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import Field, with_config

from build.schemas.common import RECORD, IsoDate, NonEmptyStr


@with_config(RECORD)
class Evidence(TypedDict):
    url: NonEmptyStr
    shows: Annotated[str, Field(min_length=1, description="What the source says, quoted from the page that was read")]
    accessed: Annotated[IsoDate, Field(description="When the page was read")]
    kind: Literal["primary", "corroborating"]
    anomaly: NotRequired[
        Annotated[str, Field(description="Where the source contradicts itself or another primary source")]
    ]


def has_primary(evidence: list[Evidence] | None) -> bool:
    """At least one evidence entry is a primary source."""
    return any(e["kind"] == "primary" for e in evidence or [])
