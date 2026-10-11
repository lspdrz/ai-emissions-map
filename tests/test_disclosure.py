import copy
import json
from datetime import date

import pytest

from build.disclosure import check_disclosure, compare_with_routes, model_levels

TODAY = date(2026, 10, 8)


@pytest.fixture
def doc(fixtures_dir):
    return json.loads((fixtures_dir / "disclosures" / "example.json").read_text())


def _routing(doc, model):
    return next(m for s in doc["services"] for m in s["models"] if m["model"] == model)["default_routing"]


def test_example_is_valid(doc):
    assert check_disclosure(doc, TODAY) == []


def test_named_facilities_are_level_facility(doc):
    assert model_levels(doc, TODAY)["test-70b"] == {"level": "facility", "zones": ["CH"], "served_as": None}


def test_least_precise_entry_decides(doc):
    # One entry names a region, the other only a country -> country; and DE plus FR -> several countries.
    assert model_levels(doc, TODAY)["test-8b"]["level"] == "country_set"
    _routing(doc, "test-8b")[1]["country"] = "DE"
    assert model_levels(doc, TODAY)["test-8b"]["level"] == "country"
    _routing(doc, "test-8b")[1]["region"] = "eu-de-2"
    assert model_levels(doc, TODAY)["test-8b"]["level"] == "region"


def test_entry_with_no_location_is_unknown(doc):
    _routing(doc, "test-8b").append({"share_of_traffic": 0.1})
    assert model_levels(doc, TODAY)["test-8b"]["level"] == "unknown"


def test_facility_needs_operator_and_city(doc):
    del _routing(doc, "test-70b")[0]["operator"]
    assert model_levels(doc, TODAY)["test-70b"]["level"] == "country"   # falls back to what the entry still names


def test_expired_file_rates_nothing(doc):
    assert check_disclosure(doc, date(2027, 4, 1)) == ["valid_until 2027-03-31 has passed"]
    assert model_levels(doc, date(2027, 4, 1)) == {}


def test_schema_errors_name_the_field(doc):
    bad = copy.deepcopy(doc)
    del bad["contact"]
    _routing(bad, "test-70b")[0]["country"] = "Switzerland"
    assert check_disclosure(bad, TODAY) == [
        "(root): 'contact' is a required property",
        "services[0].models[0].default_routing[0].country: 'Switzerland' does not match '^[A-Z]{2}$'",
    ]


def test_consistency_errors(doc):
    bad = copy.deepcopy(doc)
    bad["valid_until"] = "2026-09-01"
    _routing(bad, "test-70b")[0]["share_of_traffic"] = 0.9
    assert check_disclosure(bad, TODAY) == [
        "valid_until 2026-09-01 is before published 2026-10-01",
        "services[0].models[0] (test-70b): share_of_traffic adds up to 1.1",
    ]


def test_compare_with_curated_routes(doc, sources):
    rows = compare_with_routes(doc, TODAY, "multihost", sources)
    assert rows == [{"route": "multihost-test-70b", "model": "test-70b", "curated": "country_set",
                     "disclosed": "facility", "disclosed_zones": ["CH"]}]


def test_route_missing_from_the_file_is_unknown(doc, sources):
    rows = compare_with_routes(doc, TODAY, "alpinehost", sources)
    by_route = {r["route"]: r for r in rows}
    assert by_route["alpinehost-test-8b"]["disclosed"] == "country_set"     # matched on model test-8b
    doc["services"][0]["models"] = doc["services"][0]["models"][:1]
    rows = compare_with_routes(doc, TODAY, "alpinehost", sources)
    assert {r["route"]: r["disclosed"] for r in rows}["alpinehost-test-8b"] == "unknown"


def test_cli_reports_a_file_that_is_not_json(tmp_path, capsys):
    from build.disclosure import main
    page = tmp_path / "error-page.html"
    page.write_text("<html><body>404 Not Found</body></html>")
    assert main([str(page)]) == 1
    assert capsys.readouterr().out.startswith(f"ERROR: {page}: not a JSON document")


def test_unknown_organization_is_named(doc, sources):
    from build.disclosure import DisclosureError
    with pytest.raises(DisclosureError, match="no organization 'nobody'"):
        compare_with_routes(doc, TODAY, "nobody", sources)
