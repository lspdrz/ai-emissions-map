"""python -m build import-cloud-regions: the Green Software Foundation's cloud-region metadata -> cloud_regions.csv.

Reads Cloud_Region_Metadata.csv from https://github.com/Green-Software-Foundation/real-time-cloud at a pinned commit,
downloaded by hand from the URL below (sources/snapshots/README.md), keeps each AWS, Azure and Google Cloud region's
grid zones and its published PUE, and writes the table every cloud: candidate resolves through, with a .provenance.json beside it. It keeps a
copy of the download in sources/snapshots/files/gsf_files/, under its file name, replacing the previous one; git holds
the earlier ones.

    uv run python -m build import-cloud-regions --csv <Cloud_Region_Metadata.csv> --commit <commit>
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path

from build.constants.snapshots import CLOUD_REGIONS_FILE, SNAPSHOT_SOURCE_DIR
from build.types import Import

REPOSITORY = "https://github.com/Green-Software-Foundation/real-time-cloud"
FILE_NAME = "Cloud_Region_Metadata.csv"
RAW_URL = "https://raw.githubusercontent.com/Green-Software-Foundation/real-time-cloud/{commit}/" + FILE_NAME
# The providers kept, under the vendor names cloud: candidates use.
VENDORS = {"Amazon Web Services": "aws", "Microsoft Azure": "azure", "Google Cloud": "gcp"}
COLUMNS = ("vendor", "region", "zone", "year", "location", "pue", "pue_year")
# Where the download is kept.
DOWNLOAD_COPY = SNAPSHOT_SOURCE_DIR / "gsf_files" / FILE_NAME


def region_rows(metadata_csv: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """The table's rows and the regions left out, each with its reason. Each region keeps the zones it lists in the
    most recent year that has an em-zone-id, one row per zone (a region drawing on several zones gives its routes a
    range), and its power-usage-effectiveness in the most recent year that has one, on each of its rows (empty when
    no year has one). Rows and skipped regions are sorted by provider (its full name, as the source spells it) and region, and a
    region's zones by code."""
    with metadata_csv.open(encoding="utf-8-sig", newline="") as fh:
        records = list(csv.DictReader(fh))
    regions: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in records:
        regions.setdefault((r["cloud-provider"], r["cloud-region"]), []).append(r)
    rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for (provider, region), entries in sorted(regions.items()):
        if provider not in VENDORS:
            skipped.append({"vendor": provider, "region": region, "reason": "provider not kept"})
            continue
        zoned = [r for r in entries if r["em-zone-id"]]
        if not zoned:
            skipped.append({"vendor": provider, "region": region, "reason": "no em-zone-id in any year"})
            continue
        year = max(int(r["year"]) for r in zoned)
        zones = {r["em-zone-id"]: r["location"] for r in zoned if int(r["year"]) == year}
        with_pue = [r for r in entries if r["power-usage-effectiveness"]]
        pue_year = max((int(r["year"]) for r in with_pue), default=None)
        pue = next((r["power-usage-effectiveness"] for r in with_pue if int(r["year"]) == pue_year), "")
        for zone in sorted(zones):
            rows.append(
                {
                    "vendor": VENDORS[provider],
                    "region": region,
                    "zone": zone,
                    "year": str(year),
                    "location": zones[zone],
                    "pue": pue,
                    "pue_year": "" if pue_year is None else str(pue_year),
                }
            )
    return rows, skipped


def import_cloud_regions(root: Path, metadata_csv: Path, commit: str, today: date) -> Import:
    """Write sources/snapshots/cloud_regions.csv and its .provenance.json from the metadata at `commit`, and a copy of
    the download in sources/snapshots/files/gsf_files/; list the files whose content changed."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        return Import(
            [f"{commit!r}: not a commit; pin the file at a full 40-character commit hash, never a branch"], []
        )
    if not metadata_csv.is_file():
        return Import([f"{metadata_csv}: no such file; download it from the URL in sources/snapshots/README.md"], [])
    rows, skipped = region_rows(metadata_csv)
    table = io.StringIO()
    writer = csv.writer(table, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows([row[c] for c in COLUMNS] for row in rows)
    download = metadata_csv.read_bytes()
    provenance = {
        "source": "Green Software Foundation real-time-cloud, Cloud_Region_Metadata.csv (em-zone-id, power-usage-effectiveness)",
        "repository": REPOSITORY,
        "commit": commit,
        "url": RAW_URL.format(commit=commit),
        "copy": DOWNLOAD_COPY.as_posix(),
        "licence": "see the source repository's License.md",
        "retrieved": today.isoformat(),
        "sha256": hashlib.sha256(download).hexdigest(),
        "skipped": skipped,
    }
    path = root / CLOUD_REGIONS_FILE
    outputs = {
        root / DOWNLOAD_COPY: download,
        path: table.getvalue().encode(),
        path.with_suffix(".provenance.json"): (json.dumps(provenance, indent=2, ensure_ascii=False) + "\n").encode(),
    }
    written = []
    for out, content in outputs.items():
        if not out.exists() or out.read_bytes() != content:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(content)
            written.append(out)
    return Import([], written)
