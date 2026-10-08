import copy
import shutil

from build.validate import load_sources, route_owners, validate_sources

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
