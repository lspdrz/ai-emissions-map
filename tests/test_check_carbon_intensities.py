from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

from build.check_carbon_intensities import check_carbon_intensities
from build.types import ScoreRun

# Each test replaces score with a fake returning a ScoreRun written by hand: the records as stored (data) and what
# score computes now (routes). The gate's job is to compare the two.


def test_current_carbon_intensities_pass(monkeypatch):
    carbon_intensity = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "pue": {"low": 1.1, "high": 1.6},
        "pue_source": "fallback",
        "speed": None,
        "speed_source": "fallback",
        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "sci_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_intensity": carbon_intensity}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_intensity": carbon_intensity}}),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == []


def test_the_gate_runs_score_on_the_root_without_writing(monkeypatch):
    fake_score = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.check_carbon_intensities.score", fake_score)
    check_carbon_intensities(Path("/repo"))
    fake_score.assert_called_once_with(Path("/repo"), write=False)


def test_scores_errors_are_passed_through(monkeypatch):
    run = ScoreRun(errors=["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"], written=[])
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == ["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"]


def test_a_missing_carbon_intensity_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {}}},
        routes=cast(
            Any,
            {
                "acme-m-70b": {
                    "carbon_intensity": {
                        "grids": ["ch"],
                        "energy_wh": {"low": 0.5, "high": 0.6},
                        "embodied_g": {"low": 0.05, "high": 0.06},
                        "pue": {"low": 1.1, "high": 1.6},
                        "pue_source": "fallback",
                        "speed": None,
                        "speed_source": "fallback",
                        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                        "sci_g": {"low": 0.065, "high": 0.078},
                        "band": [2, 2],
                    }
                }
            },
        ),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: is missing the carbon_intensity field; run `python -m build score`"
    ]


def test_a_moved_value_is_named(monkeypatch):
    stored = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "pue": {"low": 1.1, "high": 1.6},
        "pue_source": "fallback",
        "speed": None,
        "speed_source": "fallback",
        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "sci_g": {"low": 0.0, "high": 0.0},
        "band": [2, 2],
    }
    computed = {**stored, "sci_g": {"low": 0.065, "high": 0.078}}
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_intensity": stored}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_intensity": computed}}),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its carbon intensity is out of date (sci_g); run `python -m build score`"
    ]


def test_several_moved_values_are_named_in_the_fields_order(monkeypatch):
    stored = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "pue": {"low": 1.1, "high": 1.6},
        "pue_source": "fallback",
        "speed": None,
        "speed_source": "fallback",
        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "sci_g": {"low": 0.0, "high": 0.0},
        "band": [1, 1],
    }
    computed = {**stored, "sci_g": {"low": 0.065, "high": 0.078}, "band": [2, 2]}
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_intensity": stored}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_intensity": computed}}),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its carbon intensity is out of date (sci_g, band); run `python -m build score`"
    ]


def test_a_moved_disclosure_rating_is_not_this_gates_concern(monkeypatch):
    carbon_intensity = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "pue": {"low": 1.1, "high": 1.6},
        "pue_source": "fallback",
        "speed": None,
        "speed_source": "fallback",
        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "sci_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "routes": {
                "acme-m-70b": {"carbon_intensity": carbon_intensity, "disclosure_rating": {"letter": "A", "gap": None}}
            }
        },
        routes=cast(
            Any,
            {
                "acme-m-70b": {
                    "carbon_intensity": carbon_intensity,
                    "disclosure_rating": {"letter": "B", "gap": "The grid is disclosed, not the facility."},
                }
            },
        ),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == []


def test_routes_are_named_in_order(monkeypatch):
    carbon_intensity = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "pue": {"low": 1.1, "high": 1.6},
        "pue_source": "fallback",
        "speed": None,
        "speed_source": "fallback",
        "grid_intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "sci_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"zeta-m-70b": {}, "acme-m-70b": {}}},
        routes=cast(
            Any,
            {
                "zeta-m-70b": {"carbon_intensity": carbon_intensity},
                "acme-m-70b": {"carbon_intensity": carbon_intensity},
            },
        ),
    )
    monkeypatch.setattr("build.check_carbon_intensities.score", lambda root, write: run)
    assert check_carbon_intensities(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: is missing the carbon_intensity field; run `python -m build score`",
        "routes/zeta-m-70b.yaml: is missing the carbon_intensity field; run `python -m build score`",
    ]
