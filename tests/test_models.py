import pytest
import yaml

from build.models import (add_record, check_ecologits_records, ecologits_record, installed_ecologits_version, main,
                          model_slug, model_specs, packaged_ecologits_models)
from build.ranges import Range

MOE = {"provider": "google_genai", "name": "gemini-3.5-flash",
       "architecture": {"type": "moe", "parameters": {"total": 900, "active": {"min": 90, "max": 240}}}}
DENSE = {"provider": "meta", "name": "meta-llama/CodeLlama-13b-hf",
         "architecture": {"type": "dense", "parameters": 13}}
PACKAGE = [MOE, DENSE]


def _eco(name, entry, version="0.11.2"):
    return {"name": name, "source": "ecologits", **ecologits_record(entry, version)}


def test_ecologits_moe_entry_becomes_a_record():
    assert ecologits_record(MOE, "0.11.2") == {
        "ecologits": {"id": "gemini-3.5-flash", "version": "0.11.2"}, "architecture": "moe",
        "active_b": {"min": 90, "max": 240}, "total_b": 900}


def test_ecologits_dense_entry_has_equal_active_and_total():
    record = ecologits_record(DENSE, "0.11.2")
    assert (record["architecture"], record["active_b"], record["total_b"]) == ("dense", 13, 13)


def test_specs_come_from_the_records_whatever_their_source(sources):
    models = dict(sources["models"]) | {"gemini-3-5-flash": _eco("gemini-3-5-flash", MOE)}
    specs = model_specs(models)
    assert specs["gemini-3-5-flash"] == {"active_b": Range(90, 240), "total_b": Range.point(900), "source": "ecologits"}
    assert specs["test-70b"] == {"active_b": Range.point(70), "total_b": Range.point(70), "source": "curated"}


def test_record_matching_the_package_passes():
    assert check_ecologits_records({"g": _eco("g", MOE)}, PACKAGE, "0.11.2") == []


def test_changed_parameters_are_named_with_the_fix():
    newer = [{**MOE, "architecture": {"type": "moe", "parameters": {"total": 900, "active": {"min": 100, "max": 250}}}}]
    assert check_ecologits_records({"g": _eco("g", MOE)}, newer, "0.12.0") == [
        "models/g.yaml: out of date with EcoLogits 0.12.0 (version 0.11.2 → 0.12.0; active_b 90–240 → 100–250); "
        "run `python -m build.models --sync`"]


def test_a_new_version_alone_is_reported():
    errors = check_ecologits_records({"g": _eco("g", MOE)}, PACKAGE, "0.12.0")
    assert errors == ["models/g.yaml: out of date with EcoLogits 0.12.0 (version 0.11.2 → 0.12.0); "
                      "run `python -m build.models --sync`"]


def test_an_id_missing_from_the_package_is_reported():
    assert check_ecologits_records({"g": _eco("g", MOE)}, [DENSE], "0.11.2") == [
        "models/g.yaml: 'gemini-3.5-flash' is not in EcoLogits 0.11.2"]


def test_curated_records_are_not_compared(sources):
    assert check_ecologits_records(sources["models"], PACKAGE, "0.11.2") == []


def test_model_slug_follows_the_route_slug_rule():
    assert model_slug("meta-llama/CodeLlama-13b-hf") == "codellama-13b-hf"
    assert model_slug("gemini-3.5-flash") == "gemini-3-5-flash"


def _root(tmp_path):
    (tmp_path / "sources" / "models").mkdir(parents=True)
    return tmp_path


def test_add_writes_a_record_from_the_package(tmp_path, capsys):
    root = _root(tmp_path)
    assert main(["--add", "gemini-3.5-flash", "--root", str(root)], package=PACKAGE, version="0.11.2") == 0
    record = yaml.safe_load((root / "sources" / "models" / "gemini-3-5-flash.yaml").read_text())
    assert record == {"name": "gemini-3-5-flash", "display_name": "gemini-3.5-flash", "source": "ecologits",
                      **ecologits_record(MOE, "0.11.2")}
    assert "wrote sources/models/gemini-3-5-flash.yaml" in capsys.readouterr().out


def test_add_refuses_an_unknown_id_or_an_existing_file(tmp_path, capsys):
    root = _root(tmp_path)
    assert main(["--add", "no-such-model", "--root", str(root)], package=PACKAGE, version="0.11.2") == 1
    assert "ERROR: 'no-such-model' is not in EcoLogits 0.11.2" in capsys.readouterr().out
    main(["--add", "gemini-3.5-flash", "--root", str(root)], package=PACKAGE, version="0.11.2")
    assert main(["--add", "gemini-3.5-flash", "--root", str(root)], package=PACKAGE, version="0.11.2") == 1
    assert "ERROR: sources/models/gemini-3-5-flash.yaml already exists" in capsys.readouterr().out


def test_sync_rewrites_only_the_lines_it_manages(tmp_path):
    root = _root(tmp_path)
    main(["--add", "gemini-3.5-flash", "--root", str(root)], package=PACKAGE, version="0.11.2")
    path = root / "sources" / "models" / "gemini-3-5-flash.yaml"
    path.write_text(path.read_text().replace("display_name: gemini-3.5-flash", "display_name: Gemini 3.5 Flash")
                    + "comments: >-\n  Kept by hand.\n")
    newer = [{**MOE, "architecture": {"type": "moe", "parameters": {"total": 900, "active": {"min": 100, "max": 250}}}}]
    assert main(["--sync", "--root", str(root)], package=newer, version="0.12.0") == 0
    record = yaml.safe_load(path.read_text())
    assert record["active_b"] == {"min": 100, "max": 250} and record["ecologits"]["version"] == "0.12.0"
    assert (record["display_name"], record["comments"]) == ("Gemini 3.5 Flash", "Kept by hand.")
    assert check_ecologits_records({"gemini-3-5-flash": record}, newer, "0.12.0") == []


@pytest.mark.ecologits
def test_every_real_catalogue_entry_round_trips_through_a_written_record(tmp_path):
    package, version = packaged_ecologits_models(), installed_ecologits_version()
    root = _root(tmp_path)
    seen = set()
    for entry in package:
        if model_slug(entry["name"]) in seen:
            continue   # two catalogue ids can share a slug; --add refuses the second, as it should
        seen.add(model_slug(entry["name"]))
        add_record(root / "sources" / "models", entry["name"], package, version)
    records = {p.stem: yaml.safe_load(p.read_text()) for p in (root / "sources" / "models").glob("*.yaml")}
    assert check_ecologits_records(records, package, version) == []


def test_add_creates_the_models_directory_for_the_first_record(tmp_path):
    assert main(["--add", "gemini-3.5-flash", "--root", str(tmp_path)], package=PACKAGE, version="0.11.2") == 0
    assert (tmp_path / "sources" / "models" / "gemini-3-5-flash.yaml").exists()
