"""Green Software Foundation real-time-cloud metadata -> sources/snapshots/cloud_regions.csv.

Maps each cloud region to the Electricity Maps zone(s) it draws power from, from the GSF file's
`em-zone-id` column. For each region the most recent year that names a zone is used; a region
listed under several zones in that year (Azure northeurope: Finland and Ireland) keeps all of them,
so its routes get a range. Pin a commit so the import is reproducible.

Usage:
    uv run python -m build.import_cloud_regions --commit <sha>            # fetches the file at that commit
    uv run python -m build.import_cloud_regions --commit <sha> --file Cloud_Region_Metadata.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import date
from pathlib import Path

from build.validate import ROOT

REPO = "https://github.com/Green-Software-Foundation/real-time-cloud"
RAW = "https://raw.githubusercontent.com/Green-Software-Foundation/real-time-cloud/{commit}/Cloud_Region_Metadata.csv"
VENDORS = {"Amazon Web Services": "aws", "Microsoft Azure": "azure", "Google Cloud": "gcp"}
REQUIRED = ("year", "cloud-provider", "cloud-region", "em-zone-id", "location")
FIELDS = ["vendor", "region", "zone", "year", "location"]


class CloudImportError(Exception):
    pass


def _rows(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
    if missing:
        raise CloudImportError(f"missing column(s) {missing}; found {reader.fieldnames}")
    return list(reader)


def import_cloud_regions(source: Path | None, commit: str, out_dir: Path, retrieved: date,
                         text: str | None = None) -> Path:
    """Write <out_dir>/cloud_regions.csv and cloud_regions.provenance.json from the GSF file (path or text)."""
    raw = source.read_bytes() if source is not None else text.encode("utf-8")
    rows = _rows(raw.decode("utf-8-sig"))
    by_region: dict[tuple[str, str], list[dict]] = {}
    skipped: list[dict] = []
    for row in rows:
        by_region.setdefault((row["cloud-provider"], row["cloud-region"]), []).append(row)
    out_rows: list[dict] = []
    for (provider, region), entries in sorted(by_region.items()):
        if provider not in VENDORS:
            skipped.append({"vendor": provider, "region": region, "reason": "unknown cloud provider"})
            continue
        with_zone = [e for e in entries if e["em-zone-id"].strip()]
        if not with_zone:
            skipped.append({"vendor": provider, "region": region, "reason": "no em-zone-id in any year"})
            continue
        year = max(int(e["year"]) for e in with_zone)
        zones = sorted({(e["em-zone-id"].strip(), e["location"].strip()) for e in with_zone if int(e["year"]) == year})
        out_rows += [{"vendor": VENDORS[provider], "region": region, "zone": zone, "year": year, "location": loc}
                     for zone, loc in zones]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "cloud_regions.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)
    provenance = {
        "source": "Green Software Foundation real-time-cloud, Cloud_Region_Metadata.csv (em-zone-id)",
        "repository": REPO,
        "commit": commit,
        "url": RAW.format(commit=commit),
        "licence": "see the source repository's License.md",
        "retrieved": retrieved.isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "skipped": skipped,
    }
    (out_dir / "cloud_regions.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.import_cloud_regions", description=__doc__.splitlines()[0])
    parser.add_argument("--commit", required=True, help="the real-time-cloud commit to import")
    parser.add_argument("--file", type=Path, help="a downloaded copy of the file at that commit (default: fetch it)")
    parser.add_argument("--retrieved", type=date.fromisoformat, default=date.today())
    parser.add_argument("--out-dir", type=Path, default=ROOT / "sources" / "snapshots")
    args = parser.parse_args(argv)
    text = None
    if args.file is None:
        import requests

        response = requests.get(RAW.format(commit=args.commit), timeout=60)
        response.raise_for_status()
        text = response.text
    try:
        out = import_cloud_regions(args.file, args.commit, args.out_dir, args.retrieved, text=text)
    except CloudImportError as err:
        print("ERROR:", err)
        return 1
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
