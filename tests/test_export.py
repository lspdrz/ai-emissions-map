import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from build.energy import FixedEnergyModel
from build.export import SCHEMA, ExportError, export, fill_methodology
from build.ranges import Range

REPO = Path(__file__).resolve().parents[1]
ENERGY = FixedEnergyModel({
    "test-70b": (Range(0.5, 0.6), Range(0.05, 0.06)),
    "test-8b": (Range.point(0.08), Range.point(0.007)),
})
ROUTE_KEYS = {"slug", "org", "model", "label", "default", "scored", "level", "letter", "gap", "score",
              "embodied", "band", "served_as"}


def run(tmp_path, fixtures_dir, grid=None, root=None):
    out = tmp_path / "out"
    code = export(root=root or fixtures_dir / "corpus", release=date(2026, 10, 8), out_dir=out,
                       energy_model=ENERGY, grid_path=grid or fixtures_dir / "grid.csv",
                       cloud_path=fixtures_dir / "cloud_regions.csv",
                       methodology_path=REPO / "docs" / "methodology.md", ecologits_models=[])
    return code, out


def _site(out):
    return json.loads((out / "data.json").read_text())


def test_writes_the_contract(tmp_path, fixtures_dir):
    code, out = run(tmp_path, fixtures_dir)
    assert code == 0
    site = _site(out)
    assert site["schema"] == SCHEMA
    assert site["meta"]["band_upper"] == [0.03, 0.1, 0.3, 1.0]
    assert site["meta"]["counts"]["organizations"] == 4
    assert {o["slug"] for o in site["organizations"]} == {"aggregator", "alpinehost", "multihost", "vaguehost"}


def test_site_data_holds_only_what_the_site_displays(tmp_path, fixtures_dir):
    _, out = run(tmp_path, fixtures_dir)
    text = (out / "data.json").read_text()
    assert "g_per_kwh" not in text      # no grid values, per ruling R-2026-10-12-b
    for route in _site(out)["routes"]:
        assert set(route) == ROUTE_KEYS


def test_meta_flags_a_mock_grid_from_its_provenance(tmp_path, fixtures_dir):
    grid = tmp_path / "2025.csv"
    shutil.copy(fixtures_dir / "grid.csv", grid)
    grid.with_name("2025.provenance.json").write_text(json.dumps({"mock": True, "year": 2025, "attribution": "x"}))
    _, out = run(tmp_path, fixtures_dir, grid=grid)
    assert _site(out)["meta"]["grid"] == {"year": 2025, "mock": True, "attribution": "x"}


def test_a_mock_file_name_alone_flags_the_mock(tmp_path, fixtures_dir):
    grid = tmp_path / "2025.MOCK.csv"
    shutil.copy(fixtures_dir / "grid.csv", grid)
    _, out = run(tmp_path, fixtures_dir, grid=grid)
    assert _site(out)["meta"]["grid"]["mock"] is True


def test_a_real_grid_is_not_flagged(tmp_path, fixtures_dir):
    _, out = run(tmp_path, fixtures_dir)
    assert _site(out)["meta"]["grid"]["mock"] is False


def test_labels_fall_back_to_a_zone_count_and_default_is_carried(tmp_path, fixtures_dir):
    root = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", root)
    p = root / "sources" / "routes" / "alpinehost-test-8b.yaml"
    p.write_text(p.read_text().replace("  confidence: country\n", '  confidence: country\n  label: "Switzerland"\n')
                 .replace("model: test-8b\n", "model: test-8b\ndefault: true\n"))
    _, out = run(tmp_path, fixtures_dir, root=root)
    routes = {r["slug"]: r for r in _site(out)["routes"]}
    assert (routes["alpinehost-test-8b"]["label"], routes["alpinehost-test-8b"]["default"]) == ("Switzerland", True)
    assert routes["multihost-test-70b"]["label"] == "2 grid zones"
    assert routes["vaguehost-test-70b"]["label"] == "Not disclosed"
    assert routes["aggregator-test-70b"]["label"] == "Through 2 other providers"
    assert routes["alpinehost-test-70b"]["default"] is False


def test_organization_evidence_keeps_the_quoted_passages(tmp_path, fixtures_dir):
    _, out = run(tmp_path, fixtures_dir)
    alpine = next(o for o in _site(out)["organizations"] if o["slug"] == "alpinehost")
    by_url = {e["url"]: e for e in alpine["evidence"]}
    assert by_url["https://alpinehost.example/docs/regions"]["quotes"] == ["test-70b is served exclusively from ALP-1"]
    assert by_url["https://alpinehost.example/docs/regions"]["routes"] == ["alpinehost-test-70b"]


def test_featured_model_is_the_one_with_the_most_routes(tmp_path, fixtures_dir):
    _, out = run(tmp_path, fixtures_dir)
    assert _site(out)["meta"]["featured_model"] == "test-70b"


def test_methodology_is_written_with_its_placeholders_filled(tmp_path, fixtures_dir):
    _, out = run(tmp_path, fixtures_dir)
    text = (out / "methodology.md").read_text()
    assert text.startswith("## Summary")            # the authoring comment is stripped
    assert "## Full methodology" in text
    assert "{n_" not in text and "{release_date}" not in text


def test_unknown_placeholder_is_an_error():
    with pytest.raises(ExportError, match="n_unknown"):
        fill_methodology("## Summary\n{n_unknown} routes", {"n_routes": 3})


def test_validation_errors_stop_the_export(tmp_path, fixtures_dir):
    root = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", root)
    p = root / "sources" / "organizations" / "alpinehost.yaml"
    p.write_text(p.read_text().replace("type: inference_host", "type: bakery"))
    code, out = run(tmp_path, fixtures_dir, root=root)
    assert code > 0 and not (out / "data.json").exists()
