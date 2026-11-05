import json

import pytest

from tools.estimate_emissions import estimate, published_data
from tests.builders.data import make_data, make_data_meta, make_data_model, make_data_organization, make_data_route

# Each test builds the whole release it reads, every field stated, and sets it by replacing published_data.


# Estimating a response: every route of its model, scaled to its output tokens.


def test_estimate_scales_every_range_to_the_tokens(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 50.0, "high": 50.0},
                sci={"low": 0.08, "high": 0.09},
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    result = estimate("M 70B", 500)
    assert result["output_tokens"] == 500
    [route] = result["routes"]
    assert route["energy_wh"] == {"low": 0.3, "high": 0.4}
    assert route["embodied_g"] == {"low": 0.025, "high": 0.025}
    assert route["co2e_g"] == {"low": 0.04, "high": 0.045}


def test_estimate_scales_by_the_functional_unit_the_release_states(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=500,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.068, "high": 0.074},
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    # 250 tokens of a release per 500: half each figure. A built-in 1,000 would give a quarter; no scaling, all of it.
    [route] = estimate("M 70B", 250)["routes"]
    assert route["energy_wh"] == {"low": 0.3, "high": 0.4}
    assert route["embodied_g"] == {"low": 0.025, "high": 0.025}
    assert route["co2e_g"] == {"low": 0.034, "high": 0.037}


def test_estimate_lists_every_route_of_the_model_and_no_other(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[
            make_data_model(slug="m-70b", display_name="M 70B"),
            make_data_model(slug="n-flash", display_name="N Flash"),
        ],
        organizations=[
            make_data_organization(slug="acme", display_name="Acme"),
            make_data_organization(slug="globex", display_name="Globex"),
        ],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.068, "high": 0.074},
            ),
            make_data_route(
                slug="acme-m-70b-us",
                org="acme",
                model="m-70b",
                label="United States",
                default=False,
                letter="C",
                gap="The grid is not determined: several are possible.",
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 380.0, "high": 380.0},
                sci={"low": 0.278, "high": 0.354},
            ),
            make_data_route(
                slug="globex-m-70b",
                org="globex",
                model="m-70b",
                label="Globex 1, Oslo",
                default=True,
                letter="B",
                gap="The facility is not named.",
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.068, "high": 0.074},
            ),
            make_data_route(
                slug="acme-n-flash",
                org="acme",
                model="n-flash",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as=None,
                energy={"low": 0.2, "high": 0.3},
                embodied={"low": 0.01, "high": 0.01},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.016, "high": 0.019},
            ),
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    routes = estimate("M 70B", 1000)["routes"]
    assert {route["route"]: (route["organization"], route["where"], route["rating"]) for route in routes} == {
        "acme-m-70b": ("Acme", "Acme 1, Geneva", "A"),
        "acme-m-70b-us": ("Acme", "United States", "C"),
        "globex-m-70b": ("Globex", "Globex 1, Oslo", "B"),
    }


def test_estimate_lists_routes_by_the_midpoint_of_their_carbon_and_those_without_a_grid_last(monkeypatch):
    # By midpoint: narrow (0.6), wide (0.8), upper (0.825). Sorting by the low end would put wide first, and by the high
    # end upper before wide; only the midpoint gives this order. The release lists them the other way round.
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="no-grid",
                org="acme",
                model="m-70b",
                label="Not disclosed",
                default=True,
                letter="D",
                gap="Location not disclosed by the provider.",
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity=None,
                sci=None,
            ),
            make_data_route(
                slug="upper",
                org="acme",
                model="m-70b",
                label="Upper",
                default=False,
                letter="C",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 750.0, "high": 1200.0},
                sci={"low": 0.65, "high": 1.0},
            ),
            make_data_route(
                slug="wide",
                org="acme",
                model="m-70b",
                label="Wide",
                default=False,
                letter="C",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 80.0, "high": 1800.0},
                sci={"low": 0.1, "high": 1.5},
            ),
            make_data_route(
                slug="narrow",
                org="acme",
                model="m-70b",
                label="Narrow",
                default=False,
                letter="C",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 750.0, "high": 810.0},
                sci={"low": 0.5, "high": 0.7},
            ),
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    assert [route["route"] for route in estimate("M 70B", 1000)["routes"]] == ["narrow", "wide", "upper", "no-grid"]


def test_a_route_without_a_grid_gives_energy_and_no_grams(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Not disclosed",
                default=True,
                letter="D",
                gap="Location not disclosed by the provider.",
                served_as=None,
                energy={"low": 3.0, "high": 8.0},
                embodied={"low": 0.09, "high": 0.09},
                grid_intensity=None,
                sci=None,
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    [route] = estimate("M 70B", 500)["routes"]
    assert route["co2e_g"] is None
    assert route["embodied_g"] is None
    assert route["energy_wh"] == {"low": 1.5, "high": 4.0}
    assert route["gap"] == "Location not disclosed by the provider."


def test_estimate_says_which_release_it_is_from(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    result = estimate("M 70B", 1000)
    assert set(result) == {"model", "output_tokens", "routes", "release"}
    assert result["model"] == "M 70B"
    assert result["release"] == {
        "release_date": "2026-10-28",
        "methodology_version": "0.4.0",
        "ecologits_version": "0.11.2",
        "draft": True,
    }


def test_output_tokens_below_one_is_an_error(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    with pytest.raises(ValueError, match="output_tokens"):
        estimate("M 70B", 0)


# Matching the model's name as people type it.


@pytest.mark.parametrize("name", ["m 70b", "M-70B", "M.70B", "m-70b"])
def test_model_names_match_in_any_case_and_punctuation(monkeypatch, name):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    assert estimate(name, 1000)["model"] == "M 70B"


def test_a_served_as_name_matches_in_another_case(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as="acme/m-70b-instruct",
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.068, "high": 0.074},
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    assert estimate("Acme/M-70B-Instruct", 1000)["model"] == "M 70B"


def test_a_name_that_prefixes_another_matches_only_itself(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[
            make_data_model(slug="n-flash", display_name="N Flash"),
            make_data_model(slug="n-flash-1017", display_name="N Flash 1017"),
        ],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    assert estimate("N-Flash", 1000)["model"] == "N Flash"


def test_an_unknown_model_names_the_models_on_the_map(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    with pytest.raises(LookupError, match="No model on the map matches 'X 9'. Models: M 70B."):
        estimate("X 9", 1000)


def test_an_empty_map_says_so(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)
    with pytest.raises(LookupError, match="There are no models on the map yet."):
        estimate("M 70B", 1000)


# Reading the release: data/data.json, once, whatever its schema version.


def test_published_data_reads_data_json_once(monkeypatch, tmp_path):
    first = make_data(
        schema="aem-data/99",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[],
        routes=[],
    )
    path = tmp_path / "data.json"
    path.write_text(json.dumps(first))
    monkeypatch.setattr("tools.estimate_emissions.DATA_FILE", path)
    published_data.cache_clear()
    try:
        assert published_data() == first
        path.write_text(json.dumps(first | {"models": []}))
        assert published_data() == first
    finally:
        published_data.cache_clear()
