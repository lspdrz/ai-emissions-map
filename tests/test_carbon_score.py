from types import SimpleNamespace

import pytest
from ecologits.utils.range_value import RangeValue

from build.carbon_score import carbon_score, ecologits_estimate, ecologits_grid_intensity, grid_intensity
from build.utils.range import Range
from tests.builders.grid import make_grid
from tests.builders.model import make_model


# A route's carbon score: (E x I) + M per 1,000 output tokens, with its parts. E and M are set by replacing
# ecologits_estimate, and I (EcoLogits' mix per country, in gCO2e/kWh) by replacing ecologits_grid_intensity.


def test_a_route_on_one_grid_is_scored(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    monkeypatch.setattr("build.carbon_score.ecologits_grid_intensity", lambda country: {"CH": 30.0}[country])
    r = carbon_score(make_model(), {"ch": make_grid()})
    assert r["grids"] == ["ch"]
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6}
    assert r["embodied_g"] == {"low": 0.05, "high": 0.06}
    assert r["intensity_g_per_kwh"] == {"low": 30.0, "high": 30.0}
    # score = E x I + M: 0.5..0.6 Wh x 30 g/kWh / 1000 + 0.05..0.06 g
    assert r["score_g"] == {"low": 0.065, "high": 0.078}
    assert r["band"] == [2, 2]


def test_several_grids_give_a_range(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    monkeypatch.setattr(
        "build.carbon_score.ecologits_grid_intensity", lambda country: {"DE": 330.0, "FR": 40.0}[country]
    )
    de = make_grid(name="de", country="DE", zone="DE")
    fr = make_grid(name="fr", country="FR", zone="FR")
    r = carbon_score(make_model(), {"de": de, "fr": fr})
    assert r["grids"] == ["de", "fr"]
    # 0.5 Wh x 40 g/kWh (FR) / 1000 + 0.05 .. 0.6 Wh x 330 g/kWh (DE) / 1000 + 0.06
    assert r["score_g"] == {"low": 0.07, "high": 0.258}
    assert r["band"] == [2, 3]


def test_grids_in_one_country_share_its_intensity(monkeypatch):
    # EcoLogits' mixes are per country: two zones of one country (here two US balancing authorities) get one value.
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(1.0), Range.point(0.0)))
    monkeypatch.setattr("build.carbon_score.ecologits_grid_intensity", lambda country: {"US": 384.0}[country])
    caiso = make_grid(name="us-cal-ciso", country="US", zone="US-CAL-CISO")
    pjm = make_grid(name="us-mida-pjm", country="US", zone="US-MIDA-PJM")
    r = carbon_score(make_model(), {"us-cal-ciso": caiso, "us-mida-pjm": pjm})
    assert r["intensity_g_per_kwh"] == {"low": 384.0, "high": 384.0}


def test_no_grids_no_score_but_energy_reported(monkeypatch):
    energy, embodied = Range(0.5, 0.6), Range(0.05, 0.06)  # E in Wh, M in gCO2e, per 1,000 output tokens
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (energy, embodied))
    r = carbon_score(make_model(), {})
    assert r["grids"] == []
    assert r["score_g"] is None and r["band"] is None and r["intensity_g_per_kwh"] is None
    assert r["energy_wh"] == {"low": 0.5, "high": 0.6} and r["embodied_g"] == {"low": 0.05, "high": 0.06}


# A grid's intensity: EcoLogits' mix for its country. One scenario per test.


def test_grid_intensity_is_the_mix_for_the_grids_country(monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_grid_intensity", lambda country: {"CH": 39.2}[country])
    assert grid_intensity(make_grid()) == 39.2


def test_grid_intensity_refuses_an_onsite_grid(monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_grid_intensity", lambda country: 39.2)
    onsite = make_grid(name="acme-1-onsite", country="CH", zone=None, supply="onsite")
    with pytest.raises(ValueError, match="on-site grid has no EcoLogits country mix"):
        grid_intensity(onsite)


def test_grid_intensity_refuses_a_country_ecologits_lacks(monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_grid_intensity", lambda country: None)
    with pytest.raises(ValueError, match="EcoLogits has no electricity mix for 'CH'"):
        grid_intensity(make_grid())


# How we read EcoLogits' mixes: an alpha-2 country becomes its alpha-3 zone, kgCO2e/kWh becomes gCO2e/kWh. The mixes
# are EcoLogits' data file, not a model run.


def test_ecologits_grid_intensity_converts_the_country_and_the_unit(monkeypatch):
    def fake_find(zone):
        return SimpleNamespace(gwp=0.0392) if zone == "CHE" else None

    monkeypatch.setattr("build.carbon_score.electricity_mixes.find_electricity_mix", fake_find)
    assert ecologits_grid_intensity("CH") == pytest.approx(39.2)


def test_ecologits_grid_intensity_is_none_for_an_unknown_country(monkeypatch):
    monkeypatch.setattr("build.carbon_score.electricity_mixes.find_electricity_mix", lambda zone: None)
    assert ecologits_grid_intensity("CH") is None
    assert ecologits_grid_intensity("ZZ") is None  # not an ISO 3166 country


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
