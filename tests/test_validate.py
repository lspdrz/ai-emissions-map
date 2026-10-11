import copy
import shutil
from datetime import date

from build.evidence import location_established, verified
from build.validate import ROOT, load_sources, route_owners, validate_sources, validation_warnings

SHA = "0" * 64


def _evidence(kind="primary"):
    return {"url": "https://example.com/x", "shows": "y", "accessed": "2026-09-01", "http_status": 200,
            "content_sha256": SHA, "kind": kind}


def _fixture():
    """One organization serving one route from one facility, the smallest corpus that validates."""
    return {
        "organizations": {"acme": {"name": "acme", "display_name": "Acme", "type": "inference_host",
                                   "homepage": "https://acme.example", "ids": {}, "routes": ["acme-m-70b"]}},
        "facilities": {"acme-1": {"name": "acme-1", "display_name": "Acme 1", "operator": "acme",
                                  "ownership": "owned", "grid_zone": "CH", "last_verified": "2026-09-20",
                                  "location_evidence": [_evidence()]}},
        "routes": {"acme-m-70b": {"name": "acme-m-70b", "model": "m-70b",
                                  "location": {"confidence": "facility", "candidates": ["facility:acme-1"],
                                               "last_verified": "2026-09-20", "evidence": [_evidence()]}}},
        "models": {"m-70b": {"name": "m-70b", "architecture": "dense", "active_b": 70, "total_b": 70,
                             "evidence": [_evidence()]}},
        "stray_files": [],
    }


def _with_route(d, name, org="acme"):
    d["routes"][name] = copy.deepcopy(d["routes"]["acme-m-70b"]) | {"name": name}
    d["organizations"][org]["routes"].append(name)
    return d


def _org(d, name):
    d["organizations"][name] = copy.deepcopy(d["organizations"]["acme"]) | {"name": name, "routes": []}
    return d


def test_valid_fixture_passes():
    assert validate_sources(_fixture()) == []


def test_fixture_corpus_on_disk_is_valid(sources):
    assert validate_sources(sources) == []
    assert set(sources["organizations"]) == {"alpinehost", "multihost", "vaguehost", "aggregator"}
    assert set(sources["facilities"]) == {"alp-1"}
    assert set(sources["routes"]) == {"alpinehost-test-70b", "alpinehost-test-8b", "multihost-test-70b",
                                      "vaguehost-test-70b", "aggregator-test-70b"}
    assert set(sources["models"]) == {"test-70b", "test-8b"}


def test_dates_stay_strings(sources):
    # Quoted in YAML so the schema's string type holds; code converts with date.fromisoformat where it compares.
    assert sources["routes"]["alpinehost-test-70b"]["location"]["last_verified"] == "2026-09-20"


def test_route_owners_come_from_rosters(sources):
    owners = route_owners(sources["organizations"])
    assert owners["multihost-test-70b"] == "multihost"
    assert owners["aggregator-test-70b"] == "aggregator"


def test_schema_violation_names_the_file():
    d = _fixture()
    d["organizations"]["acme"]["type"] = "spaceship"
    errs = validate_sources(d)
    assert any(e.startswith("organizations/acme.yaml: type:") for e in errs)


def test_unquoted_date_fails_the_schema():
    from datetime import date
    d = _fixture()
    d["routes"]["acme-m-70b"]["location"]["last_verified"] = date(2026, 9, 20)
    assert any("routes/acme-m-70b.yaml: location.last_verified:" in e for e in validate_sources(d))


def test_evidence_must_quote_what_the_page_shows():
    d = _fixture()
    del d["routes"]["acme-m-70b"]["location"]["evidence"][0]["shows"]
    assert any("routes/acme-m-70b.yaml" in e and "'shows' is a required property" in e for e in validate_sources(d))


# Identity: the filename stem is the slug.

def test_name_must_match_filename():
    d = _fixture()
    d["facilities"]["acme-one"] = d["facilities"].pop("acme-1")
    errs = validate_sources(d)
    assert any("facilities/acme-one.yaml" in e and "does not match the filename stem" in e for e in errs)


def test_filename_must_be_kebab_case():
    d = _fixture()
    d["facilities"]["Acme-1"] = d["facilities"].pop("acme-1") | {"name": "Acme-1"}
    assert any(e.startswith("facilities/Acme-1.yaml:") and "kebab-case" in e for e in validate_sources(d))


def test_stray_files_are_reported(tmp_path, fixtures_dir):
    root = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", root)
    routes = root / "sources" / "routes"
    (routes / "multihost-test-70b.yaml").rename(routes / "multihost-test-70b.yml")
    (routes / "old-layout").mkdir()
    (routes / ".DS_Store").write_text("")
    data = load_sources(root)
    assert data["stray_files"] == ["routes/multihost-test-70b.yml", "routes/old-layout"]
    errs = validate_sources(data)
    assert any("routes/multihost-test-70b.yml" in e for e in errs)
    assert any("routes/old-layout" in e for e in errs)


# Rosters: every route is on exactly one organization's roster, and its slug starts with that org.

def test_route_missing_from_every_roster():
    d = _fixture()
    d["organizations"]["acme"]["routes"] = []
    assert any("routes/acme-m-70b.yaml" in e and "no organization" in e for e in validate_sources(d))


def test_route_on_two_rosters():
    d = _org(_fixture(), "other")
    d["organizations"]["other"]["routes"] = ["acme-m-70b"]
    assert any("acme-m-70b" in e and "'acme'" in e and "'other'" in e for e in validate_sources(d))


def test_roster_entry_without_a_route_file():
    d = _fixture()
    d["organizations"]["acme"]["routes"].append("acme-ghost")
    assert any("organizations/acme.yaml" in e and "acme-ghost" in e for e in validate_sources(d))


def test_route_name_must_start_with_its_org():
    d = _with_route(_fixture(), "other-m-8b")
    assert any("routes/other-m-8b.yaml" in e and "'acme-'" in e for e in validate_sources(d))


# Aliases: a slug leaves the corpus only by appearing as an alias on the record that replaced it.

def test_alias_may_not_shadow_a_live_slug():
    d = _org(_fixture(), "other")
    d["organizations"]["other"]["aliases"] = ["acme"]
    assert any("organizations/other.yaml" in e and "'acme'" in e for e in validate_sources(d))


def test_two_records_may_not_claim_one_alias():
    d = _org(_fixture(), "other")
    d["organizations"]["acme"]["aliases"] = ["old-host"]
    d["organizations"]["other"]["aliases"] = ["old-host"]
    assert any("old-host" in e and "acme" in e and "other" in e for e in validate_sources(d))


def test_model_files_are_schema_checked():
    d = _fixture()
    d["models"]["m-70b"]["active_b"] = -1
    del d["models"]["m-70b"]["evidence"][0]["shows"]
    errs = validate_sources(d)
    assert any(e.startswith("models/m-70b.yaml: active_b:") for e in errs)
    assert any(e.startswith("models/m-70b.yaml: evidence[0]:") and "'shows'" in e for e in errs)


def test_model_needs_evidence():
    d = _fixture()
    d["models"]["m-70b"]["evidence"] = []
    assert any(e.startswith("models/m-70b.yaml: evidence:") for e in validate_sources(d))


def test_model_name_must_match_filename():
    d = _fixture()
    d["models"]["m-71b"] = d["models"].pop("m-70b")
    assert any("models/m-71b.yaml" in e and "does not match the filename stem" in e for e in validate_sources(d))


def test_upstream_weight_must_be_positive():
    d = _with_route(_fixture(), "acme-agg")
    agg = d["routes"]["acme-agg"]
    del agg["location"]
    agg["upstreams"] = [{"route": "acme-m-70b", "weight": 0}]
    assert any(e.startswith("routes/acme-agg.yaml: upstreams[0].weight:") for e in validate_sources(d))


# Cross-file checks (Task 3).

ZONES = {"CH", "DE", "FR"}
CLOUD = {("cloudx", "eu-de"): ["DE"], ("cloudx", "eu-fr"): ["FR"]}
MODELS = {"test-70b", "test-8b"}


def test_fixture_corpus_passes_every_check(sources):
    assert validate_sources(sources, model_ids=MODELS, grid_zones=ZONES, cloud_regions=CLOUD) == []
    assert validation_warnings(sources, date(2026, 10, 8)) == []


def test_verified_needs_primary_and_recent(sources):
    loc = sources["routes"]["alpinehost-test-70b"]["location"]
    assert verified(loc, date(2026, 10, 8))
    assert verified(loc, date(2026, 12, 19))       # exactly 90 days after location.last_verified 2026-09-20
    assert not verified(loc, date(2026, 12, 20))
    press = sources["routes"]["vaguehost-test-70b"]["location"]   # corroborating evidence only
    assert not verified(press, date(2026, 10, 8))


def test_location_established(sources):
    assert location_established(sources["routes"]["alpinehost-test-70b"]["location"], date(2026, 10, 8))
    assert not location_established(sources["routes"]["vaguehost-test-70b"]["location"], date(2026, 10, 8))


def test_unknown_zone_reported(sources):
    errs = validate_sources(sources, grid_zones={"DE", "FR"})
    assert "facilities/alp-1.yaml: grid zone 'CH' is not in the grid data" in errs
    assert "routes/alpinehost-test-8b.yaml: grid zone 'CH' is not in the grid data" in errs


def test_unknown_cloud_region_reported(sources):
    errs = validate_sources(sources, cloud_regions={("cloudx", "eu-de"): ["DE"]})
    assert errs == ["routes/multihost-test-70b.yaml: cloud region cloudx:eu-fr is not in the cloud-region data"]


def test_unknown_facility_and_upstream_reported():
    d = _with_route(_fixture(), "acme-agg")
    d["routes"]["acme-m-70b"]["location"]["candidates"] = ["facility:nowhere"]
    agg = d["routes"]["acme-agg"]
    del agg["location"]
    agg["upstreams"] = [{"route": "acme-ghost", "weight": 1}]
    agg["upstream_evidence"] = [_evidence()]
    errs = validate_sources(d)
    assert "routes/acme-m-70b.yaml: facility 'nowhere' has no facilities/nowhere.yaml" in errs
    assert "routes/acme-agg.yaml: upstream route 'acme-ghost' has no routes/acme-ghost.yaml" in errs


def test_upstream_cycle_reported(sources):
    d = copy.deepcopy(sources)
    alp = d["routes"]["alpinehost-test-70b"]
    del alp["location"]
    alp["upstreams"] = [{"route": "aggregator-test-70b", "weight": 1}]
    alp["upstream_evidence"] = d["routes"]["aggregator-test-70b"]["upstream_evidence"]
    assert any("upstream cycle" in e and "aggregator-test-70b -> alpinehost-test-70b" in e
               for e in validate_sources(d))


def test_location_needs_primary_evidence():
    d = _fixture()
    d["routes"]["acme-m-70b"]["location"]["evidence"][0]["kind"] = "corroborating"
    assert validate_sources(d) == ["routes/acme-m-70b.yaml: confidence 'facility' needs at least one primary source"]


def test_location_needs_candidates():
    d = _fixture()
    d["routes"]["acme-m-70b"]["location"]["candidates"] = []
    assert validate_sources(d) == ["routes/acme-m-70b.yaml: confidence 'facility' needs at least one candidate"]


def test_upstreams_need_primary_evidence():
    d = _with_route(_fixture(), "acme-agg")
    agg = d["routes"]["acme-agg"]
    del agg["location"]
    agg["upstreams"] = [{"route": "acme-m-70b", "weight": 1}]
    assert validate_sources(d) == ["routes/acme-agg.yaml: upstream weights need a primary source"]


def test_facility_needs_primary_evidence():
    d = _fixture()
    d["facilities"]["acme-1"]["location_evidence"][0]["kind"] = "corroborating"
    assert validate_sources(d) == ["facilities/acme-1.yaml: facility location needs a primary source"]


def test_route_shape():
    d = _fixture()
    del d["routes"]["acme-m-70b"]["location"]
    assert validate_sources(d) == ["routes/acme-m-70b.yaml: route needs either a location or upstreams"]
    d = _with_route(_fixture(), "acme-agg")
    d["routes"]["acme-agg"]["upstreams"] = [{"route": "acme-m-70b", "weight": 1}]
    d["routes"]["acme-agg"]["upstream_evidence"] = [_evidence()]
    assert validate_sources(d) == ["routes/acme-agg.yaml: route cannot have both a location and upstreams"]


def test_unknown_model_and_label_without_evidence():
    d = _fixture()
    d["routes"]["acme-m-70b"]["served_as"] = "m-70b-v1.5"
    errs = validate_sources(d, model_ids={"something-else"})
    assert "routes/acme-m-70b.yaml: model 'm-70b' is not in EcoLogits or sources/models/" in errs
    assert any("served_as 'm-70b-v1.5' differs" in e for e in errs)


def test_gap_map_id_is_not_a_field():
    # Our organizations are serving providers, not the Gap Map's model makers; the link was dropped (2026-10-11).
    d = _fixture()
    d["organizations"]["acme"]["ids"]["gap_map"] = "acme-ai"
    assert any(e.startswith("organizations/acme.yaml: ids:") and "gap_map" in e for e in validate_sources(d))


def test_malformed_record_is_reported_once():
    d = _fixture()
    del d["routes"]["acme-m-70b"]["location"]["candidates"]
    assert validate_sources(d) == ["routes/acme-m-70b.yaml: location: 'candidates' is a required property"]


def test_stale_location_is_a_warning(sources):
    warns = validation_warnings(sources, date(2027, 6, 1))
    assert any(w.startswith("routes/alpinehost-test-70b.yaml: no primary location evidence verified") for w in warns)


def test_org_without_routes_is_a_warning():
    d = _org(_fixture(), "idle")
    assert validation_warnings(d) == ["organizations/idle.yaml: has no routes and will not be rated"]


# Fixes from the final review.

def test_cloud_region_whose_zone_is_not_in_the_grid():
    # The validator must catch what would otherwise crash compute_routes after "0 errors".
    errs = validate_sources(_cloud_fixture(), grid_zones={"CH", "DE"}, cloud_regions={("cloudx", "eu-pl"): ["DE", "PL"]})
    assert errs == ["routes/acme-m-70b.yaml: cloud region cloudx:eu-pl maps to grid zone 'PL', "
                    "which is not in the grid data"]


def _cloud_fixture():
    d = _fixture()
    loc = d["routes"]["acme-m-70b"]["location"]
    loc["confidence"], loc["candidates"] = "region", ["cloud:cloudx:eu-pl"]
    return d


def test_aggregator_upstream_must_serve_the_same_model():
    d = _with_route(_fixture(), "acme-agg")
    d["routes"]["acme-m-8b"] = copy.deepcopy(d["routes"]["acme-m-70b"]) | {"name": "acme-m-8b", "model": "m-8b"}
    d["organizations"]["acme"]["routes"].append("acme-m-8b")
    agg = d["routes"]["acme-agg"]
    del agg["location"]
    agg["upstreams"] = [{"route": "acme-m-8b", "weight": 1}]
    agg["upstream_evidence"] = [_evidence()]
    assert validate_sources(d) == [
        "routes/acme-agg.yaml: upstream route 'acme-m-8b' serves model 'm-8b', not 'm-70b'"]


def test_facility_confidence_needs_facility_candidates():
    d = _fixture()
    d["routes"]["acme-m-70b"]["location"]["candidates"] = ["zone:CH"]
    assert validate_sources(d) == [
        "routes/acme-m-70b.yaml: confidence 'facility' needs every candidate to be a facility: candidate"]


def test_region_confidence_cannot_rest_on_a_bare_zone():
    d = _fixture()
    loc = d["routes"]["acme-m-70b"]["location"]
    loc["confidence"], loc["candidates"] = "region", ["zone:CH"]
    assert validate_sources(d) == [
        "routes/acme-m-70b.yaml: confidence 'region' needs every candidate to be a facility: or cloud: candidate"]
    loc["candidates"] = ["facility:acme-1"]
    assert validate_sources(d) == []


def test_future_last_verified_does_not_count(sources):
    loc = copy.deepcopy(sources["routes"]["alpinehost-test-70b"]["location"])
    loc["last_verified"] = "2062-09-20"   # a typo, after the release
    assert not verified(loc, date(2026, 10, 8))


def test_cli_reports_a_broken_model_file_instead_of_crashing(tmp_path, fixtures_dir, capsys):
    from build.validate import main
    root = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", root)
    shutil.copytree(ROOT / "docs", root / "docs")
    model = root / "sources" / "models" / "test-8b.yaml"
    model.write_text(model.read_text().replace("total_b: 8\n", ""))
    assert main(["--root", str(root)]) == 1
    assert "ERROR: models/test-8b.yaml: 'total_b' is a required property" in capsys.readouterr().out


def test_browser_capture_is_accepted():
    d = _fixture()
    d["routes"]["acme-m-70b"]["location"]["evidence"][0]["capture"] = "browser"
    assert validate_sources(d) == []
    d["routes"]["acme-m-70b"]["location"]["evidence"][0]["capture"] = "screenshot"
    assert any("capture" in e for e in validate_sources(d))


def test_unwritten_shows_placeholder_is_an_error():
    # build.fetch_source leaves this placeholder for the curator; it must never reach main.
    d = _fixture()
    d["facilities"]["acme-1"]["location_evidence"][0]["shows"] = "TODO: quote what the page says, in double quotes"
    assert validate_sources(d) == [
        "facilities/acme-1.yaml: location_evidence[0].shows is still the fetch_source placeholder"]
