"""Grid emissions: each grid's carbon intensity, looked up in Ember's data and written into the grid's file.

When a curator adds a grid, `python -m build grid-emissions --write <grid>` looks up its intensity in the Ember
snapshot (sources/snapshots/grid_intensity.csv) and writes it at the end of the grid file. `score` reads it from there
and never opens the snapshot. CI runs `python -m build grid-emissions`, without --write, to make sure every stored value
still matches it.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

import yaml
from pydantic import TypeAdapter

from build.constants.config import GRID_YEAR
from build.load_sources import GRID_INTENSITY_FILE, load_grid_intensities, load_sources
from build.schemas.grid import CheckedGrid, Grid, GridIntensity
from build.validate import check_identity

# The Ember snapshot, as load_grid_intensities reads it: geography -> year -> intensity in gCO2e/kWh. A geography is a
# country code (CH) or a subdivision code (US-VA, CN-GD).
EmberTable = Mapping[str, Mapping[int, float]]

# The comment above the intensity: field at the end of a grid file. The command rewrites everything below it.
GRID_EMISSIONS_COMMENT = (
    "# Written by `python -m build grid-emissions` from sources/snapshots/grid_intensity.csv. Everything below this line"
    " is rewritten by it; do not edit it by hand."
)


class GridRun(NamedTuple):
    errors: list[str]
    written: list[Path]


# Looking up one grid.


def grid_geography(grid: Grid) -> str:
    """Where to look a grid up: its subdivision if it names one (US-VA), otherwise its country (CH)."""
    if "subdivision" in grid:
        return f"{grid['country']}-{grid['subdivision']}"
    return grid["country"]


def grid_intensity(grid: Grid, ember: EmberTable, year: int) -> GridIntensity:
    """The grid's intensity for `year`, or for the latest earlier year Ember has; never a later one.

    Raises ValueError when there is none, or when the grid is on-site (a facility's own generation, which no country
    or state average describes)."""
    if grid.get("supply") == "onsite":
        raise ValueError(f"grids/{grid['name']}.yaml: an on-site grid has no Ember value")
    geography = grid_geography(grid)
    years = [y for y in ember.get(geography, {}) if y <= year]
    if not years:
        raise ValueError(f"grids/{grid['name']}.yaml: Ember has no intensity for {geography!r} in {year} or earlier")
    latest = max(years)
    return GridIntensity(g_per_kwh=ember[geography][latest], year=latest, geography=geography, source="Ember")


def _look_up(root: Path, names: list[str] | None = None) -> tuple[dict[str, Grid], dict[str, GridIntensity], list[str]]:
    """Read the grid files and the snapshot, and look up each grid (only `names`, when given), in name order.

    Returns the grids, their intensities and every problem found: a grid file that fails its schema, a name with no
    file, a missing snapshot, a grid Ember has no value for."""
    errors, grids = check_identity("grids", load_sources(root).get("grids") or {}, TypeAdapter(CheckedGrid))
    errors += [f"grids/{name}.yaml: no such grid file" for name in sorted(set(names or []) - set(grids))]
    snapshot = root / GRID_INTENSITY_FILE
    if not snapshot.exists():
        errors.append(f"{GRID_INTENSITY_FILE.as_posix()}: missing; run `python -m build import-ember`")
    if errors:
        return grids, {}, errors

    ember = load_grid_intensities(snapshot)
    values: dict[str, GridIntensity] = {}
    for name in sorted(names or grids):
        try:
            values[name] = grid_intensity(grids[name], ember, GRID_YEAR)
        except ValueError as error:
            errors.append(f"{error}; see docs/workflows/add-grid.md")
    return grids, values, errors


def _with_intensity(text: str, value: GridIntensity) -> str:
    """A grid file's text with its intensity: field written below GRID_EMISSIONS_COMMENT, replacing any earlier one.
    Everything above the comment is kept exactly as the curator wrote it (the file is never loaded and re-dumped)."""
    curated = text.partition(GRID_EMISSIONS_COMMENT)[0].rstrip()
    field = yaml.safe_dump({"intensity": dict(value)}, sort_keys=False, allow_unicode=True)
    return f"{curated}\n\n{GRID_EMISSIONS_COMMENT}\n{field}"


def _difference(name: str, stored: GridIntensity | None, value: GridIntensity) -> str:
    """What is wrong with a grid file whose intensity: is not what grid-emissions would write, and how to fix it."""
    fix = f"run `python -m build grid-emissions --write {name}`"
    if stored is None:
        return f"grids/{name}.yaml: is missing the intensity field; {fix}"
    changed = [key for key in value if stored.get(key) != value[key]]
    if changed:
        return f"grids/{name}.yaml: its intensity is out of date ({', '.join(changed)}); {fix}"
    return f"grids/{name}.yaml: its intensity: block was edited by hand; {fix}"


def grid_emissions(root: Path, names: list[str] | None = None, *, write: bool = False) -> GridRun:
    """python -m build grid-emissions [--write] [<grid> ...]: compare each grid's stored intensity with the snapshot
    (the named grids, or every grid if none is named).

    Without write (what CI runs), every grid that differs is an error and nothing is written. With write (what a
    curator runs after adding a grid), the differences are written instead. Either way, nothing is written if any grid
    has a problem."""
    grids, values, errors = _look_up(root, names)
    if errors:
        return GridRun(errors, [])
    written = []
    for name, value in values.items():
        path = root / "sources" / "grids" / f"{name}.yaml"
        old = path.read_text(encoding="utf-8")
        new = _with_intensity(old, value)
        if new == old:
            continue
        if write:
            path.write_text(new, encoding="utf-8")
            written.append(path)
        else:
            errors.append(_difference(name, grids[name].get("intensity"), value))
    return GridRun(errors, written)
