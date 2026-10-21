from typing import Any

import yaml

from build.schemas.score import RouteScore
from build.score import GENERATED_COMMENT, org_text, route_grids, route_text, score, score_organizations
from build.utils.range import Range
from tests.builders.corpus import make_corpus
from tests.builders.files import write_corpus, write_grid_intensities, write_source
from tests.builders.grid import make_grid
from tests.builders.location import make_location
from tests.builders.model import make_model
from tests.builders.organization import make_organization
from tests.builders.route import make_route


# An organization's rating is computed from its own routes' ratings.


def test_an_organization_is_rated_on_its_own_routes_only():
    corpus = make_corpus(
        organizations=[make_organization(name="acme"), make_organization(name="other"), make_organization(name="idle")],
        routes=[
            make_route(name="acme-m-70b", org="acme"),
            make_route(name="acme-m-70b-eu", org="acme"),
            make_route(name="other-m-70b", org="other"),
        ],
    )
    route_scores: Any = {  # only the letters matter here
        "acme-m-70b": {"disclosure_rating": {"letter": "A", "gap": None}},
        "acme-m-70b-eu": {"disclosure_rating": {"letter": "B", "gap": None}},
        "other-m-70b": {"disclosure_rating": {"letter": "D", "gap": None}},
    }
    orgs = score_organizations(corpus, route_scores)
    assert {name: o["summary"] for name, o in orgs.items()} == {
        "acme": "B (1 route at A, 1 route at B)",
        "idle": "Not rated (no routes)",
        "other": "D (1 route at D)",
    }


# A route's grids: the grid files its candidates resolve to.


def test_a_grid_candidate_resolves_to_its_grid_file():
    route = make_route(location=make_location(candidates=["grid:de"]))
    ch, de = make_grid(name="ch", country="CH", zone="CH"), make_grid(name="de", country="DE", zone="DE")
    assert route_grids(route, {"ch": ch, "de": de}, {}) == {"de": de}


def test_a_cloud_candidate_resolves_to_the_grid_file_claiming_its_zone():
    route = make_route(location=make_location(candidates=["cloud:cloudx:eu-de"]))
    ch, de = make_grid(name="ch", country="CH", zone="CH"), make_grid(name="de", country="DE", zone="DE")
    assert route_grids(route, {"ch": ch, "de": de}, {("cloudx", "eu-de"): ["DE"]}) == {"de": de}


def test_a_cloud_region_spanning_two_zones_resolves_to_both_grid_files():
    route = make_route(location=make_location(candidates=["cloud:azure:northeurope"]))
    fi, ie = make_grid(name="fi", country="FI", zone="FI"), make_grid(name="ie", country="IE", zone="IE")
    assert route_grids(route, {"fi": fi, "ie": ie}, {("azure", "northeurope"): ["FI", "IE"]}) == {"fi": fi, "ie": ie}


def test_candidates_on_one_grid_resolve_to_it_once():
    route = make_route(location=make_location(candidates=["grid:de", "cloud:cloudx:eu-de"]))
    de = make_grid(name="de", country="DE", zone="DE")
    assert route_grids(route, {"de": de}, {("cloudx", "eu-de"): ["DE"]}) == {"de": de}


def test_a_routes_grids_are_sorted_by_name():
    route = make_route(location=make_location(candidates=["grid:fr", "grid:de"]))
    de, fr = make_grid(name="de", country="DE", zone="DE"), make_grid(name="fr", country="FR", zone="FR")
    assert list(route_grids(route, {"de": de, "fr": fr}, {})) == ["de", "fr"]


# The fields score writes go below GENERATED_COMMENT, at the end of a file: everything below it is rewritten, nothing
# above it.


def test_a_routes_fields_are_appended_below_the_comment():
    route_score: Any = {"disclosure_rating": {"letter": "B", "gap": None}, "carbon_score": {"grids": ["ch"]}}
    assert route_text("name: acme-m-70b\n# a curated comment\norg: acme\n", route_score) == (
        "name: acme-m-70b\n# a curated comment\norg: acme\n\n"
        + GENERATED_COMMENT
        + "\ndisclosure_rating:\n  letter: B\n  gap: null\n\ncarbon_score:\n  grids:\n  - ch\n"
    )


def test_a_route_written_again_with_the_same_fields_is_unchanged():
    route_score: Any = {"disclosure_rating": {"letter": "B", "gap": None}, "carbon_score": {"grids": ["ch"]}}
    text = (
        "name: acme-m-70b\n\n"
        + GENERATED_COMMENT
        + "\ndisclosure_rating:\n  letter: B\n  gap: null\n\ncarbon_score:\n  grids:\n  - ch\n"
    )
    assert route_text(text, route_score) == text


def test_a_routes_fields_that_moved_replace_the_old_ones():
    route_score: Any = {"disclosure_rating": {"letter": "C", "gap": None}, "carbon_score": {"grids": ["ch", "de"]}}
    text = (
        "name: acme-m-70b\n\n"
        + GENERATED_COMMENT
        + "\ndisclosure_rating:\n  letter: B\n  gap: null\n\ncarbon_score:\n  grids:\n  - ch\n"
    )
    assert route_text(text, route_score) == (
        "name: acme-m-70b\n\n"
        + GENERATED_COMMENT
        + "\ndisclosure_rating:\n  letter: C\n  gap: null\n\ncarbon_score:\n  grids:\n  - ch\n  - de\n"
    )


def test_an_organizations_field_is_appended_below_the_comment():
    org_rating: Any = {"letter": "B", "gap": None}
    assert org_text("name: acme\n", org_rating) == (
        "name: acme\n\n" + GENERATED_COMMENT + "\ndisclosure_rating:\n  letter: B\n  gap: null\n"
    )


def test_everything_below_the_comment_is_rewritten():
    org_rating: Any = {"letter": "B", "gap": None}
    edited = "name: acme\n\n" + GENERATED_COMMENT + "\ndisclosure_rating:\n  letter: A\nnote: added by hand\n"
    assert org_text(edited, org_rating) == (
        "name: acme\n\n" + GENERATED_COMMENT + "\ndisclosure_rating:\n  letter: B\n  gap: null\n"
    )


def test_trailing_blank_lines_above_the_comment_become_one():
    org_rating: Any = {"letter": "B", "gap": None}
    assert org_text("name: acme\n\n\n", org_rating) == (
        "name: acme\n\n" + GENERATED_COMMENT + "\ndisclosure_rating:\n  letter: B\n  gap: null\n"
    )


def test_written_fields_read_back_equal():
    route_score: RouteScore = {
        "disclosure_rating": {"letter": "C", "gap": "The grid is not determined: several are possible."},
        "carbon_score": {
            "grids": ["de", "fr"],
            "energy_wh": {"low": 0.5, "high": 0.6},
            "embodied_g": {"low": 0.05, "high": 0.06},
            "intensity_g_per_kwh": {"low": 40.0, "high": 330.0},
            "intensity_years": [2025],
            "score_g": {"low": 0.07, "high": 0.258},
            "band": [2, 3],
        },
    }
    text = route_text("name: acme-m-70b\n", route_score)
    assert yaml.safe_load(text) == {"name": "acme-m-70b", **route_score}


# python -m build score, end to end. The tests that reach scoring set E and M to zero: score always computes a carbon
# score, and its value is not what these tests are about.


def _rel(root, paths):
    return [p.relative_to(root).as_posix() for p in paths]


def test_score_writes_the_files_whose_fields_change(tmp_path, monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[make_grid(name="ch", country="CH", zone="CH")],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    write_grid_intensities(tmp_path, {"CH": {2025: 30.0}})
    run = score(tmp_path)
    assert (run.errors, _rel(tmp_path, run.written)) == (
        [],
        ["sources/grids/ch.yaml", "sources/organizations/acme.yaml", "sources/routes/acme-m-70b.yaml"],
    )


def test_a_second_run_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[make_grid(name="ch", country="CH", zone="CH")],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    write_grid_intensities(tmp_path, {"CH": {2025: 30.0}})
    score(tmp_path)
    rerun = score(tmp_path)
    assert (rerun.errors, rerun.written) == ([], [])


def test_score_writes_nothing_when_there_are_errors(tmp_path):
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    before = {p: p.read_text() for p in (tmp_path / "sources").rglob("*.yaml")}
    run = score(tmp_path)
    assert (run.errors, run.written) == (["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"], [])
    assert {p: p.read_text() for p in (tmp_path / "sources").rglob("*.yaml")} == before


def test_score_resolves_cloud_regions_through_the_committed_table(tmp_path):
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[],
            routes=[
                make_route(
                    name="acme-m-70b",
                    org="acme",
                    model="m-70b",
                    location=make_location(candidates=["cloud:cloudx:eu-de"]),
                )
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    write_source(tmp_path, "snapshots/cloud_regions.csv", "vendor,region,zone\ncloudx,eu-de,DE\n")
    assert score(tmp_path).errors == [
        "routes/acme-m-70b.yaml: cloud region cloudx:eu-de maps to zone 'DE', which has no grid file; "
        "add one (docs/workflows/add-grid.md)"
    ]


def test_check_mode_lists_what_score_would_write_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[make_grid(name="ch", country="CH", zone="CH")],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    write_grid_intensities(tmp_path, {"CH": {2025: 30.0}})
    before = {p: p.read_text() for p in (tmp_path / "sources").rglob("*.yaml")}
    run = score(tmp_path, write=False)
    assert (run.errors, _rel(tmp_path, run.written)) == (
        [],
        ["sources/grids/ch.yaml", "sources/organizations/acme.yaml", "sources/routes/acme-m-70b.yaml"],
    )
    assert {p: p.read_text() for p in (tmp_path / "sources").rglob("*.yaml")} == before


def test_score_reports_grids_without_an_ember_value(tmp_path):
    # No grid-intensity table at all: every grid is left without a value, and score says so.
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[make_grid(name="ch", country="CH", zone="CH")],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    run = score(tmp_path)
    assert (run.errors, run.written) == (
        ["grids/ch.yaml: Ember has no intensity for 'CH' in 2025 or earlier; see docs/workflows/add-grid.md"],
        [],
    )


def test_score_writes_each_grids_intensity_below_the_comment(tmp_path, monkeypatch):
    monkeypatch.setattr("build.carbon_score.ecologits_estimate", lambda model: (Range.point(0.0), Range.point(0.0)))
    write_corpus(
        tmp_path,
        make_corpus(
            organizations=[make_organization(name="acme")],
            grids=[make_grid(name="ch", country="CH", zone="CH")],
            routes=[
                make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
            ],
            models=[make_model(name="m-70b")],
        ),
    )
    write_grid_intensities(tmp_path, {"CH": {2024: 34.6, 2025: 39.3}})
    score(tmp_path)
    text = (tmp_path / "sources" / "grids" / "ch.yaml").read_text()
    assert text.endswith(
        GENERATED_COMMENT + "\nintensity:\n  g_per_kwh: 39.3\n  year: 2025\n  geography: CH\n  source: Ember\n"
    )
