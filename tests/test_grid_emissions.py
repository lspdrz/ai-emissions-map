import pytest

from build.grid_emissions import grid_geography, grid_intensity
from tests.builders.grid import make_grid

# A grid's intensity: Ember's value for its subdivision or country, for the scoring year (2025 in every test below) or
# its latest earlier year. One scenario per test; each passes its own Ember table (geography -> year -> gCO2e/kWh).


def test_a_grid_uses_its_countrys_value():
    assert grid_intensity(make_grid(), {"CH": {2025: 39.3}}, scoring_year=2025) == {
        "g_per_kwh": 39.3,
        "year": 2025,
        "geography": "CH",
        "source": "Ember",
    }


def test_a_us_grid_naming_its_state_uses_the_states_value():
    grid = make_grid(name="us-mida-pjm", country="US", zone="US-MIDA-PJM", subdivision="VA")
    assert grid_geography(grid) == "US-VA"
    resolved = grid_intensity(grid, {"US": {2025: 384.0}, "US-VA": {2025: 357.0}}, scoring_year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (357.0, "US-VA")


def test_a_chinese_grid_naming_its_province_uses_the_provinces_value():
    grid = make_grid(name="cn", country="CN", zone="CN", subdivision="SC")
    assert grid_geography(grid) == "CN-SC"
    resolved = grid_intensity(grid, {"CN": {2025: 560.0}, "CN-SC": {2025: 178.0}}, scoring_year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (178.0, "CN-SC")


def test_a_grid_without_a_subdivision_uses_the_national_value():
    grid = make_grid(name="us", country="US", zone="US")
    resolved = grid_intensity(grid, {"US": {2025: 384.0}, "US-VA": {2025: 357.0}}, scoring_year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (384.0, "US")


def test_a_grid_without_the_scoring_year_uses_its_latest_earlier_year():
    resolved = grid_intensity(make_grid(), {"CH": {2023: 40.0, 2024: 34.6}}, scoring_year=2025)
    assert (resolved["g_per_kwh"], resolved["year"]) == (34.6, 2024)


def test_a_later_year_is_never_used():
    resolved = grid_intensity(make_grid(), {"CH": {2024: 34.6, 2026: 10.0}}, scoring_year=2025)
    assert (resolved["g_per_kwh"], resolved["year"]) == (34.6, 2024)


def test_a_grid_with_only_later_years_is_refused():
    with pytest.raises(ValueError, match="Ember has no intensity for 'CH' in 2025 or earlier"):
        grid_intensity(make_grid(), {"CH": {2026: 10.0}}, scoring_year=2025)


def test_a_geography_missing_from_the_table_is_refused():
    with pytest.raises(ValueError, match="Ember has no intensity for 'CH' in 2025 or earlier"):
        grid_intensity(make_grid(), {}, scoring_year=2025)


def test_an_onsite_grid_is_refused():
    onsite = make_grid(name="acme-1-onsite", country="CH", zone=None, supply="onsite")
    with pytest.raises(ValueError, match="on-site grid has no Ember value"):
        grid_intensity(onsite, {"CH": {2025: 39.3}}, scoring_year=2025)
