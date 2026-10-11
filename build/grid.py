"""Grid intensity (I) per zone, and resolution of route locations to zones (spec §8)."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from build.ranges import Range


class GridError(Exception):
    pass


def load_grid(path: Path) -> dict[str, dict]:
    """Zone -> {"direct", "lifecycle": gCO2e/kWh, consumption-based; "fallback": bool; "source": str}.

    The score uses direct factors; life-cycle factors are shown alongside.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        return {
            row["zone"]: {
                "direct": float(row["direct_gco2_per_kwh"]), "lifecycle": float(row["lifecycle_gco2_per_kwh"]),
                "fallback": row["fallback"].strip().lower() == "true", "source": row["source"],
            }
            for row in csv.DictReader(fh)
        }


def latest_grid(directory: Path, allow_mock: bool = False) -> Path | None:
    """The newest real snapshot, <year>.csv. A <year>.MOCK.csv counts only with allow_mock, and never beats real data."""
    real = sorted(p for p in directory.glob("*.csv") if re.fullmatch(r"\d{4}", p.stem))
    if real:
        return real[-1]
    mocks = sorted(p for p in directory.glob("*.csv") if re.fullmatch(r"\d{4}\.MOCK", p.stem))
    return mocks[-1] if allow_mock and mocks else None


def load_cloud_regions(path: Path) -> dict[tuple[str, str], list[str]]:
    """(vendor, region) -> its grid zones, sorted. A region drawing on several zones has one row per zone."""
    regions: dict[tuple[str, str], list[str]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            regions.setdefault((row["vendor"], row["region"]), []).append(row["zone"])
    return {key: sorted(set(zones)) for key, zones in regions.items()}


def resolve_zones(location: dict, facilities: dict, cloud_regions: dict[tuple[str, str], list[str]]) -> list[str]:
    if location["confidence"] == "unknown":
        raise GridError("an unknown location cannot be resolved to grid zones")
    zones: set[str] = set()
    for cand in location["candidates"]:
        kind, _, rest = cand.partition(":")
        if kind == "facility":
            if rest not in facilities:
                raise GridError(f"facility {rest!r} not found")
            zones.add(facilities[rest]["grid_zone"])
        elif kind == "cloud":
            vendor, _, region = rest.partition(":")
            if (vendor, region) not in cloud_regions:
                raise GridError(f"cloud region {vendor}:{region} not found")
            zones.update(cloud_regions[(vendor, region)])
        elif kind == "zone":
            zones.add(rest)
        else:
            raise GridError(f"unrecognised location candidate {cand!r}")
    if not zones:
        raise GridError(f"location with confidence {location['confidence']!r} lists no candidates")
    return sorted(zones)


def intensity_range(zones: list[str], grid: dict[str, dict], basis: str) -> Range:
    missing = [z for z in zones if z not in grid]
    if missing:
        raise GridError(f"grid data has no intensity for zone(s): {', '.join(missing)}")
    values = [grid[z][basis] for z in zones]
    return Range(min(values), max(values))
