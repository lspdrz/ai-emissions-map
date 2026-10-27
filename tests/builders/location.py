from typing import Any

from pydantic import TypeAdapter

from build.schemas.evidence import Evidence
from build.schemas.route import CheckedLocation, Facility, FacilityPue, Location
from tests.builders.evidence import make_evidence

_LOCATION = TypeAdapter(CheckedLocation)
_FACILITY = TypeAdapter(Facility)
_FACILITY_PUE = TypeAdapter(FacilityPue)


def make_facility(name: str = "Acme 1, Geneva", pue: FacilityPue | None = None) -> Facility:
    """A building the evidence names; with pue, its published PUE."""
    return _FACILITY.validate_python({"name": name} | ({} if pue is None else {"pue": pue}))


def make_facility_pue(value: float = 1.2, **overrides: Any) -> FacilityPue:
    """A facility's published annual PUE, on one primary source. By default 1.2 for the year to 2025-12-31."""
    return _FACILITY_PUE.validate_python(
        {
            "value": value,
            "period_end": "2025-12-31",
            "evidence": [make_evidence(shows='Efficiency page: "annual PUE of 1.2"')],
        }
        | overrides
    )


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
