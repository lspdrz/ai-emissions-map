"""Reading sources/ from disk: every record keyed by its filename stem, and the cloud-region table."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

# The sources/ folders that hold records, in the order they are read and checked.
SOURCE_DIRS = ("organizations", "grids", "routes", "models")

CLOUD_REGIONS_FILE = Path("sources") / "snapshots" / "cloud_regions.csv"


def load_sources(root: Path) -> dict:
    """Every sources/<dir>/<slug>.yaml keyed by its filename stem, plus anything that is not one.

    `stray_files` lists entries that would otherwise be skipped silently (a .yml file, a subfolder),
    so validate_sources can report them. Dotfiles such as .DS_Store are ignored.
    """
    sources = root / "sources"
    data: dict = {"stray_files": []}
    for name in SOURCE_DIRS:
        records = {}
        directory = sources / name
        for p in sorted(directory.iterdir()) if directory.is_dir() else []:
            if p.name.startswith("."):
                continue
            if p.is_file() and p.suffix == ".yaml":
                records[p.stem] = yaml.safe_load(p.read_text(encoding="utf-8"))
            else:
                data["stray_files"].append(p.relative_to(sources).as_posix())
        data[name] = records
    return data


def load_cloud_regions(path: Path) -> dict[tuple[str, str], list[str]]:
    """(vendor, region) -> its grid zones, sorted. A region drawing on several zones has one row per zone."""
    regions: dict[tuple[str, str], list[str]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            regions.setdefault((row["vendor"], row["region"]), []).append(row["zone"])
    return {key: sorted(set(zones)) for key, zones in regions.items()}
