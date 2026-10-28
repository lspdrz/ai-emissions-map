"""Reading sources/ from disk: every record keyed by its filename stem, the cloud-region table and the grid-intensity
table."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

from build.constants.snapshots import CLOUD_REGIONS_FILE, GRID_INTENSITY_FILE
from build.types import CloudRegion

# The sources/ folders that hold records, in the order they are read and checked.
SOURCE_DIRS = ("organizations", "grids", "routes", "models")


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


def load_cloud_regions(path: Path) -> dict[tuple[str, str], CloudRegion]:
    """(vendor, region) -> its grid zones, sorted, and its published PUE. A region drawing on several zones has one
    row per zone, each with the region's PUE; a region without one, or a table without the pue column, has None."""
    regions: dict[tuple[str, str], CloudRegion] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            region = regions.setdefault((row["vendor"], row["region"]), CloudRegion(zones=[], pue=None))
            region["zones"].append(row["zone"])
            if row.get("pue"):
                region["pue"] = float(row["pue"])
    return {key: CloudRegion(zones=sorted(set(r["zones"])), pue=r["pue"]) for key, r in regions.items()}


def load_grid_intensities(path: Path) -> dict[str, dict[int, float]]:
    """Each geography (a country's ISO 3166-1 alpha-2 code, or a subdivision's ISO 3166-2 code such as US-VA or
    CN-GD) to its Ember intensity by year, in gCO2e/kWh: one year each, as import-ember keeps it."""
    intensities: dict[str, dict[int, float]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            intensities.setdefault(row["geography"], {})[int(row["year"])] = float(row["intensity"])
    return intensities
