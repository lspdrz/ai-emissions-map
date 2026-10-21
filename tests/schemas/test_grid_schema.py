import pytest
from pydantic import TypeAdapter, ValidationError

from build.schemas.grid import CheckedGrid
from tests.builders.broken import changed
from tests.builders.grid import make_grid

_GRID = TypeAdapter(CheckedGrid)


# A grid's rules beyond the shape of its fields: its location and its supply. It holds no values.


def test_a_public_grid_is_its_zone_and_country():
    grid = make_grid(name="ch", country="CH", zone="CH")
    assert _GRID.validate_python(grid) == {"name": "ch", "display_name": "CH", "country": "CH", "zone": "CH"}


def test_an_onsite_grid_with_a_zone_is_refused():
    grid = make_grid(name="acme-1", country="CH", zone="CH")
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(grid, "supply", to="onsite"))
    assert [problem["msg"] for problem in error.value.errors()] == ["Value error, an onsite grid has no zone"]


def test_an_onsite_grid_without_a_zone_is_valid():
    grid = make_grid(name="acme-1", country="CH", zone=None, supply="onsite")
    assert _GRID.validate_python(grid) == grid


def test_a_country_is_two_capital_letters():
    with pytest.raises(ValidationError):
        _GRID.validate_python(changed(make_grid(), "country", to="CHE"))


def test_values_are_no_longer_part_of_a_grid():
    # Intensities come from EcoLogits; a grid file that still carries values is refused, not silently ignored.
    with pytest.raises(ValidationError) as error:
        _GRID.validate_python(changed(make_grid(), "values", to={"2025": {}}))
    assert [problem["msg"] for problem in error.value.errors()] == ["Extra inputs are not permitted"]


def test_a_grid_may_name_its_subdivision():
    us = make_grid(name="us-mida-pjm", country="US", zone="US-MIDA-PJM", subdivision="VA")
    cn = make_grid(name="cn", country="CN", zone="CN", subdivision="GD")
    assert (_GRID.validate_python(us)["subdivision"], _GRID.validate_python(cn)["subdivision"]) == ("VA", "GD")


def test_a_subdivision_is_its_iso_3166_2_code_without_the_country():
    with pytest.raises(ValidationError):
        _GRID.validate_python(changed(make_grid(), "subdivision", to="US-VA"))


def test_a_grid_may_carry_the_intensity_score_wrote():
    grid = make_grid(intensity={"g_per_kwh": 39.3, "year": 2025, "geography": "CH", "source": "Ember"})
    assert _GRID.validate_python(grid)["intensity"]["g_per_kwh"] == 39.3


def test_a_stored_intensity_must_come_from_ember():
    with pytest.raises(ValidationError):
        make_grid(intensity={"g_per_kwh": 39.3, "year": 2025, "geography": "CH", "source": "VSE"})
