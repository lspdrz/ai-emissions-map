from datetime import date

from build.validate import (
    check_candidates,
    check_defaults,
    check_grid_intensities,
    check_models,
    check_orgs,
    check_stored_scores,
    check_unused_grids,
    check_zones,
    validate_sources,
)
from tests.builders.broken import changed, without
from tests.builders.corpus import make_corpus, make_raw_corpus
from tests.builders.grid import make_grid
from tests.builders.location import make_location
from tests.builders.model import make_model
from tests.builders.organization import make_organization
from tests.builders.route import make_route


# validate_sources: every folder checked, each error naming its file and field.


def test_a_valid_corpus_has_no_errors():
    corpus = make_corpus(
        organizations=[make_organization(name="acme")],
        grids=[make_grid(name="ch", country="CH", zone="CH"), make_grid(name="de", country="DE", zone="DE")],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"])),
            make_route(
                name="acme-m-70b-de",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["cloud:cloudx:eu-de"]),
            ),
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus, cloud_regions={("cloudx", "eu-de"): ["DE"]}) == []


def test_stray_files_are_reported():
    corpus = make_corpus(stray_files=["routes/acme-m-70b.yml", "routes/old-layout"])
    assert validate_sources(corpus) == [
        "routes/acme-m-70b.yml: only <slug>.yaml files belong in sources/routes/",
        "routes/old-layout: only <slug>.yaml files belong in sources/routes/",
    ]


def test_an_organizations_filename_must_be_a_kebab_case_slug():
    corpus = make_raw_corpus()
    corpus["organizations"] = {"Acme": changed(make_organization(name="acme"), "name", to="Acme")}
    assert validate_sources(corpus) == ["organizations/Acme.yaml: filename must be a lowercase kebab-case slug"]


def test_a_grids_filename_must_be_a_kebab_case_slug():
    corpus = make_raw_corpus()
    corpus["grids"] = {"CH": changed(make_grid(name="ch", country="CH", zone="CH"), "name", to="CH")}
    assert validate_sources(corpus) == ["grids/CH.yaml: filename must be a lowercase kebab-case slug"]


def test_a_routes_filename_must_be_a_kebab_case_slug():
    corpus = make_raw_corpus()
    route = make_route(name="acme-m-70b", org="acme", model="m-70b")
    corpus["routes"] = {"acme_m_70b": changed(route, "name", to="acme_m_70b")}
    assert validate_sources(corpus) == ["routes/acme_m_70b.yaml: filename must be a lowercase kebab-case slug"]


def test_a_models_filename_must_be_a_kebab_case_slug():
    corpus = make_raw_corpus()
    corpus["models"] = {"m-70B": changed(make_model(name="m-70b"), "name", to="m-70B")}
    assert validate_sources(corpus) == ["models/m-70B.yaml: filename must be a lowercase kebab-case slug"]


def test_an_organizations_name_must_match_its_filename():
    corpus = make_raw_corpus()
    corpus["organizations"] = {"acme-one": make_organization(name="acme")}
    assert validate_sources(corpus) == [
        "organizations/acme-one.yaml: name 'acme' does not match the filename stem 'acme-one'"
    ]


def test_a_grids_name_must_match_its_filename():
    corpus = make_raw_corpus()
    corpus["grids"] = {"ch-one": make_grid(name="ch", country="CH", zone="CH")}
    assert validate_sources(corpus) == ["grids/ch-one.yaml: name 'ch' does not match the filename stem 'ch-one'"]


def test_a_routes_name_must_match_its_filename():
    corpus = make_raw_corpus()
    corpus["routes"] = {"acme-m-70b-one": make_route(name="acme-m-70b", org="acme", model="m-70b")}
    assert validate_sources(corpus) == [
        "routes/acme-m-70b-one.yaml: name 'acme-m-70b' does not match the filename stem 'acme-m-70b-one'"
    ]


def test_a_models_name_must_match_its_filename():
    corpus = make_raw_corpus()
    corpus["models"] = {"m-70b-one": make_model(name="m-70b")}
    assert validate_sources(corpus) == [
        "models/m-70b-one.yaml: name 'm-70b' does not match the filename stem 'm-70b-one'"
    ]


def test_a_schema_error_names_the_file_and_the_field():
    corpus = make_raw_corpus(organizations=[changed(make_organization(name="acme"), "type", to="spaceship")])
    assert validate_sources(corpus) == [
        "organizations/acme.yaml: type: Input should be 'model_lab', 'inference_host', 'cloud' or 'public_compute'"
    ]


def test_a_schema_error_names_a_nested_field_with_its_index():
    # An unquoted date in YAML reads as a date, which the schema refuses: dates are quoted strings.
    route = make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=[]))
    corpus = make_raw_corpus(routes=[changed(route, "location", "evidence", 0, "accessed", to=date(2026, 9, 1))])
    assert validate_sources(corpus) == [
        "routes/acme-m-70b.yaml: location.evidence[0].accessed: Input should be a valid string"
    ]


def test_a_schema_error_names_a_grids_field():
    grid = make_grid(name="ch", country="CH", zone="CH")
    corpus = make_raw_corpus(grids=[changed(grid, "country", to="CHE")])
    assert validate_sources(corpus) == ["grids/ch.yaml: country: String should match pattern '^[A-Z]{2}$'"]


def test_model_files_are_checked_against_the_model_schema():
    corpus = make_raw_corpus(models=[changed(make_model(name="m-70b"), "active_b", to=-1)])
    assert validate_sources(corpus) == ["models/m-70b.yaml: active_b: Input should be greater than 0"]


# validate_sources: a broken file is reported once, and the records around it are not blamed for it.


def test_an_organization_failing_its_schema_does_not_orphan_its_routes():
    corpus = make_raw_corpus(
        organizations=[changed(make_organization(name="acme"), "type", to="spaceship")],
        grids=[make_grid(name="ch", country="CH", zone="CH")],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus) == [
        "organizations/acme.yaml: type: Input should be 'model_lab', 'inference_host', 'cloud' or 'public_compute'"
    ]


def test_a_grid_failing_its_schema_is_not_reported_missing():
    de = make_grid(name="de", country="DE", zone="DE")
    alpha_3 = changed(de, "country", to="DEU")
    corpus = make_raw_corpus(
        organizations=[make_organization(name="acme")],
        grids=[alpha_3],
        routes=[
            make_route(
                name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["cloud:cloudx:eu-de"])
            )
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus, cloud_regions={("cloudx", "eu-de"): ["DE"]}) == [
        "grids/de.yaml: country: String should match pattern '^[A-Z]{2}$'"
    ]


def test_a_route_failing_its_schema_is_not_checked_against_other_files():
    route = make_route(name="acme-m-70b", org="ghost", model="m-0b", location=make_location(candidates=["grid:ch"]))
    corpus = make_raw_corpus(routes=[without(route, "location", "candidates")])
    assert validate_sources(corpus) == ["routes/acme-m-70b.yaml: location.candidates: Field required"]


def test_a_route_failing_its_schema_does_not_make_its_grid_unused():
    route = make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
    corpus = make_raw_corpus(
        organizations=[make_organization(name="acme")],
        grids=[make_grid(name="ch", country="CH", zone="CH")],
        routes=[changed(route, "colour", to="red")],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus, cloud_regions={}) == [
        "routes/acme-m-70b.yaml: colour: Extra inputs are not permitted"
    ]


def test_an_unused_grid_is_reported_with_cloud_region_data():
    corpus = make_corpus(grids=[make_grid(name="ch", country="CH", zone="CH")])
    assert validate_sources(corpus, cloud_regions={}) == ["grids/ch.yaml: no route uses this grid; remove it"]


def test_an_unused_grid_is_not_reported_without_cloud_region_data():
    corpus = make_corpus(grids=[make_grid(name="ch", country="CH", zone="CH")])
    assert validate_sources(corpus) == []


# validate_sources runs every cross-file check: one test per check, each corpus breaking that check's rule alone.


def test_validate_sources_checks_the_organization_a_route_names():
    corpus = make_corpus(
        grids=[make_grid(name="ch", country="CH", zone="CH")],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus) == ["routes/acme-m-70b.yaml: organization 'acme' has no organizations/acme.yaml"]


def test_validate_sources_checks_the_model_a_route_names():
    corpus = make_corpus(
        organizations=[make_organization(name="acme")],
        grids=[make_grid(name="ch", country="CH", zone="CH")],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
        ],
    )
    assert validate_sources(corpus) == [
        "routes/acme-m-70b.yaml: model 'm-70b' has no sources/models/m-70b.yaml; add one (docs/workflows/add-model.md)"
    ]


def test_validate_sources_checks_zones():
    corpus = make_corpus(
        grids=[make_grid(name="ch", country="CH", zone="CH"), make_grid(name="ch-2", country="CH", zone="CH")]
    )
    assert validate_sources(corpus) == ["grids/ch-2.yaml: zone 'CH' is also claimed by grids/ch.yaml"]


def test_validate_sources_checks_every_grid_has_its_intensity():
    corpus = make_corpus(grids=[make_grid(name="ch", country="CH", zone="CH", intensity=None)])
    assert validate_sources(corpus) == [
        "grids/ch.yaml: has no intensity; run `python -m build grid-emissions --write ch`"
    ]


def test_validate_sources_checks_candidates():
    corpus = make_corpus(
        organizations=[make_organization(name="acme")],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus) == ["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"]


def test_validate_sources_checks_defaults():
    corpus = make_corpus(
        organizations=[make_organization(name="acme")],
        grids=[make_grid(name="ch", country="CH", zone="CH")],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                default=True,
            ),
            make_route(
                name="acme-m-70b-eu",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                default=True,
            ),
        ],
        models=[make_model(name="m-70b")],
    )
    assert validate_sources(corpus) == [
        "organizations/acme.yaml: routes acme-m-70b and acme-m-70b-eu are both marked default for model 'm-70b'"
    ]


# The organizations and models routes name.


def test_a_route_must_name_an_existing_organization():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", org="ghost")}
    assert check_orgs({}, routes) == ["routes/acme-m-70b.yaml: organization 'ghost' has no organizations/ghost.yaml"]


def test_a_routes_name_must_start_with_its_organizations_slug():
    routes = {"other-m-8b": make_route(name="other-m-8b", org="acme")}
    assert check_orgs({"acme": make_organization(name="acme")}, routes) == [
        "routes/other-m-8b.yaml: name must start with 'acme-', its organization's slug"
    ]


def test_a_route_must_name_an_existing_model():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", model="m-70b")}
    assert check_models(routes, {}) == [
        "routes/acme-m-70b.yaml: model 'm-70b' has no sources/models/m-70b.yaml; add one (docs/workflows/add-model.md)"
    ]


# Grids: one file per zone, each valued by EcoLogits' mix for its country.


def test_two_grids_may_not_claim_one_zone():
    grids = {"ch": make_grid(name="ch", zone="CH"), "ch-2": make_grid(name="ch-2", zone="CH")}
    assert check_zones(grids) == ["grids/ch-2.yaml: zone 'CH' is also claimed by grids/ch.yaml"]


def test_grids_without_a_zone_claim_none():
    grids = {"acme-1": make_grid(name="acme-1", zone=None, supply="onsite"), "ch": make_grid(name="ch", zone="CH")}
    assert check_zones(grids) == []


def test_a_grid_with_its_intensity_passes():
    assert check_grid_intensities({"ch": make_grid(name="ch")}) == []


def test_each_grid_without_its_intensity_is_named_with_the_command_to_run():
    grids = {
        "ch": make_grid(name="ch", intensity=None),
        "de": make_grid(name="de", country="DE", zone="DE", intensity=None),
    }
    assert check_grid_intensities(grids) == [
        "grids/ch.yaml: has no intensity; run `python -m build grid-emissions --write ch`",
        "grids/de.yaml: has no intensity; run `python -m build grid-emissions --write de`",
    ]


def test_a_grid_no_route_uses_is_reported():
    grids = {"ch": make_grid(name="ch", zone="CH"), "de": make_grid(name="de", country="DE", zone="DE")}
    assert check_unused_grids(grids, used={"ch"}) == ["grids/de.yaml: no route uses this grid; remove it"]


# Candidates: each resolves to grid files that exist; the grids it resolves to count as used.


def test_a_grid_candidate_resolves_to_its_file():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["grid:ch"]))}
    assert check_candidates(routes, {"ch": make_grid(name="ch", zone="CH")}, None) == ([], {"ch"})


def test_a_grid_candidate_needs_its_file():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["grid:ch"]))}
    assert check_candidates(routes, {}, None) == (["routes/acme-m-70b.yaml: grid 'ch' has no grids/ch.yaml"], set())


def test_a_cloud_candidate_resolves_to_the_grid_files_of_its_zones():
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["cloud:azure:northeurope"]))
    }
    grids = {"fi": make_grid(name="fi", country="FI", zone="FI"), "ie": make_grid(name="ie", country="IE", zone="IE")}
    assert check_candidates(routes, grids, {("azure", "northeurope"): ["FI", "IE"]}) == ([], {"fi", "ie"})


def test_a_cloud_candidate_needs_its_region_in_the_cloud_region_data():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["cloud:cloudx:eu-fr"]))}
    assert check_candidates(routes, {}, {("cloudx", "eu-de"): ["DE"]}) == (
        ["routes/acme-m-70b.yaml: cloud region cloudx:eu-fr is not in the cloud-region data"],
        set(),
    )


def test_a_cloud_candidates_zone_needs_a_grid_file():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["cloud:cloudx:eu-de"]))}
    assert check_candidates(routes, {}, {("cloudx", "eu-de"): ["DE"]}) == (
        [
            "routes/acme-m-70b.yaml: cloud region cloudx:eu-de maps to zone 'DE', which has no grid file; "
            "add one (docs/workflows/add-grid.md)"
        ],
        set(),
    )


def test_cloud_candidates_are_not_checked_without_cloud_region_data():
    routes = {"acme-m-70b": make_route(name="acme-m-70b", location=make_location(candidates=["cloud:cloudx:eu-de"]))}
    assert check_candidates(routes, {}, None) == ([], set())


# Defaults: at most one route per organization and model is marked default.


def test_two_default_routes_for_one_model_are_refused():
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", org="acme", model="m-70b", default=True),
        "acme-m-70b-eu": make_route(name="acme-m-70b-eu", org="acme", model="m-70b", default=True),
    }
    assert check_defaults(routes) == [
        "organizations/acme.yaml: routes acme-m-70b and acme-m-70b-eu are both marked default for model 'm-70b'"
    ]


def test_two_organizations_may_each_mark_a_default_route_for_one_model():
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", org="acme", model="m-70b", default=True),
        "other-m-70b": make_route(name="other-m-70b", org="other", model="m-70b", default=True),
    }
    assert check_defaults(routes) == []


def test_one_default_route_per_model_is_allowed():
    routes = {
        "acme-m-70b": make_route(name="acme-m-70b", org="acme", model="m-70b", default=True),
        "acme-m-8b": make_route(name="acme-m-8b", org="acme", model="m-8b", default=True),
    }
    assert check_defaults(routes) == []


# The fields score writes: a route's disclosure_rating: and carbon_intensity:, an organization's disclosure_rating:.


def test_stored_fields_that_are_present_pass():
    grid: dict = {**make_grid(name="ch"), "intensity": {}}
    org: dict = {**make_organization(name="acme"), "disclosure_rating": {}}
    route: dict = {**make_route(name="acme-m-70b"), "disclosure_rating": {}, "carbon_intensity": {}}
    data = {"grids": {"ch": grid}, "organizations": {"acme": org}, "routes": {"acme-m-70b": route}}
    assert check_stored_scores(data) == []


def test_missing_stored_fields_are_named():
    data = {
        "organizations": {"acme": make_organization(name="acme")},
        "routes": {"acme-m-70b": make_route(name="acme-m-70b")},
    }
    assert check_stored_scores(data) == [
        "organizations/acme.yaml: is missing the disclosure_rating field; run `python -m build score`",
        "routes/acme-m-70b.yaml: is missing the disclosure_rating field; run `python -m build score`",
        "routes/acme-m-70b.yaml: is missing the carbon_intensity field; run `python -m build score`",
    ]
