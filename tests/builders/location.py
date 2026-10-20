from typing import Any

from pydantic import TypeAdapter

from build.schemas.evidence import Evidence
from build.schemas.route import CheckedLocation, Location
from tests.builders.evidence import make_evidence

_LOCATION = TypeAdapter(CheckedLocation)


def make_location(
    candidates: list[str] | None = None, evidence: list[Evidence] | None = None, **overrides: Any
) -> Location:
    """A route's location. By default: the CH grid, on one primary source."""
    return _LOCATION.validate_python(
        {
            "candidates": ["grid:ch"] if candidates is None else candidates,
            "evidence": [make_evidence()] if evidence is None else evidence,
        }
        | overrides
    )
