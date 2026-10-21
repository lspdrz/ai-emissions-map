from datetime import date
from importlib.metadata import version

import pytest

from build.constants.config import CARBON_BAND_UPPER, DRAFT, GRID_YEAR, METHODOLOGY_VERSION, PUE
from build.generate_site_data import (
    SCHEMA,
    build_data,
    check_contract,
    model_entry,
    organization_entry,
    organization_evidence,
    route_entry,
    route_label,
)
from tests.builders.corpus import make_corpus
from tests.builders.evidence import make_evidence
from tests.builders.location import make_location
from tests.builders.model import make_model
from tests.builders.organization import make_organization
from tests.builders.route import make_route


# The contract: the data file holds only the fields the site displays, at every level.


def test_data_within_the_contract_has_no_problems():
    data = {"schema": SCHEMA, "meta": {"release_date": "2026-10-08"}, "organizations": [], "models": [], "routes": []}
    assert check_contract(data) == []


@pytest.mark.parametrize(
    "data, problem",
    [
        ({"unknown_field": {}}, "top level: field 'unknown_field' is not in the contract"),
        ({"meta": {"unknown_field": {}}}, "meta: field 'unknown_field' is not in the contract"),
        ({"meta": {"grid": {"unknown_field": {}}}}, "meta.grid: field 'unknown_field' is not in the contract"),
        ({"meta": {"counts": {"unknown_field": 1}}}, "meta.counts: field 'unknown_field' is not in the contract"),
        ({"organizations": [{"unknown_field": {}}]}, "organizations[]: field 'unknown_field' is not in the contract"),
        (
            {"organizations": [{"rating": {"unknown_field": {}}}]},
            "organizations[].rating: field 'unknown_field' is not in the contract",
        ),
        (
            {"organizations": [{"evidence": [{"unknown_field": {}}]}]},
            "organizations[].evidence[]: field 'unknown_field' is not in the contract",
        ),
        ({"models": [{"unknown_field": {}}]}, "models[]: field 'unknown_field' is not in the contract"),
        ({"routes": [{"unknown_field": {}}]}, "routes[]: field 'unknown_field' is not in the contract"),
    ],
)
def test_a_field_outside_the_contract_is_named_with_its_level(data, problem):
    assert check_contract(data) == [problem]


def test_a_level_that_is_not_an_object_has_no_fields_to_check():
    assert check_contract({"meta": {"counts": None}}) == []


# A route's entry: its stored ratings and how it is labelled.


def test_a_routes_entry_carries_its_stored_fields():
    route = make_route(
        name="acme-m-70b",
        org="acme",
        model="m-70b",
        location=make_location(candidates=["grid:ch"]),
        disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
        carbon_score={
            "grids": ["ch"],
            "energy_wh": {"low": 0.5, "high": 0.6},
            "embodied_g": {"low": 0.05, "high": 0.06},
            "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
            "intensity_years": [2025],
            "score_g": {"low": 0.065, "high": 0.078},
            "band": [2, 2],
        },
    )
    assert route_entry("acme-m-70b", route) == {
        "slug": "acme-m-70b",
        "org": "acme",
        "model": "m-70b",
        "label": "1 grid",
        "default": False,
        "letter": "B",
        "gap": "The grid is disclosed, not the facility.",
        "score": {"low": 0.065, "high": 0.078},
        "energy": {"low": 0.5, "high": 0.6},
        "intensity": {"low": 30.0, "high": 30.0},
        "embodied": {"low": 0.05, "high": 0.06},
        "band": [2, 2],
        "served_as": None,
    }


def test_a_default_routes_entry_is_marked_default():
    route = make_route(
        name="acme-m-70b",
        org="acme",
        model="m-70b",
        location=make_location(candidates=["grid:ch"]),
        default=True,
        disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
        carbon_score={
            "grids": ["ch"],
            "energy_wh": {"low": 0.5, "high": 0.6},
            "embodied_g": {"low": 0.05, "high": 0.06},
            "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
            "intensity_years": [2025],
            "score_g": {"low": 0.065, "high": 0.078},
            "band": [2, 2],
        },
    )
    assert route_entry("acme-m-70b", route)["default"] is True


def test_a_routes_entry_carries_the_name_it_is_served_as():
    route = make_route(
        name="acme-m-70b",
        org="acme",
        model="m-70b",
        location=make_location(candidates=["grid:ch"]),
        served_as="acme/M-70B-Instruct",
        served_model_evidence=[make_evidence(kind="primary")],
        disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
        carbon_score={
            "grids": ["ch"],
            "energy_wh": {"low": 0.5, "high": 0.6},
            "embodied_g": {"low": 0.05, "high": 0.06},
            "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
            "intensity_years": [2025],
            "score_g": {"low": 0.065, "high": 0.078},
            "band": [2, 2],
        },
    )
    assert route_entry("acme-m-70b", route)["served_as"] == "acme/M-70B-Instruct"


def test_a_routes_label_is_its_locations_label():
    location = make_location(candidates=["grid:ch"], label="Switzerland")
    assert route_label(location, ["ch"]) == "Switzerland"


def test_a_route_on_one_grid_without_a_label_is_labelled_1_grid():
    assert route_label(make_location(candidates=["grid:ch"]), ["ch"]) == "1 grid"


def test_a_route_on_several_grids_without_a_label_is_labelled_with_their_count():
    location = make_location(candidates=["cloud:cloudx:eu-de", "cloud:cloudx:eu-fr"])
    assert route_label(location, ["de", "fr"]) == "2 grids"


def test_a_route_with_no_grids_is_labelled_not_disclosed():
    location = make_location(candidates=[], evidence=[make_evidence(kind="corroborating")])
    assert route_label(location, []) == "Not disclosed"


# An organization's entry: who it is, its rating, its routes and the sources behind them.


def test_an_organizations_entry_carries_its_record_and_rating():
    org = make_organization(
        name="acme",
        display_name="Acme",
        type="inference_host",
        homepage="https://acme.example",
        country="CH",
        description="Serves from Switzerland.",
        disclosure_rating={"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"},
    )
    assert organization_entry("acme", org, {}) == {
        "slug": "acme",
        "display_name": "Acme",
        "type": "inference_host",
        "country": "CH",
        "homepage": "https://acme.example",
        "description": "Serves from Switzerland.",
        "rating": {"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"},
        "routes": [],
        "evidence": [],
    }


def test_an_organizations_entry_lists_its_own_routes_sorted():
    org = make_organization(
        name="acme", disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 2}, "summary": "B (2 routes at B)"}
    )
    routes = {
        "acme-m-8b": make_route(name="acme-m-8b", org="acme", model="m-8b"),
        "acme-m-70b": make_route(name="acme-m-70b", org="acme", model="m-70b"),
        "other-m-70b": make_route(name="other-m-70b", org="other", model="m-70b"),
    }
    assert organization_entry("acme", org, routes)["routes"] == ["acme-m-70b", "acme-m-8b"]


def test_a_source_is_listed_with_its_quoted_passages_when_it_was_read_and_its_routes():
    evidence = make_evidence(
        url="https://acme.example/regions", shows='Regions page: "m-70b is served from Acme 1"', accessed="2026-09-01"
    )
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[evidence]))}
    assert organization_evidence(routes, ["acme-m-70b"]) == [
        {
            "url": "https://acme.example/regions",
            "quotes": ["m-70b is served from Acme 1"],
            "accessed": "2026-09-01",
            "routes": ["acme-m-70b"],
        }
    ]


def test_a_corroborating_source_is_not_listed():
    press = make_evidence(
        kind="corroborating", url="https://news.example/acme", shows='Article: "Acme opens in Geneva"'
    )
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=[], evidence=[press]))}
    assert organization_evidence(routes, ["acme-m-70b"]) == []


def test_a_source_two_routes_cite_is_listed_once_with_both():
    evidence = make_evidence(url="https://acme.example/regions", shows='Regions page: "served from Acme 1"')
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[evidence])),
        "acme-m-8b": make_route(name="acme-m-8b", model="m-8b", location=make_location(evidence=[evidence])),
    }
    [entry] = organization_evidence(routes, ["acme-m-70b", "acme-m-8b"])
    assert entry["routes"] == ["acme-m-70b", "acme-m-8b"]


def test_a_route_citing_one_source_twice_is_listed_once():
    regions = make_evidence(url="https://acme.example/regions", shows='Regions page: "served from Acme 1"')
    regions_again = make_evidence(url="https://acme.example/regions", shows='Regions page: "Acme 1 is in Geneva"')
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[regions, regions_again]))}
    [entry] = organization_evidence(routes, ["acme-m-70b"])
    assert entry["routes"] == ["acme-m-70b"]


def test_a_passage_quoted_twice_from_one_source_is_listed_once():
    evidence = make_evidence(url="https://acme.example/regions", shows='Regions page: "served from Acme 1"')
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[evidence])),
        "acme-m-8b": make_route(name="acme-m-8b", model="m-8b", location=make_location(evidence=[evidence])),
    }
    [entry] = organization_evidence(routes, ["acme-m-70b", "acme-m-8b"])
    assert entry["quotes"] == ["served from Acme 1"]


def test_a_source_read_more_than_once_is_dated_when_it_was_last_read():
    first = make_evidence(
        url="https://acme.example/regions", shows='Regions page: "served from Acme 1"', accessed="2026-09-01"
    )
    later = make_evidence(
        url="https://acme.example/regions", shows='Regions page: "served from Acme 1"', accessed="2026-10-01"
    )
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[first])),
        "acme-m-8b": make_route(name="acme-m-8b", model="m-8b", location=make_location(evidence=[later])),
    }
    [entry] = organization_evidence(routes, ["acme-m-70b", "acme-m-8b"])
    assert entry["accessed"] == "2026-10-01"


def test_a_quote_shorter_than_8_characters_is_not_a_passage():
    evidence = make_evidence(url="https://acme.example/regions", shows='Regions page: "Geneva"')
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[evidence]))}
    [entry] = organization_evidence(routes, ["acme-m-70b"])
    assert entry["quotes"] == []


def test_sources_are_listed_by_url():
    regions = make_evidence(url="https://acme.example/regions", shows='Regions page: "served from Acme 1"')
    about = make_evidence(url="https://acme.example/about", shows='About page: "our data centers in Geneva"')
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(evidence=[regions, about]))}
    assert [entry["url"] for entry in organization_evidence(routes, ["acme-m-70b"])] == [
        "https://acme.example/about",
        "https://acme.example/regions",
    ]


# A model's entry: its name and parameter counts.


def test_a_models_entry_carries_its_name_and_counts():
    model = make_model(
        name="m-70b", display_name="M 70B", architecture="dense", active_b={"min": 70, "max": 72}, total_b=72
    )
    assert model_entry("m-70b", model) == {
        "slug": "m-70b",
        "display_name": "M 70B",
        "architecture": "dense",
        "active_b": {"min": 70, "max": 72},
        "total_b": 72,
    }


def test_a_model_without_a_display_name_is_shown_by_its_slug():
    assert model_entry("m-70b", make_model(name="m-70b"))["display_name"] == "m-70b"


# build_data: the whole file. Every test writes its routes with the fields `python -m build score` stores, by hand.


def test_the_data_file_names_its_schema():
    assert build_data(make_corpus(), date(2026, 10, 8))["schema"] == SCHEMA


def test_meta_states_the_release_date_and_the_configured_method():
    meta = build_data(make_corpus(), date(2026, 10, 8))["meta"]
    assert {
        key: meta[key]
        for key in ("release_date", "methodology_version", "ecologits_version", "pue", "band_upper", "draft", "grid")
    } == {
        "release_date": "2026-10-08",
        "methodology_version": METHODOLOGY_VERSION,
        "ecologits_version": version("ecologits"),
        "pue": list(PUE),
        "band_upper": list(CARBON_BAND_UPPER),
        "draft": DRAFT,
        "grid": {"source": "Ember", "year": GRID_YEAR},
    }


def test_meta_counts_organizations_routes_models_and_distinct_grids():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 2}, "summary": "B (2 routes at B)"},
            )
        ],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "intensity_years": [2025],
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            ),
            make_route(
                name="acme-m-70b-eu",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch", "grid:de"]),
                disclosure_rating={"letter": "C", "gap": "The grid is not determined: several are possible."},
                carbon_score={
                    "grids": ["ch", "de"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 330.0},
                    "intensity_years": [2025],
                    "score_g": {"low": 0.065, "high": 0.258},
                    "band": [2, 3],
                },
            ),
        ],
        models=[make_model(name="m-70b")],
    )
    assert build_data(corpus, date(2026, 10, 8))["meta"]["counts"] == {
        "organizations": 1,
        "routes": 2,
        "models": 1,
        "grids": 2,  # ch counted once
    }


def test_a_model_no_route_serves_is_left_out():
    corpus = make_corpus(models=[make_model(name="m-70b")])
    assert build_data(corpus, date(2026, 10, 8))["models"] == []


def test_entries_are_sorted_by_slug():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="zeta",
                disclosure_rating={"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"},
            ),
            make_organization(
                name="acme",
                disclosure_rating={"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"},
            ),
        ],
        routes=[
            make_route(
                name="acme-m-8b",
                org="acme",
                model="m-8b",
                location=make_location(candidates=[], evidence=[make_evidence(kind="corroborating")]),
                disclosure_rating={"letter": "D", "gap": "Location not disclosed by the provider."},
                carbon_score={
                    "grids": [],
                    "energy_wh": {"low": 0.08, "high": 0.12},
                    "embodied_g": {"low": 0.007, "high": 0.007},
                    "intensity_g_per_kwh": None,
                    "intensity_years": [],
                    "score_g": None,
                    "band": None,
                },
            ),
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=[], evidence=[make_evidence(kind="corroborating")]),
                disclosure_rating={"letter": "D", "gap": "Location not disclosed by the provider."},
                carbon_score={
                    "grids": [],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": None,
                    "intensity_years": [],
                    "score_g": None,
                    "band": None,
                },
            ),
        ],
        models=[make_model(name="m-8b"), make_model(name="m-70b")],
    )
    data = build_data(corpus, date(2026, 10, 8))
    assert (
        [o["slug"] for o in data["organizations"]],
        [r["slug"] for r in data["routes"]],
        [m["slug"] for m in data["models"]],
    ) == (["acme", "zeta"], ["acme-m-70b", "acme-m-8b"], ["m-70b", "m-8b"])


def test_the_intensity_spread_is_the_highest_scored_intensity_over_the_lowest():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 2}, "summary": "B (2 routes at B)"},
            )
        ],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "intensity_years": [2025],
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            ),
            make_route(
                name="acme-m-70b-de",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:de"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["de"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 330.0, "high": 330.0},
                    "intensity_years": [2025],
                    "score_g": {"low": 0.215, "high": 0.258},
                    "band": [3, 3],
                },
            ),
        ],
        models=[make_model(name="m-70b")],
    )
    assert build_data(corpus, date(2026, 10, 8))["meta"]["intensity_spread"] == 11  # 330 / 30


def test_there_is_no_intensity_spread_when_no_route_is_scored():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "D", "mean": 0.0, "spread": {"D": 1}, "summary": "D (1 route at D)"},
            )
        ],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=[], evidence=[make_evidence(kind="corroborating")]),
                disclosure_rating={"letter": "D", "gap": "Location not disclosed by the provider."},
                carbon_score={
                    "grids": [],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": None,
                    "intensity_years": [],
                    "score_g": None,
                    "band": None,
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    assert build_data(corpus, date(2026, 10, 8))["meta"]["intensity_spread"] is None


def test_the_featured_model_is_the_one_most_routes_serve():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "D", "mean": 0.0, "spread": {"D": 3}, "summary": "D (3 routes at D)"},
            )
        ],
        routes=[
            make_route(
                name=name,
                org="acme",
                model=model,
                location=make_location(candidates=[], evidence=[make_evidence(kind="corroborating")]),
                disclosure_rating={"letter": "D", "gap": "Location not disclosed by the provider."},
                carbon_score={
                    "grids": [],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": None,
                    "intensity_years": [],
                    "score_g": None,
                    "band": None,
                },
            )
            for name, model in (("acme-m-8b", "m-8b"), ("acme-m-70b", "m-70b"), ("acme-m-70b-eu", "m-70b"))
        ],
        models=[make_model(name="m-8b"), make_model(name="m-70b")],
    )
    assert build_data(corpus, date(2026, 10, 8))["meta"]["featured_model"] == "m-70b"


def test_on_a_tie_the_featured_model_is_the_first_by_name():
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "D", "mean": 0.0, "spread": {"D": 2}, "summary": "D (2 routes at D)"},
            )
        ],
        routes=[
            make_route(
                name=name,
                org="acme",
                model=model,
                location=make_location(candidates=[], evidence=[make_evidence(kind="corroborating")]),
                disclosure_rating={"letter": "D", "gap": "Location not disclosed by the provider."},
                carbon_score={
                    "grids": [],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": None,
                    "intensity_years": [],
                    "score_g": None,
                    "band": None,
                },
            )
            for name, model in (("acme-m-8b", "m-8b"), ("acme-m-70b", "m-70b"))
        ],
        models=[make_model(name="m-8b"), make_model(name="m-70b")],
    )
    assert build_data(corpus, date(2026, 10, 8))["meta"]["featured_model"] == "m-70b"  # "m-70b" sorts before "m-8b"
