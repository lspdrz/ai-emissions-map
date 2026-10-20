from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

from build.check_disclosure_ratings import check_disclosure_ratings
from build.score import ScoreRun

# Each test replaces score with a fake returning a ScoreRun written by hand: the records as stored (data) and what
# score computes now (routes, orgs). The gate's job is to compare the two.


def test_current_ratings_pass(monkeypatch):
    org_rating = {"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"}
    route_rating = {"letter": "B", "gap": "The grid is disclosed, not the facility."}
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {"acme": {"disclosure_rating": org_rating}},
            "routes": {"acme-m-70b": {"disclosure_rating": route_rating}},
        },
        routes=cast(Any, {"acme-m-70b": {"disclosure_rating": route_rating}}),
        orgs=cast(Any, {"acme": org_rating}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == []


def test_the_gate_runs_score_on_the_root_without_writing(monkeypatch):
    fake_score = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.check_disclosure_ratings.score", fake_score)
    check_disclosure_ratings(Path("/repo"))
    fake_score.assert_called_once_with(Path("/repo"), write=False)


def test_scores_errors_are_passed_through(monkeypatch):
    run = ScoreRun(errors=["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"], written=[])
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == ["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"]


def test_an_organization_without_a_rating_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={"organizations": {"acme": {}}, "routes": {}},
        routes=cast(Any, {}),
        orgs=cast(Any, {"acme": {"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"}}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "organizations/acme.yaml: is missing the disclosure_rating field; run `python -m build score`"
    ]


def test_a_route_without_a_rating_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={"organizations": {}, "routes": {"acme-m-70b": {}}},
        routes=cast(
            Any,
            {"acme-m-70b": {"disclosure_rating": {"letter": "B", "gap": "The grid is disclosed, not the facility."}}},
        ),
        orgs=cast(Any, {}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: is missing the disclosure_rating field; run `python -m build score`"
    ]


def test_an_organizations_moved_rating_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {
                "acme": {
                    "disclosure_rating": {"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"}
                }
            },
            "routes": {},
        },
        routes=cast(Any, {}),
        orgs=cast(Any, {"acme": {"letter": "B", "mean": 2.0, "spread": {"C": 1}, "summary": "B (1 route at B)"}}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "organizations/acme.yaml: its disclosure rating is out of date (spread); run `python -m build score`"
    ]


def test_an_organizations_several_moved_values_are_named_in_the_fields_order(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {
                "acme": {
                    "disclosure_rating": {"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"}
                }
            },
            "routes": {},
        },
        routes={},
        orgs=cast(Any, {"acme": {"letter": "C", "mean": 1.0, "spread": {"C": 1}, "summary": "C (1 route at C)"}}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "organizations/acme.yaml: its disclosure rating is out of date (letter, mean, spread, summary); "
        "run `python -m build score`"
    ]


def test_a_routes_moved_rating_is_named(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {},
            "routes": {"acme-m-70b": {"disclosure_rating": {"letter": "B", "gap": "Old wording."}}},
        },
        routes=cast(
            Any,
            {"acme-m-70b": {"disclosure_rating": {"letter": "B", "gap": "The grid is disclosed, not the facility."}}},
        ),
        orgs=cast(Any, {}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its disclosure rating is out of date (gap); run `python -m build score`"
    ]


def test_several_moved_values_are_named_in_the_fields_order(monkeypatch):
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {},
            "routes": {
                "acme-m-70b": {"disclosure_rating": {"letter": "D", "gap": "Location not disclosed by the provider."}}
            },
        },
        routes=cast(
            Any,
            {"acme-m-70b": {"disclosure_rating": {"letter": "B", "gap": "The grid is disclosed, not the facility."}}},
        ),
        orgs=cast(Any, {}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "routes/acme-m-70b.yaml: its disclosure rating is out of date (letter, gap); run `python -m build score`"
    ]


def test_a_moved_carbon_score_is_not_this_gates_concern(monkeypatch):
    route_rating = {"letter": "B", "gap": "The grid is disclosed, not the facility."}
    run = ScoreRun(
        errors=[],
        written=[],
        data={
            "organizations": {},
            "routes": {
                "acme-m-70b": {
                    "disclosure_rating": route_rating,
                    "carbon_score": {"score_g": {"low": 0.0, "high": 0.0}},
                }
            },
        },
        routes=cast(
            Any,
            {
                "acme-m-70b": {
                    "disclosure_rating": route_rating,
                    "carbon_score": {"score_g": {"low": 0.065, "high": 0.078}},
                }
            },
        ),
        orgs=cast(Any, {}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == []


def test_organizations_are_named_before_routes_each_in_order(monkeypatch):
    org_rating = {"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"}
    route_rating = {"letter": "B", "gap": "The grid is disclosed, not the facility."}
    run = ScoreRun(
        errors=[],
        written=[],
        data={"organizations": {"zeta": {}, "acme": {}}, "routes": {"zeta-m-70b": {}, "acme-m-70b": {}}},
        routes=cast(
            Any, {"zeta-m-70b": {"disclosure_rating": route_rating}, "acme-m-70b": {"disclosure_rating": route_rating}}
        ),
        orgs=cast(Any, {"zeta": org_rating, "acme": org_rating}),
    )
    monkeypatch.setattr("build.check_disclosure_ratings.score", lambda root, write: run)
    assert check_disclosure_ratings(Path("/repo")).errors == [
        "organizations/acme.yaml: is missing the disclosure_rating field; run `python -m build score`",
        "organizations/zeta.yaml: is missing the disclosure_rating field; run `python -m build score`",
        "routes/acme-m-70b.yaml: is missing the disclosure_rating field; run `python -m build score`",
        "routes/zeta-m-70b.yaml: is missing the disclosure_rating field; run `python -m build score`",
    ]
