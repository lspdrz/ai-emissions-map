"""Constrained types shared by the record schemas."""

from typing import Annotated

from pydantic import ConfigDict, Field

# Every record: no unknown fields, and no type coercion (an unquoted YAML date is a date, not a string).
RECORD = ConfigDict(extra="forbid", strict=True)

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
IsoDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO 8601, quoted in YAML")]
NonEmptyStr = Annotated[str, Field(min_length=1)]
