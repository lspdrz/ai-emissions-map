from types import SimpleNamespace

import pytest
from ecologits.utils.range_value import RangeValue

from build.carbon_intensity import carbon_intensity, ecologits_estimate
from build.utils.range import Range
from tests.builders.grid import make_grid_intensity
from tests.builders.model import make_model
from tests.builders.speed import make_speed


# A route's carbon intensity: (E x I) + M per 1,000 output tokens, with its parts. E and M are set by replacing
# ecologits_estimate; I is each grid's resolved intensity, as score passes it from the grid files (tests/test_grid_emissions.py).


def test_a_route_on_one_grid_has_a_carbon_intensity(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model, pue, speed: (energy, embodied))
    r = carbon_intensity(make_model(), {"ch": make_grid_intensity(30.0)}, Range(1.1, 1.6), "fallback", None, "fallback")
    assert r["grids"] == ["ch"]
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6}
    assert r["embodied_g"] == {"low": 0.05, "high": 0.06}
    assert r["grid_intensity_g_per_kwh"] == {"low": 30.0, "high": 30.0}
    # SCI = E x I + M: 0.5..0.6 Wh x 30 g/kWh / 1000 + 0.05..0.06 g
    assert r["sci_g"] == {"low": 0.065, "high": 0.078}
    assert r["band"] == [2, 2]


def test_several_grids_give_a_range(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model, pue, speed: (energy, embodied))
    de, fr = make_grid_intensity(330.0, geography="DE"), make_grid_intensity(40.0, geography="FR")
    r = carbon_intensity(make_model(), {"de": de, "fr": fr}, Range(1.1, 1.6), "fallback", None, "fallback")
    assert r["grids"] == ["de", "fr"]
    # 0.5 Wh x 40 g/kWh (FR) / 1000 + 0.05 .. 0.6 Wh x 330 g/kWh (DE) / 1000 + 0.06
    assert r["sci_g"] == {"low": 0.07, "high": 0.258}
    assert r["band"] == [2, 3]


def test_the_routes_pue_is_used_and_stored_with_its_source(monkeypatch):
    used = []

    def estimate(model, pue, speed):
        used.append(pue)
        return Range(0.5, 0.6), Range(0.05, 0.06)

    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", estimate)
    r = carbon_intensity(
        make_model(),
        {"fr": make_grid_intensity(40.0, geography="FR")},
        Range.point(1.18),
        "published",
        None,
        "fallback",
    )
    assert used == [Range.point(1.18)]
    assert (r["pue"], r["pue_source"]) == ({"low": 1.18, "high": 1.18}, "published")


def test_the_routes_speed_is_used_and_stored_with_its_source(monkeypatch):
    used = []

    def estimate(model, pue, speed):
        used.append(speed)
        return Range(0.5, 0.6), Range(0.05, 0.06)

    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", estimate)
    speed = make_speed(tokens_per_second=70.0, time_to_first_token_s=3.8)
    r = carbon_intensity(
        make_model(), {"ch": make_grid_intensity(30.0)}, Range(1.1, 1.6), "fallback", speed, "openrouter"
    )
    assert used == [speed]
    assert (r["speed"], r["speed_source"]) == ({"tokens_per_second": 70.0, "time_to_first_token_s": 3.8}, "openrouter")


def test_no_grids_no_carbon_intensity_but_energy_reported(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model, pue, speed: (energy, embodied))
    r = carbon_intensity(make_model(), {}, Range(1.1, 1.6), "fallback", None, "fallback")
    assert r["grids"] == []
    assert r["sci_g"] is None and r["band"] is None and r["grid_intensity_g_per_kwh"] is None
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6} and r["embodied_g"] == {"low": 0.05, "high": 0.06}


# Energy (E) and embodied emissions (M): how we read EcoLogits' answer. EcoLogits itself is not run: the test replaces
# compute_llm_impacts with a fake returning energy as a RangeValue in kWh and embodied emissions as a float in kg, as
# EcoLogits does.


def test_ecologits_estimate_converts_kwh_to_wh_and_kg_to_g(monkeypatch):
    def fake_impacts(**arguments):
        return SimpleNamespace(
            energy=SimpleNamespace(value=RangeValue(min=0.0005, max=0.0006)),  # kWh
            embodied=SimpleNamespace(gwp=SimpleNamespace(value=0.00005)),  # kg
        )

    monkeypatch.setattr("build.carbon_intensity.compute_llm_impacts", fake_impacts)
    energy, embodied = ecologits_estimate(make_model(active_b=70, total_b=70), Range(1.1, 1.6), None)
    assert (energy.low, energy.high) == (pytest.approx(0.5), pytest.approx(0.6))  # Wh
    assert (embodied.low, embodied.high) == (pytest.approx(0.05), pytest.approx(0.05))  # g


def test_ecologits_estimate_passes_the_pue_to_ecologits(monkeypatch):
    passed = []

    def fake_impacts(**arguments):
        passed.append(arguments["datacenter_pue"])
        return SimpleNamespace(
            energy=SimpleNamespace(value=0.0005), embodied=SimpleNamespace(gwp=SimpleNamespace(value=0.00005))
        )

    monkeypatch.setattr("build.carbon_intensity.compute_llm_impacts", fake_impacts)
    ecologits_estimate(make_model(active_b=70, total_b=70), Range(1.18, 1.3), None)
    assert [(p.min, p.max) for p in passed] == [(1.18, 1.3), (1.18, 1.3)]  # once per end of the parameter range


def test_ecologits_estimate_passes_a_measured_speed_to_ecologits(monkeypatch):
    passed = []

    def fake_impacts(**arguments):
        passed.append((arguments["tps"], arguments["ttft"]))
        return SimpleNamespace(
            energy=SimpleNamespace(value=0.0005), embodied=SimpleNamespace(gwp=SimpleNamespace(value=0.00005))
        )

    monkeypatch.setattr("build.carbon_intensity.compute_llm_impacts", fake_impacts)
    ecologits_estimate(make_model(active_b=70, total_b=70), Range(1.1, 1.6), make_speed(70.0, 3.8))
    assert passed == [(70.0, 3.8), (70.0, 3.8)]


def test_without_a_speed_ecologits_estimates_it(monkeypatch):
    passed = []

    def fake_impacts(**arguments):
        passed.append((arguments["tps"], arguments["ttft"]))
        return SimpleNamespace(
            energy=SimpleNamespace(value=0.0005), embodied=SimpleNamespace(gwp=SimpleNamespace(value=0.00005))
        )

    monkeypatch.setattr("build.carbon_intensity.compute_llm_impacts", fake_impacts)
    ecologits_estimate(make_model(active_b=70, total_b=70), Range(1.1, 1.6), None)
    assert passed == [(None, None), (None, None)]
