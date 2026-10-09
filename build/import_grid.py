"""Electricity Maps yearly CSVs -> sources/snapshots/grid/<year>.csv, with a provenance file beside it.

The free historical datasets (consumption-based, direct and life-cycle factors, ODbL) are downloaded
by a maintainer from the Electricity Maps data portal, which needs a free account; this module only
imports what was downloaded, one yearly file per zone.

Usage:
    uv run python -m build.import_grid --year 2024 --retrieved 2026-10-08 ~/Downloads/*_2024_yearly.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from build.validate import ROOT

SOURCE_URL = "https://portal.electricitymaps.com/datasets"
COLUMNS = {
    "datetime": "Datetime (UTC)",
    "zone": "Zone id",
    "direct": "Carbon intensity gCO₂eq/kWh (direct)",
    "lifecycle": "Carbon intensity gCO₂eq/kWh (Life cycle)",
    "estimated": "Data estimated",
}
SNAPSHOT_FIELDS = ["zone", "year", "direct_gco2_per_kwh", "lifecycle_gco2_per_kwh", "source", "fallback", "estimated"]


class GridImportError(Exception):
    pass


def read_yearly(path: Path) -> dict:
    """The one row of an Electricity Maps yearly file: {"zone", "year", "direct", "lifecycle", "estimated"}."""
    with path.open(encoding="utf-8-sig", newline="") as fh:  # the portal's files may carry a byte-order mark
        reader = csv.DictReader(fh)
        rows = list(reader)
        found = reader.fieldnames or []
    missing = [c for c in COLUMNS.values() if c not in found]
    if missing:
        raise GridImportError(f"{path.name}: missing column(s) {missing}; found {found}")
    if len(rows) != 1:
        raise GridImportError(f"{path.name}: a yearly file has one row, this one has {len(rows)}")
    row = rows[0]
    values = {}
    for key in ("direct", "lifecycle"):
        try:
            values[key] = float(row[COLUMNS[key]])
        except ValueError:
            raise GridImportError(f"{path.name}: {key} intensity {row[COLUMNS[key]]!r} is not a number") from None
    return {"zone": row[COLUMNS["zone"]], "year": int(row[COLUMNS["datetime"]][:4]), **values,
            "estimated": row[COLUMNS["estimated"]].strip().lower() == "true"}


def import_grid(files: list[Path], year: int, out_dir: Path, retrieved: date) -> Path:
    """Write <out_dir>/<year>.csv and <year>.provenance.json. Nothing is written if any file is refused."""
    rows: dict[str, dict] = {}
    for path in files:
        row = read_yearly(path)
        if row["year"] != year:
            raise GridImportError(f"{path.name}: data year {row['year']}, expected {year}")
        if row["zone"] in rows:
            raise GridImportError(f"{path.name}: zone {row['zone']} appears in more than one file")
        rows[row["zone"]] = row
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{year}.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SNAPSHOT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for zone in sorted(rows):
            r = rows[zone]
            writer.writerow({"zone": zone, "year": year, "direct_gco2_per_kwh": r["direct"],
                             "lifecycle_gco2_per_kwh": r["lifecycle"], "source": "electricitymaps",
                             "fallback": "false", "estimated": str(r["estimated"]).lower()})
    provenance = {
        "source": "Electricity Maps historical datasets: yearly, consumption-based, direct and life-cycle factors",
        "url": SOURCE_URL,
        "licence": "ODbL-1.0",
        "attribution": "Electricity Maps (https://www.electricitymaps.com)",
        "retrieved": retrieved.isoformat(),
        "year": year,
        "files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in sorted(files, key=lambda p: p.name)],
    }
    (out_dir / f"{year}.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.import_grid", description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path, help="Electricity Maps yearly CSVs, one per zone")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--retrieved", type=date.fromisoformat, default=date.today(),
                        help="the day the files were downloaded (default: today)")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "sources" / "snapshots" / "grid")
    args = parser.parse_args(argv)
    try:
        out = import_grid(args.files, args.year, args.out_dir, args.retrieved)
    except GridImportError as err:
        print("ERROR:", err)
        return 1
    print(f"wrote {out} ({len(args.files)} zone(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
