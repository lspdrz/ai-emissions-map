import pytest

from build.grid_emissions import (
    GRID_EMISSIONS_COMMENT,
    grid_geography,
    grid_emissions,
    grid_intensity,
)
from tests.builders.files import write_ember_table, write_source
from tests.builders.grid import make_grid

# A grid's intensity: Ember's value for its subdivision or country, for the scoring year (2025 in every test below) or
# its latest earlier year. One scenario per test; each passes its own Ember table (geography -> year -> gCO2e/kWh).


def test_a_grid_uses_its_countrys_value():
    assert grid_intensity(make_grid(), {"CH": {2025: 39.3}}, year=2025) == {
        "g_per_kwh": 39.3,
        "year": 2025,
        "geography": "CH",
        "source": "Ember",
    }


def test_a_us_grid_naming_its_state_uses_the_states_value():
    grid = make_grid(name="us-mida-pjm", country="US", zone="US-MIDA-PJM", subdivision="VA")
    assert grid_geography(grid) == "US-VA"
    resolved = grid_intensity(grid, {"US": {2025: 384.0}, "US-VA": {2025: 357.0}}, year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (357.0, "US-VA")


def test_a_chinese_grid_naming_its_province_uses_the_provinces_value():
    grid = make_grid(name="cn", country="CN", zone="CN", subdivision="SC")
    assert grid_geography(grid) == "CN-SC"
    resolved = grid_intensity(grid, {"CN": {2025: 560.0}, "CN-SC": {2025: 178.0}}, year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (178.0, "CN-SC")


def test_a_grid_without_a_subdivision_uses_the_national_value():
    grid = make_grid(name="us", country="US", zone="US")
    resolved = grid_intensity(grid, {"US": {2025: 384.0}, "US-VA": {2025: 357.0}}, year=2025)
    assert (resolved["g_per_kwh"], resolved["geography"]) == (384.0, "US")


def test_a_grid_without_the_grid_year_uses_its_latest_earlier_year():
    resolved = grid_intensity(make_grid(), {"CH": {2023: 40.0, 2024: 34.6}}, year=2025)
    assert (resolved["g_per_kwh"], resolved["year"]) == (34.6, 2024)


def test_a_later_year_is_never_used():
    resolved = grid_intensity(make_grid(), {"CH": {2024: 34.6, 2026: 10.0}}, year=2025)
    assert (resolved["g_per_kwh"], resolved["year"]) == (34.6, 2024)


def test_a_grid_with_only_later_years_is_refused():
    with pytest.raises(ValueError, match="Ember has no intensity for 'CH' in 2025 or earlier"):
        grid_intensity(make_grid(), {"CH": {2026: 10.0}}, year=2025)


def test_a_geography_missing_from_the_table_is_refused():
    with pytest.raises(ValueError, match="Ember has no intensity for 'CH' in 2025 or earlier"):
        grid_intensity(make_grid(), {}, year=2025)


def test_an_onsite_grid_is_refused():
    onsite = make_grid(name="acme-1-onsite", country="CH", zone=None, supply="onsite")
    with pytest.raises(ValueError, match="on-site grid has no Ember value"):
        grid_intensity(onsite, {"CH": {2025: 39.3}}, year=2025)


# Each test writes its own grid files (curated part only, as a curator leaves them) and Ember table into tmp_path.


def _grid(root, name, country="CH", extra=""):
    write_source(root, f"grids/{name}.yaml", f"name: {name}\ndisplay_name: {name.upper()}\ncountry: {country}\n{extra}")


def _read(root, name):
    return (root / "sources" / "grids" / f"{name}.yaml").read_text()


# python -m build grid-emissions --write: writes each grid's intensity: below its comment.


def test_every_grids_intensity_is_written_below_its_comment(tmp_path):
    _grid(tmp_path, "ch", extra="zone: CH\n")
    write_ember_table(tmp_path, {"CH": {2024: 34.6, 2025: 39.3}})
    run = grid_emissions(tmp_path, write=True)
    assert (run.errors, [p.name for p in run.written]) == ([], ["ch.yaml"])
    assert _read(tmp_path, "ch") == (
        "name: ch\ndisplay_name: CH\ncountry: CH\nzone: CH\n\n"
        + GRID_EMISSIONS_COMMENT
        + "\nintensity:\n  g_per_kwh: 39.3\n  year: 2025\n  geography: CH\n  source: Ember\n"
    )


def test_only_the_named_grids_are_written(tmp_path):
    _grid(tmp_path, "ch")
    _grid(tmp_path, "de", country="DE")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}, "DE": {2025: 334.1}})
    run = grid_emissions(tmp_path, ["de"], write=True)
    assert [p.name for p in run.written] == ["de.yaml"]
    assert GRID_EMISSIONS_COMMENT not in _read(tmp_path, "ch")


def test_a_us_grid_naming_its_subdivision_gets_the_states_value(tmp_path):
    _grid(tmp_path, "us-mida-pjm", country="US", extra="subdivision: VA\n")
    write_ember_table(tmp_path, {"US": {2025: 384.4}, "US-VA": {2025: 356.6}})
    grid_emissions(tmp_path, write=True)
    assert "  g_per_kwh: 356.6\n  year: 2025\n  geography: US-VA\n" in _read(tmp_path, "us-mida-pjm")


def test_a_second_run_writes_nothing(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    grid_emissions(tmp_path, write=True)
    assert grid_emissions(tmp_path, write=True).written == []


def test_a_refreshed_table_rewrites_the_value_and_keeps_the_curated_part(tmp_path):
    _grid(tmp_path, "ch", extra="comments: Example.\n")
    write_ember_table(tmp_path, {"CH": {2024: 34.6}})
    grid_emissions(tmp_path, write=True)
    write_ember_table(tmp_path, {"CH": {2024: 34.6, 2025: 39.3}})
    grid_emissions(tmp_path, write=True)
    text = _read(tmp_path, "ch")
    assert text.startswith("name: ch\ndisplay_name: CH\ncountry: CH\ncomments: Example.\n\n")
    assert text.count(GRID_EMISSIONS_COMMENT) == 1 and "  g_per_kwh: 39.3\n  year: 2025\n" in text


def test_a_grid_without_an_ember_value_is_reported_and_nothing_is_written(tmp_path):
    _grid(tmp_path, "ch")
    _grid(tmp_path, "xk", country="XK")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    run = grid_emissions(tmp_path, write=True)
    assert run == (
        ["grids/xk.yaml: Ember has no intensity for 'XK' in 2025 or earlier; see docs/workflows/add-grid.md"],
        [],
    )
    assert GRID_EMISSIONS_COMMENT not in _read(tmp_path, "ch")


def test_an_unknown_grid_name_is_reported(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    assert grid_emissions(tmp_path, ["fr"], write=True).errors == ["grids/fr.yaml: no such grid file"]


def test_a_missing_table_is_reported(tmp_path):
    _grid(tmp_path, "ch")
    assert grid_emissions(tmp_path, write=True).errors == [
        "sources/snapshots/grid_intensity.csv: missing; run `python -m build import-ember`"
    ]


# python -m build grid-emissions, without --write: the CI gate on stored values.


def test_current_intensities_pass(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    grid_emissions(tmp_path, write=True)
    assert grid_emissions(tmp_path) == ([], [])


def test_a_missing_intensity_is_named(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    assert grid_emissions(tmp_path).errors == [
        "grids/ch.yaml: is missing the intensity field; run `python -m build grid-emissions --write ch`"
    ]


def test_a_value_moved_by_a_refreshed_table_is_named(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2024: 34.6}})
    grid_emissions(tmp_path, write=True)
    write_ember_table(tmp_path, {"CH": {2024: 34.6, 2025: 39.3}})
    assert grid_emissions(tmp_path).errors == [
        "grids/ch.yaml: its intensity is out of date (g_per_kwh, year); run `python -m build grid-emissions --write ch`"
    ]


def test_a_hand_edited_value_is_named(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    grid_emissions(tmp_path, write=True)
    path = tmp_path / "sources" / "grids" / "ch.yaml"
    path.write_text(path.read_text().replace("g_per_kwh: 39.3", "g_per_kwh: 10.0"))
    assert grid_emissions(tmp_path).errors == [
        "grids/ch.yaml: its intensity is out of date (g_per_kwh); run `python -m build grid-emissions --write ch`"
    ]


def test_the_gate_writes_nothing(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    before = _read(tmp_path, "ch")
    grid_emissions(tmp_path)
    assert _read(tmp_path, "ch") == before


def test_without_write_a_grid_missing_its_intensity_is_reported_not_written(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    run = grid_emissions(tmp_path, ["ch"])
    assert run.written == [] and GRID_EMISSIONS_COMMENT not in _read(tmp_path, "ch")


def test_a_hand_edited_block_with_the_right_values_is_reported(tmp_path):
    _grid(tmp_path, "ch")
    write_ember_table(tmp_path, {"CH": {2025: 39.3}})
    grid_emissions(tmp_path, write=True)
    path = tmp_path / "sources" / "grids" / "ch.yaml"
    path.write_text(path.read_text() + "# a note\n")
    assert grid_emissions(tmp_path).errors == [
        "grids/ch.yaml: its intensity: block was edited by hand; run `python -m build grid-emissions --write ch`"
    ]
