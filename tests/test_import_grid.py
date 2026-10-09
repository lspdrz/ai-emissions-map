import csv
import hashlib
import json
from datetime import date

import pytest

from build.import_grid import GridImportError, import_grid, read_yearly
from build.grid import load_grid

EM = "electricitymaps"


def test_reads_one_yearly_file(fixtures_dir):
    row = read_yearly(fixtures_dir / EM / "CH_2024_yearly.csv")   # UTF-8 with a byte-order mark
    assert row == {"zone": "CH", "year": 2024, "direct": 29.85, "lifecycle": 45.12, "estimated": False}


def test_writes_snapshot_and_provenance(tmp_path, fixtures_dir):
    files = [fixtures_dir / EM / "DE_2024_yearly.csv", fixtures_dir / EM / "CH_2024_yearly.csv"]
    out = import_grid(files, year=2024, out_dir=tmp_path, retrieved=date(2026, 10, 8))
    assert out == tmp_path / "2024.csv"
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["zone"] for r in rows] == ["CH", "DE"]                     # sorted by zone
    assert rows[1] == {"zone": "DE", "year": "2024", "direct_gco2_per_kwh": "330.4",
                       "lifecycle_gco2_per_kwh": "380.9", "source": "electricitymaps", "fallback": "false",
                       "estimated": "true"}
    # The snapshot is what build.grid reads.
    assert load_grid(out)["CH"] == {"direct": 29.85, "lifecycle": 45.12, "fallback": False,
                                    "source": "electricitymaps"}
    prov = json.loads((tmp_path / "2024.provenance.json").read_text())
    assert prov["licence"] == "ODbL-1.0" and prov["retrieved"] == "2026-10-08"
    assert prov["files"][0] == {"name": "CH_2024_yearly.csv",
                                "sha256": hashlib.sha256((fixtures_dir / EM / "CH_2024_yearly.csv").read_bytes()).hexdigest()}


def test_wrong_year_is_refused(tmp_path, fixtures_dir):
    with pytest.raises(GridImportError, match="FR_2023_yearly.csv.*2023.*2024"):
        import_grid([fixtures_dir / EM / "FR_2023_yearly.csv"], year=2024, out_dir=tmp_path, retrieved=date(2026, 10, 8))
    assert not (tmp_path / "2024.csv").exists()


def test_duplicate_zone_is_refused(tmp_path, fixtures_dir):
    ch = fixtures_dir / EM / "CH_2024_yearly.csv"
    with pytest.raises(GridImportError, match="CH"):
        import_grid([ch, ch], year=2024, out_dir=tmp_path, retrieved=date(2026, 10, 8))


def test_unexpected_columns_name_what_was_found(tmp_path):
    bad = tmp_path / "XX_2024_hourly.csv"
    bad.write_text("Datetime (UTC),Zone id,Carbon intensity\n2024-01-01 00:00:00,XX,12\n", encoding="utf-8")
    with pytest.raises(GridImportError, match=r"XX_2024_hourly.csv.*missing.*Life cycle.*found"):
        read_yearly(bad)


def test_hourly_file_is_refused(tmp_path, fixtures_dir):
    lines = (fixtures_dir / EM / "DE_2024_yearly.csv").read_text(encoding="utf-8").splitlines()
    hourly = tmp_path / "DE_2024_hourly.csv"
    hourly.write_text("\n".join([lines[0], lines[1], lines[1].replace("00:00:00", "01:00:00")]) + "\n", encoding="utf-8")
    with pytest.raises(GridImportError, match="one row"):
        read_yearly(hourly)


def test_blank_intensity_is_refused(tmp_path, fixtures_dir):
    lines = (fixtures_dir / EM / "DE_2024_yearly.csv").read_text(encoding="utf-8").splitlines()
    blank = tmp_path / "DE_2024_yearly.csv"
    blank.write_text(lines[0] + "\n" + lines[1].replace("330.4", "") + "\n", encoding="utf-8")
    with pytest.raises(GridImportError, match="DE_2024_yearly.csv.*direct"):
        read_yearly(blank)
