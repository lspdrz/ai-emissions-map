import pytest
from pydantic import TypeAdapter, ValidationError

from build.schemas.grid import CheckedGrid
from tests.builders.broken import changed, without
from tests.builders.evidence import make_evidence
from tests.builders.grid import make_grid, make_intensity

_GRID = TypeAdapter(CheckedGrid)


# A grid's rules beyond the shape of its fields: its supply, its years and the values in them.


def test_an_onsite_grid_with_a_zone_is_refused():
    grid = make_grid(name="acme-1", country="CH", zone="CH")
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(grid, "supply", to="onsite"))
    assert [problem["msg"] for problem in error.value.errors()] == ["Value error, an onsite grid has no zone"]


def test_an_onsite_grid_without_a_zone_is_valid():
    grid = make_grid(name="acme-1", country="CH", zone=None, supply="onsite")
    assert _GRID.validate_python(grid) == grid


def test_an_unquoted_year_is_refused():
    # A year unquoted in YAML reads as a number, which the schema refuses: years are quoted strings.
    grid = make_grid(name="ch", country="CH", zone="CH")
    unquoted = changed(grid, "values", to={2025: {"consumption": make_intensity(direct=30.0, lifecycle=None)}})
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(unquoted)
    assert [problem["msg"] for problem in error.value.errors()] == ["Input should be a valid string"]


def test_a_year_needs_a_basis():
    grid = make_grid(name="ch", country="CH", zone="CH")
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(grid, "values", to={"2025": {}}))
    assert [problem["msg"] for problem in error.value.errors()] == ["Value error, needs consumption or production"]


def test_a_value_needs_a_direct_or_a_life_cycle_figure():
    grid = make_grid(name="ch", country="CH", zone="CH")
    neither = without(make_intensity(direct=30.0, lifecycle=None), "direct")
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(grid, "values", to={"2025": {"consumption": neither}}))
    assert [problem["msg"] for problem in error.value.errors()] == ["Value error, needs direct or lifecycle"]


def test_a_value_with_only_a_life_cycle_figure_is_valid():
    grid = make_grid(
        name="ch",
        country="CH",
        zone="CH",
        values={"2025": {"consumption": make_intensity(direct=None, lifecycle=45.0)}},
    )
    assert _GRID.validate_python(grid) == grid


def test_a_value_needs_a_primary_source():
    grid = make_grid(name="ch", country="CH", zone="CH")
    press_only = make_intensity(direct=30.0, lifecycle=None, evidence=[make_evidence(kind="corroborating")])
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(grid, "values", to={"2025": {"consumption": press_only}}))
    assert [problem["msg"] for problem in error.value.errors()] == ["Value error, needs at least one primary source"]
