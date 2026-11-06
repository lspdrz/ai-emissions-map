import pytest
from pydantic import TypeAdapter, ValidationError

from build.schemas.route import CheckedLocation, CheckedRoute, CheckedSpeed
from tests.builders.broken import changed, without
from tests.builders.evidence import make_evidence
from tests.builders.location import make_facility, make_facility_pue, make_location
from tests.builders.route import make_route
from tests.builders.speed import make_speed

_LOCATION = TypeAdapter(CheckedLocation)
_ROUTE = TypeAdapter(CheckedRoute)
_SPEED = TypeAdapter(CheckedSpeed)


# A location: what it discloses rests on primary evidence.


def test_candidates_need_a_primary_source():
    location = make_location(candidates=["grid:ch"], evidence=[make_evidence(kind="primary")])
    press_only = changed(location, "evidence", to=[make_evidence(kind="corroborating")])
    with pytest.raises(ValidationError, match="candidates and facilities need at least one primary source"):
        _LOCATION.validate_python(press_only)


def test_facilities_need_the_grid_they_draw_from_as_a_candidate():
    location = make_location(candidates=["grid:ch"], facilities=[make_facility("Acme 1, Geneva")])
    without_grid = changed(location, "candidates", to=[])
    with pytest.raises(ValidationError, match="facilities need the grid they draw from as a candidate"):
        _LOCATION.validate_python(without_grid)


def test_an_undisclosed_location_needs_no_primary_source():
    location = {"candidates": [], "evidence": [make_evidence(kind="corroborating")]}
    assert _LOCATION.validate_python(location) == location


# A facility's PUE: measured over a year, on a primary source.


def test_a_named_facility_can_have_its_pue():
    location = make_location(candidates=["grid:ch"], facilities=[make_facility("Acme 1, Geneva", make_facility_pue())])
    assert _LOCATION.validate_python(location) == location


def test_a_pue_needs_a_primary_source():
    location = make_location(candidates=["grid:ch"], facilities=[make_facility("Acme 1, Geneva", make_facility_pue())])
    press_only = changed(location, "facilities", 0, "pue", "evidence", to=[make_evidence(kind="corroborating")])
    with pytest.raises(ValidationError, match="'Acme 1, Geneva': its PUE needs at least one primary source"):
        _LOCATION.validate_python(press_only)


def test_a_pue_is_at_least_one():
    location = make_location(candidates=["grid:ch"], facilities=[make_facility("Acme 1, Geneva", make_facility_pue())])
    below_one = changed(location, "facilities", 0, "pue", "value", to=0.9)
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        _LOCATION.validate_python(below_one)


# A route's speed: measured for its service, from the provider's own publications or OpenRouter's providers page.


def test_a_speed_from_openrouter_is_valid():
    speed = make_speed()
    assert _SPEED.validate_python(speed) == speed


def test_a_speed_from_the_provider_is_valid():
    speed = make_speed(evidence=[make_evidence(kind="primary")])
    assert _SPEED.validate_python(speed) == speed


def test_a_third_partys_speed_is_from_openrouter_only():
    speed = make_speed()
    elsewhere = changed(speed, "evidence", 0, "url", to="https://benchmarks.example/acme")
    with pytest.raises(ValidationError, match="a third party's speed must come from openrouter.ai"):
        _SPEED.validate_python(elsewhere)


def test_a_speed_is_above_zero():
    with pytest.raises(ValidationError, match="greater than 0"):
        _SPEED.validate_python(changed(make_speed(), "tokens_per_second", to=0))


def test_a_speed_has_its_time_to_first_token():
    with pytest.raises(ValidationError, match="time_to_first_token_s"):
        _SPEED.validate_python(without(make_speed(), "time_to_first_token_s"))


def test_a_route_can_have_its_speed():
    route = make_route(speed=make_speed())
    assert _ROUTE.validate_python(route) == route


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
