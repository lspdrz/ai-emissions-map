import json
from unittest.mock import Mock

from build.check_site_data import check_site_data

# Each test writes its own web/data/data.json into tmp_path and replaces inputs_sha with a fake returning "abc": the
# hash of what the data file would be built from now.


def test_current_site_data_within_its_contract_passes(tmp_path, monkeypatch):
    monkeypatch.setattr("build.check_site_data.inputs_sha", lambda root: "abc")
    data = {"schema": "aem-data/3", "meta": {"inputs_sha": "abc"}, "organizations": [], "models": [], "routes": []}
    (tmp_path / "web" / "data").mkdir(parents=True)
    (tmp_path / "web" / "data" / "data.json").write_text(json.dumps(data))
    assert check_site_data(tmp_path).errors == []


def test_site_data_built_from_other_inputs_is_out_of_date(tmp_path, monkeypatch):
    monkeypatch.setattr("build.check_site_data.inputs_sha", lambda root: "abc")
    data = {"schema": "aem-data/3", "meta": {"inputs_sha": "old"}, "organizations": [], "models": [], "routes": []}
    (tmp_path / "web" / "data").mkdir(parents=True)
    (tmp_path / "web" / "data" / "data.json").write_text(json.dumps(data))
    assert check_site_data(tmp_path).errors == [
        "web/data/data.json: is out of date: sources/ or build/ changed since the last release; "
        "run `python -m build release`"
    ]


def test_a_field_outside_the_contract_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr("build.check_site_data.inputs_sha", lambda root: "abc")
    data = {
        "schema": "aem-data/3",
        "meta": {"inputs_sha": "abc"},
        "organizations": [],
        "models": [],
        "routes": [],
        "unknown_field": {},
    }
    (tmp_path / "web" / "data").mkdir(parents=True)
    (tmp_path / "web" / "data" / "data.json").write_text(json.dumps(data))
    assert check_site_data(tmp_path).errors == [
        "web/data/data.json: top level: field 'unknown_field' is not in the contract"
    ]


def test_a_missing_data_file_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr("build.check_site_data.inputs_sha", lambda root: "abc")
    assert check_site_data(tmp_path).errors == ["web/data/data.json: is missing; run `python -m build release`"]


def test_a_data_file_that_is_not_json_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr("build.check_site_data.inputs_sha", lambda root: "abc")
    (tmp_path / "web" / "data").mkdir(parents=True)
    (tmp_path / "web" / "data" / "data.json").write_text("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> other\n")
    assert check_site_data(tmp_path).errors == [
        "web/data/data.json: is not valid JSON (a merge conflict?); run `python -m build release`"
    ]


def test_the_gate_hashes_the_root_it_checks(tmp_path, monkeypatch):
    fake_inputs_sha = Mock(return_value="abc")
    monkeypatch.setattr("build.check_site_data.inputs_sha", fake_inputs_sha)
    data = {"schema": "aem-data/3", "meta": {"inputs_sha": "abc"}, "organizations": [], "models": [], "routes": []}
    (tmp_path / "web" / "data").mkdir(parents=True)
    (tmp_path / "web" / "data" / "data.json").write_text(json.dumps(data))
    check_site_data(tmp_path)
    fake_inputs_sha.assert_called_once_with(tmp_path)
