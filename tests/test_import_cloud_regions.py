import csv
import json
from datetime import date

import pytest

from build.grid import load_cloud_regions
from build.import_cloud_regions import CloudImportError, import_cloud_regions

COMMIT = "8f99b3bc01ecb342905b80a485573fda9494a052"


@pytest.fixture
def snapshot(tmp_path, fixtures_dir):
    out = import_cloud_regions(fixtures_dir / "gsf" / "Cloud_Region_Metadata.csv", commit=COMMIT,
                               out_dir=tmp_path, retrieved=date(2026, 10, 8))
    return out, tmp_path


def test_latest_year_with_a_zone_wins(snapshot):
    out, _ = snapshot
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    by_key = {}
    for r in rows:
        by_key.setdefault((r["vendor"], r["region"]), []).append((r["zone"], r["year"]))
    assert by_key[("aws", "eu-central-1")] == [("DE", "2024")]
    assert by_key[("aws", "ca-west-1")] == [("CA-AB", "2023")]      # 2024 row has no zone, 2023 does
    assert by_key[("azure", "northeurope")] == [("FI", "2023"), ("IE", "2023")]   # one region, two zones
    assert by_key[("gcp", "europe-west6")] == [("CH", "2024")]
    assert ("gcp", "us-east2") not in by_key                          # never had a zone


def test_unknown_vendor_is_skipped_and_reported(snapshot):
    _, out_dir = snapshot
    prov = json.loads((out_dir / "cloud_regions.provenance.json").read_text())
    assert prov["skipped"] == [
        {"vendor": "Google Cloud", "region": "us-east2", "reason": "no em-zone-id in any year"},
        {"vendor": "Oracle Cloud", "region": "eu-zurich-1", "reason": "unknown cloud provider"},
    ]
    assert prov["commit"] == COMMIT and prov["retrieved"] == "2026-10-08"
    assert prov["url"].endswith(f"/{COMMIT}/Cloud_Region_Metadata.csv")


def test_snapshot_loads_as_region_to_zones(snapshot):
    out, _ = snapshot
    cloud = load_cloud_regions(out)
    assert cloud[("azure", "northeurope")] == ["FI", "IE"]
    assert cloud[("aws", "eu-central-1")] == ["DE"]


def test_missing_columns_are_refused(tmp_path):
    bad = tmp_path / "meta.csv"
    bad.write_text("year,cloud-provider,cloud-region\n2024,Amazon Web Services,eu-central-1\n", encoding="utf-8")
    with pytest.raises(CloudImportError, match="em-zone-id"):
        import_cloud_regions(bad, commit=COMMIT, out_dir=tmp_path, retrieved=date(2026, 10, 8))
