from types import SimpleNamespace

import pytest
from ecologits.utils.range_value import RangeValue

from build.carbon_intensity import carbon_intensity, ecologits_estimate
from build.utils.range import Range
from tests.builders.grid import make_grid_intensity
from tests.builders.model import make_model


# A route's carbon intensity: (E x I) + M per 1,000 output tokens, with its parts. E and M are set by replacing
# ecologits_estimate; I is each grid's resolved intensity, as score passes it from the grid files (tests/test_grid_emissions.py).


def test_a_route_on_one_grid_has_a_carbon_intensity(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model: (energy, embodied))
    r = carbon_intensity(make_model(), {"ch": make_grid_intensity(30.0)})
    assert r["grids"] == ["ch"]
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6}
    assert r["embodied_g"] == {"low": 0.05, "high": 0.06}
    assert r["grid_intensity_g_per_kwh"] == {"low": 30.0, "high": 30.0}
    # SCI = E x I + M: 0.5..0.6 Wh x 30 g/kWh / 1000 + 0.05..0.06 g
    assert r["sci_g"] == {"low": 0.065, "high": 0.078}
    assert r["band"] == [2, 2]


def test_several_grids_give_a_range(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model: (energy, embodied))
    de, fr = make_grid_intensity(330.0, geography="DE"), make_grid_intensity(40.0, geography="FR")
    r = carbon_intensity(make_model(), {"de": de, "fr": fr})
    assert r["grids"] == ["de", "fr"]
    # 0.5 Wh x 40 g/kWh (FR) / 1000 + 0.05 .. 0.6 Wh x 330 g/kWh (DE) / 1000 + 0.06
    assert r["sci_g"] == {"low": 0.07, "high": 0.258}
    assert r["band"] == [2, 3]


def test_no_grids_no_carbon_intensity_but_energy_reported(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_intensity.ecologits_estimate", lambda model: (energy, embodied))
    r = carbon_intensity(make_model(), {})
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
    energy, embodied = ecologits_estimate(make_model(active_b=70, total_b=70))
    assert (energy.low, energy.high) == (pytest.approx(0.5), pytest.approx(0.6))  # Wh
    assert (embodied.low, embodied.high) == (pytest.approx(0.05), pytest.approx(0.05))  # g
