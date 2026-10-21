"""Where the snapshots live: the tables imported from outside the map, and the downloads they were imported from
(sources/snapshots/README.md). Paths are relative to the repository root."""

from __future__ import annotations

from pathlib import Path

SNAPSHOTS_DIR = Path("sources") / "snapshots"

# Cloud region -> grid zone(s), from the Green Software Foundation (python -m build import-cloud-regions).
CLOUD_REGIONS_FILE = SNAPSHOTS_DIR / "cloud_regions.csv"
# Country, US state or Chinese province -> grid intensity, from Ember (python -m build import-ember).
GRID_INTENSITY_FILE = SNAPSHOTS_DIR / "grid_intensity.csv"

# Where the imports keep the files they read, as downloaded (Ember's in ember_files/, the GSF's in gsf_files/).
SNAPSHOT_SOURCE_DIR = SNAPSHOTS_DIR / "files"
