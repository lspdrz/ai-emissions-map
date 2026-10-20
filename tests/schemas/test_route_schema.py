import pytest
from pydantic import TypeAdapter, ValidationError

from build.schemas.route import CheckedLocation, CheckedRoute
from tests.builders.broken import changed
from tests.builders.evidence import make_evidence
from tests.builders.location import make_location
from tests.builders.route import make_route

_LOCATION = TypeAdapter(CheckedLocation)
_ROUTE = TypeAdapter(CheckedRoute)


# A location: what it discloses rests on primary evidence.


def test_candidates_need_a_primary_source():
    location = make_location(candidates=["grid:ch"], evidence=[make_evidence(kind="primary")])
    press_only = changed(location, "evidence", to=[make_evidence(kind="corroborating")])
    with pytest.raises(ValidationError, match="candidates and facilities need at least one primary source"):
        _LOCATION.validate_python(press_only)


def test_facilities_need_the_grid_they_draw_from_as_a_candidate():
    location = make_location(candidates=["grid:ch"], facilities=["Acme 1, Geneva"])
    without_grid = changed(location, "candidates", to=[])
    with pytest.raises(ValidationError, match="facilities need the grid they draw from as a candidate"):
        _LOCATION.validate_python(without_grid)


def test_an_undisclosed_location_needs_no_primary_source():
    location = {"candidates": [], "evidence": [make_evidence(kind="corroborating")]}
    assert _LOCATION.validate_python(location) == location


# A route: the model it serves.


def test_a_served_name_that_differs_from_the_model_needs_evidence():
    route = changed(make_route(name="acme-m-70b", model="m-70b"), "served_as", to="m-70b-v1.5")
    with pytest.raises(
        ValidationError, match="served_as 'm-70b-v1.5' differs from model 'm-70b'; add served_model_evidence"
    ):
        _ROUTE.validate_python(route)


def test_a_served_name_that_differs_from_the_model_with_evidence_is_valid():
    route = make_route(
        name="acme-m-70b", model="m-70b", served_as="m-70b-v1.5", served_model_evidence=[make_evidence(kind="primary")]
    )
    assert _ROUTE.validate_python(route) == route
