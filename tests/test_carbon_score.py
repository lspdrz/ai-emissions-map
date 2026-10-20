from types import SimpleNamespace

import pytest
from ecologits.utils.range_value import RangeValue

from build.carbon_score import carbon_score, ecologits_estimate, grid_value, value_flags
from build.schemas.carbon_score import GridValue
from build.utils.range import Range
from tests.builders.grid import make_grid, make_intensity
from tests.builders.model import make_model


# A route's carbon score: (E x I) + M per 1,000 output tokens, with its parts.


def test_a_route_on_one_grid_is_scored(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    ch = make_grid(values={"2025": {"consumption": make_intensity(direct=30.0, lifecycle=45.0)}})  # gCO2e/kWh
    r = carbon_score(make_model(), {"ch": ch})
    assert (r["grids"], r["flags"]) == (["ch"], {})
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6}
    assert r["embodied_g"] == {"low": 0.05, "high": 0.06}
    assert r["intensity_g_per_kwh"] == {"low": 30.0, "high": 30.0}
    # score = E x I + M: 0.5..0.6 Wh x 30 g/kWh / 1000 + 0.05..0.06 g
    assert r["score_g"] == {"low": 0.065, "high": 0.078}
    assert r["score_lifecycle_g"] == {"low": 0.0725, "high": 0.087}  # 0.5 x 45 / 1000 + 0.05 .. 0.6 x 45 / 1000 + 0.06
    assert r["band"] == [2, 2]


def test_several_grids_give_a_range(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    de = make_grid(name="de", country="DE", zone="DE", values={"2025": {"consumption": make_intensity(direct=330.0)}})
    fr = make_grid(name="fr", country="FR", zone="FR", values={"2025": {"consumption": make_intensity(direct=40.0)}})
    r = carbon_score(make_model(), {"de": de, "fr": fr})
    assert r["grids"] == ["de", "fr"]
    # 0.5 Wh x 40 g/kWh (FR) / 1000 + 0.05 .. 0.6 Wh x 330 g/kWh (DE) / 1000 + 0.06
    assert r["score_g"] == {"low": 0.07, "high": 0.258}
    assert r["band"] == [2, 3]


def test_no_grids_no_score_but_energy_reported(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    r = carbon_score(make_model(), {})
    assert r["grids"] == []
    assert r["score_g"] is None and r["band"] is None
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6} and r["embodied_g"] == {"low": 0.05, "high": 0.06}


def test_no_life_cycle_score_when_a_grid_has_no_life_cycle_value(monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    ch = make_grid(values={"2025": {"consumption": make_intensity(direct=30.0, lifecycle=45.0)}})
    de = make_grid(
        name="de",
        country="DE",
        zone="DE",
        values={"2025": {"consumption": make_intensity(direct=330.0, lifecycle=None)}},
    )
    r = carbon_score(make_model(), {"ch": ch, "de": de})
    assert r["score_lifecycle_g"] is None


# A grid's value: its consumption-based value with a direct figure, for the newest year up to the scoring year (2025
# in every test below). One scenario per test.


def test_grid_value_uses_the_scoring_years_consumption_based_direct_value():
    grid = make_grid(values={"2025": {"consumption": make_intensity(direct=20.0, lifecycle=29.0)}})
    assert grid_value(grid, scoring_year=2025) == {"year": 2025, "intensity": 20.0, "lifecycle": 29.0, "gas": "co2e"}


def test_grid_value_uses_the_newest_earlier_year_when_the_scoring_year_has_none():
    grid = make_grid(
        values={
            "2023": {"consumption": make_intensity(direct=50.0, lifecycle=None)},
            "2024": {"consumption": make_intensity(direct=40.0, lifecycle=None)},
        }
    )
    assert grid_value(grid, scoring_year=2025) == {"year": 2024, "intensity": 40.0, "lifecycle": None, "gas": "co2e"}


def test_grid_value_uses_a_value_of_any_age_when_it_is_the_newest():
    grid = make_grid(values={"2019": {"consumption": make_intensity(direct=60.0, lifecycle=None)}})
    assert grid_value(grid, scoring_year=2025) == {"year": 2019, "intensity": 60.0, "lifecycle": None, "gas": "co2e"}


def test_grid_value_never_uses_a_later_year():
    grid = make_grid(
        values={
            "2024": {"consumption": make_intensity(direct=40.0, lifecycle=None)},
            "2026": {"consumption": make_intensity(direct=10.0, lifecycle=None)},
        }
    )
    assert grid_value(grid, scoring_year=2025) == {"year": 2024, "intensity": 40.0, "lifecycle": None, "gas": "co2e"}


def test_grid_value_never_uses_a_production_based_value_even_a_newer_one():
    grid = make_grid(
        values={
            "2024": {"consumption": make_intensity(direct=40.0, lifecycle=None)},
            "2025": {"production": make_intensity(direct=30.0, lifecycle=None)},
        }
    )
    assert grid_value(grid, scoring_year=2025) == {"year": 2024, "intensity": 40.0, "lifecycle": None, "gas": "co2e"}


def test_grid_value_never_uses_a_life_cycle_figure_in_place_of_a_direct_one():
    grid = make_grid(
        values={
            "2024": {"consumption": make_intensity(direct=40.0, lifecycle=None)},
            "2025": {"consumption": make_intensity(direct=None, lifecycle=50.0)},
        }
    )
    assert grid_value(grid, scoring_year=2025) == {"year": 2024, "intensity": 40.0, "lifecycle": None, "gas": "co2e"}


def test_grid_value_carries_the_gas_of_the_value():
    grid = make_grid(values={"2025": {"consumption": make_intensity(direct=344.0, lifecycle=None, gas="co2")}})
    assert grid_value(grid, scoring_year=2025) == {"year": 2025, "intensity": 344.0, "lifecycle": None, "gas": "co2"}


def test_grid_value_refuses_a_grid_with_only_production_based_values():
    grid = make_grid(values={"2025": {"production": make_intensity(direct=30.0, lifecycle=None)}})
    with pytest.raises(ValueError) as error:
        grid_value(grid, scoring_year=2025)
    assert str(error.value) == "grids/ch.yaml: no consumption-based direct value for 2025 or earlier"


def test_grid_value_refuses_a_grid_with_only_life_cycle_figures():
    grid = make_grid(values={"2025": {"consumption": make_intensity(direct=None, lifecycle=50.0)}})
    with pytest.raises(ValueError) as error:
        grid_value(grid, scoring_year=2025)
    assert str(error.value) == "grids/ch.yaml: no consumption-based direct value for 2025 or earlier"


def test_grid_value_refuses_a_grid_with_only_later_years():
    grid = make_grid(values={"2026": {"consumption": make_intensity(direct=10.0, lifecycle=None)}})
    with pytest.raises(ValueError) as error:
        grid_value(grid, scoring_year=2025)
    assert str(error.value) == "grids/ch.yaml: no consumption-based direct value for 2025 or earlier"


# What a reader must be told about a grid's value, without it changing which value is used: CO2 only, or a year more
# than the maximum grid age (2 years in every test below) older than the scoring year (2025). One scenario per test.


def test_value_flags_nothing_for_a_co2e_value_of_the_scoring_year():
    value = GridValue(year=2025, intensity=30.0, lifecycle=None, gas="co2e")
    assert value_flags(value, scoring_year=2025, max_age=2) == []


def test_value_flags_a_co2_only_value():
    value = GridValue(year=2025, intensity=30.0, lifecycle=None, gas="co2")
    assert value_flags(value, scoring_year=2025, max_age=2) == ["gas"]


def test_value_flags_nothing_for_a_value_exactly_the_maximum_age_old():
    value = GridValue(year=2023, intensity=30.0, lifecycle=None, gas="co2e")
    assert value_flags(value, scoring_year=2025, max_age=2) == []


def test_value_flags_a_value_older_than_the_maximum_age():
    value = GridValue(year=2022, intensity=30.0, lifecycle=None, gas="co2e")
    assert value_flags(value, scoring_year=2025, max_age=2) == ["year"]


def test_value_flags_both_in_order():
    value = GridValue(year=2020, intensity=30.0, lifecycle=None, gas="co2")
    assert value_flags(value, scoring_year=2025, max_age=2) == ["gas", "year"]


def test_flags_name_each_grid_they_concern_and_no_other(monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    ch = make_grid(values={"2025": {"consumption": make_intensity(direct=30.0, lifecycle=None)}})
    de = make_grid(
        name="de",
        country="DE",
        zone="DE",
        values={"2025": {"consumption": make_intensity(direct=344.0, lifecycle=None, gas="co2")}},
    )
    fi = make_grid(
        name="fi",
        country="FI",
        zone="FI",
        values={"2020": {"consumption": make_intensity(direct=26.0, lifecycle=None, gas="co2")}},
    )
    r = carbon_score(make_model(), {"ch": ch, "de": de, "fi": fi})
    assert r["flags"] == {"gas": ["de", "fi"], "year": ["fi"]}


# Energy (E) and embodied emissions (M): how we read EcoLogits' answer. EcoLogits itself is not run: the test replaces
# compute_llm_impacts with a fake returning energy as a RangeValue in kWh and embodied emissions as a float in kg, as
# EcoLogits does.


def test_ecologits_estimate_converts_kwh_to_wh_and_kg_to_g(monkeypatch):
    def fake_impacts(**arguments):
        return SimpleNamespace(
            energy=SimpleNamespace(value=RangeValue(min=0.0005, max=0.0006)),  # kWh
            embodied=SimpleNamespace(gwp=SimpleNamespace(value=0.00005)),  # kg
        )

    monkeypatch.setattr("build.carbon_score.compute_llm_impacts", fake_impacts)
    energy, embodied = ecologits_estimate(make_model(active_b=70, total_b=70))
    assert (energy.low, energy.high) == (pytest.approx(0.5), pytest.approx(0.6))  # Wh
    assert (embodied.low, embodied.high) == (pytest.approx(0.05), pytest.approx(0.05))  # g
