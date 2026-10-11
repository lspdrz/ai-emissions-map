import json
from datetime import date

from build.energy import FixedEnergyModel
from build.ranges import Range
from build.serialize import serialize

ENERGY = FixedEnergyModel({
    "test-70b": (Range(0.5, 0.6), Range(0.05, 0.06)),
    "test-8b": (Range.point(0.08), Range.point(0.007)),
})


def run(tmp_path, fixtures_dir, **kw):
    return serialize(root=fixtures_dir / "corpus", release=date(2026, 10, 8), out_dir=tmp_path, energy_model=ENERGY,
                     grid_path=fixtures_dir / "grid.csv", cloud_path=fixtures_dir / "cloud_regions.csv",
                     ecologits_models=[], **kw)


def test_end_to_end_on_fixture_corpus(tmp_path, fixtures_dir):
    assert run(tmp_path, fixtures_dir) == 0
    orgs = json.loads((tmp_path / "organizations.json").read_text())
    routes = json.loads((tmp_path / "routes.json").read_text())
    assert orgs["meta"]["release_date"] == "2026-10-08"
    assert orgs["meta"]["methodology_version"] == "0.1.0"
    by_org = {o["org"]: o for o in orgs["organizations"]}
    assert by_org["alpinehost"]["summary"] == "B (1 route at A, 1 route at C)"
    by_route = {r["name"]: r for r in routes["routes"]}
    multi = by_route["multihost-test-70b"]
    assert multi["org"] == "multihost"
    assert multi["score_direct_g_per_1k_tokens"] == {"low": 0.07, "high": 0.258}
    assert multi["operational_direct_g_per_1k_tokens"] == {"low": 0.02, "high": 0.198}
    assert multi["band"] == [2, 3]
    assert multi["rating"]["letter"] == "D"
    assert by_route["vaguehost-test-70b"]["scored"] is False
    assert by_route["vaguehost-test-70b"]["score_direct_g_per_1k_tokens"] is None


def test_validation_errors_stop_the_build(tmp_path, fixtures_dir, capsys):
    assert run(tmp_path, fixtures_dir, grid_zones_override={"DE", "FR"}) > 0
    assert not (tmp_path / "organizations.json").exists()
    assert "ERROR: facilities/alp-1.yaml: grid zone 'CH' is not in the grid data" in capsys.readouterr().out


def test_broken_model_file_is_reported_not_raised(tmp_path, fixtures_dir, capsys):
    import shutil
    root = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", root)
    model = root / "sources" / "models" / "test-8b.yaml"
    model.write_text(model.read_text().replace("active_b: 8\n", "active_b: 8B\n"))
    out = tmp_path / "out"
    assert serialize(root=root, release=date(2026, 10, 8), out_dir=out, energy_model=ENERGY,
                     grid_path=fixtures_dir / "grid.csv", cloud_path=fixtures_dir / "cloud_regions.csv",
                     ecologits_models=[]) > 0
    assert "ERROR: models/test-8b.yaml: active_b:" in capsys.readouterr().out
    assert not out.exists()


def test_release_meta_records_input_provenance(tmp_path, fixtures_dir):
    import shutil
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    shutil.copy(fixtures_dir / "grid.csv", inputs / "2025.csv")
    shutil.copy(fixtures_dir / "cloud_regions.csv", inputs / "cloud_regions.csv")
    (inputs / "2025.provenance.json").write_text(json.dumps(
        {"year": 2025, "retrieved": "2026-10-08", "licence": "ODbL-1.0", "attribution": "Electricity Maps",
         "files": []}))
    (inputs / "cloud_regions.provenance.json").write_text(json.dumps(
        {"repository": "https://github.com/Green-Software-Foundation/real-time-cloud", "commit": "8f99b3b",
         "retrieved": "2026-10-08", "skipped": []}))
    out = tmp_path / "out"
    assert serialize(root=fixtures_dir / "corpus", release=date(2026, 10, 8), out_dir=out, energy_model=ENERGY,
                     grid_path=inputs / "2025.csv", cloud_path=inputs / "cloud_regions.csv", ecologits_models=[]) == 0
    meta = json.loads((out / "routes.json").read_text())["meta"]
    assert meta["grid_data"] == {"year": 2025, "retrieved": "2026-10-08", "licence": "ODbL-1.0",
                                 "attribution": "Electricity Maps"}
    assert meta["cloud_regions"]["commit"] == "8f99b3b"


def test_meta_without_provenance_says_so(tmp_path, fixtures_dir):
    assert run(tmp_path, fixtures_dir) == 0
    meta = json.loads((tmp_path / "routes.json").read_text())["meta"]
    assert meta["grid_data"] is None and meta["cloud_regions"] is None


def test_cli_without_grid_data_explains_itself(tmp_path, capsys):
    from build.serialize import main
    assert main(["--release-date", "2026-10-08", "--root", str(tmp_path)]) == 1
    assert "no grid snapshot in" in capsys.readouterr().out
