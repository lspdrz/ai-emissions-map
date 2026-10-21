from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

from build.check_carbon_scores import check_carbon_scores
from build.score import ScoreRun

# Each test replaces score with a fake returning a ScoreRun written by hand: the records as stored (data) and what
# score computes now (routes). The gate's job is to compare the two.


def test_current_scores_pass(monkeypatch):
    carbon_score = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "intensity_years": [2025],
        "score_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_score": carbon_score}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_score": carbon_score}}),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == []


def test_the_gate_runs_score_on_the_root_without_writing(monkeypatch):
    fake_score = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.check_carbon_scores.score", fake_score)
    check_carbon_scores(Path("/repo"))
    fake_score.assert_called_once_with(Path("/repo"), write=False)


def test_scores_errors_are_passed_through(monkeypatch):
    run = ScoreRun(errors=["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"], written=[])
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == ["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"]


def test_a_missing_score_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {}}},
        routes=cast(
            Any,
            {
                "acme-m-70b": {
                    "carbon_score": {
                        "grids": ["ch"],
                        "energy_wh": {"low": 0.5, "high": 0.6},
                        "embodied_g": {"low": 0.05, "high": 0.06},
                        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                        "intensity_years": [2025],
                        "score_g": {"low": 0.065, "high": 0.078},
                        "band": [2, 2],
                    }
                }
            },
        ),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: is missing the carbon_score field; run `python -m build score`"
    ]


def test_a_moved_value_is_named(monkeypatch):
    stored = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "intensity_years": [2025],
        "score_g": {"low": 0.0, "high": 0.0},
        "band": [2, 2],
    }
    computed = {**stored, "score_g": {"low": 0.065, "high": 0.078}}
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_score": stored}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_score": computed}}),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its carbon score is out of date (score_g); run `python -m build score`"
    ]


def test_several_moved_values_are_named_in_the_fields_order(monkeypatch):
    stored = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "intensity_years": [2025],
        "score_g": {"low": 0.0, "high": 0.0},
        "band": [1, 1],
    }
    computed = {**stored, "score_g": {"low": 0.065, "high": 0.078}, "band": [2, 2]}
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"acme-m-70b": {"carbon_score": stored}}},
        routes=cast(Any, {"acme-m-70b": {"carbon_score": computed}}),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its carbon score is out of date (score_g, band); run `python -m build score`"
    ]


def test_a_moved_disclosure_rating_is_not_this_gates_concern(monkeypatch):
    carbon_score = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "intensity_years": [2025],
        "score_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "routes": {"acme-m-70b": {"carbon_score": carbon_score, "disclosure_rating": {"letter": "A", "gap": None}}}
        },
        routes=cast(
            Any,
            {
                "acme-m-70b": {
                    "carbon_score": carbon_score,
                    "disclosure_rating": {"letter": "B", "gap": "The grid is disclosed, not the facility."},
                }
            },
        ),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == []


def test_routes_are_named_in_order(monkeypatch):
    carbon_score = {
        "grids": ["ch"],
        "energy_wh": {"low": 0.5, "high": 0.6},
        "embodied_g": {"low": 0.05, "high": 0.06},
        "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
        "intensity_years": [2025],
        "score_g": {"low": 0.065, "high": 0.078},
        "band": [2, 2],
    }
    run = ScoreRun(
        errors=[],
        written=[],
        data={"routes": {"zeta-m-70b": {}, "acme-m-70b": {}}},
        routes=cast(Any, {"zeta-m-70b": {"carbon_score": carbon_score}, "acme-m-70b": {"carbon_score": carbon_score}}),
    )
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: run)
    assert check_carbon_scores(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: is missing the carbon_score field; run `python -m build score`",
        "routes/zeta-m-70b.yaml: is missing the carbon_score field; run `python -m build score`",
    ]


# Grids: each stored intensity: against what score resolves now from Ember's table.


def _grid_run(stored: dict) -> ScoreRun:
    computed = {"g_per_kwh": 39.3, "year": 2025, "geography": "CH", "source": "Ember"}
    return ScoreRun(
        errors=[],
        written=[],
        data={"grids": {"ch": stored}, "routes": {}},
        routes={},
        orgs={},
        grids=cast(Any, {"ch": computed}),
    )


def test_a_current_grid_intensity_passes(monkeypatch):
    stored = {"intensity": {"g_per_kwh": 39.3, "year": 2025, "geography": "CH", "source": "Ember"}}
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: _grid_run(stored))
    assert check_carbon_scores(Path("/repo")).errors == []


def test_a_missing_grid_intensity_is_named(monkeypatch):
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: _grid_run({}))
    assert check_carbon_scores(Path("/repo")).errors == [
        "grids/ch.yaml: is missing the intensity field; run `python -m build score`"
    ]


def test_a_grid_intensity_moved_by_a_refreshed_table_is_named(monkeypatch):
    stored = {"intensity": {"g_per_kwh": 34.6, "year": 2024, "geography": "CH", "source": "Ember"}}
    monkeypatch.setattr("build.check_carbon_scores.score", lambda root, write: _grid_run(stored))
    assert check_carbon_scores(Path("/repo")).errors == [
        "grids/ch.yaml: its intensity is out of date (g_per_kwh, year); run `python -m build score`"
    ]
