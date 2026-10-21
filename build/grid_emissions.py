"""Each grid's carbon intensity: Ember's yearly value for its subdivision (a US state, a Chinese province) or else its
country, from the committed snapshot sources/snapshots/grid_intensity.csv. It is written into the grid file at curation
time, and a CI gate keeps it current.

    uv run python -m build grid-emissions [<grid> ...]   # write the intensity: of the named grids (default: all)
    uv run python -m build check-grid-emissions        # CI gate: every stored intensity: is what it would write now

The intensity is written when a grid is added (docs/workflows/add-grid.md) or the snapshot refreshed (`import-ember`
rewrites every grid), below GRID_EMISSIONS_COMMENT at the end of the grid file. `score` and `release` only read it:
neither loads Ember's table.
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

# Ember's intensities as sources/snapshots/grid_intensity.csv holds them: each geography (a country's ISO 3166-1 alpha-2
# code, or a subdivision's ISO 3166-2 code such as US-VA or CN-GD) to its value per year, in gCO2e/kWh
# (build.load_sources.load_grid_intensities reads it).
GridIntensities = Mapping[str, Mapping[int, float]]


def grid_geography(grid: Grid) -> str:
    """The geography whose Ember value a grid uses: its subdivision where it names one (US-VA, CN-GD), else its
    country."""
    return f"{grid['country']}-{grid['subdivision']}" if "subdivision" in grid else grid["country"]


def grid_intensity(grid: Grid, intensities: GridIntensities, scoring_year: int) -> GridIntensity:
    """A grid's intensity, as its intensity: field stores it: Ember's value for its geography for `scoring_year`
    (GRID_YEAR when scoring), or for its latest earlier year. A later year is never used.

    ValueError for an on-site grid (a facility's own generation, which no country or subdivision value describes) or a
    geography with no value for scoring_year or earlier; validation refuses both before any score."""
    if grid.get("supply") == "onsite":
        raise ValueError(f"grids/{grid['name']}.yaml: an on-site grid has no Ember value")
    geography = grid_geography(grid)
    by_year = intensities.get(geography, {})
    years = [year for year in by_year if year <= scoring_year]
    if not years:
        raise ValueError(
            f"grids/{grid['name']}.yaml: Ember has no intensity for {geography!r} in {scoring_year} or earlier"
        )
    year = max(years)
    return GridIntensity(g_per_kwh=by_year[year], year=year, geography=geography, source="Ember")


# The line above the intensity: field, at the end of each grid file.
GRID_EMISSIONS_COMMENT = (
    "# Written by `python -m build grid-emissions` from sources/snapshots/grid_intensity.csv. Everything below this line"
    " is rewritten by it; do not edit it by hand."
)


class GridRun(NamedTuple):
    errors: list[str]
    written: list[Path]


def grid_text(file_text: str, intensity: GridIntensity) -> str:
    """A grid file's text ending with GRID_EMISSIONS_COMMENT and its intensity:. Everything below the comment is
    replaced; everything above it is kept byte for byte (the file is never loaded and dumped)."""
    kept = file_text.partition(GRID_EMISSIONS_COMMENT)[0].rstrip()
    field = yaml.safe_dump({"intensity": dict(intensity)}, sort_keys=False, allow_unicode=True)
    return kept + "\n\n" + GRID_EMISSIONS_COMMENT + "\n" + field


def _grids_and_table(root: Path) -> tuple[list[str], dict[str, Grid], GridIntensities]:
    """The grid files that pass their schema, and Ember's table; the grids' schema errors."""
    data = load_sources(root)
    errors, grids = check_identity("grids", data.get("grids") or {}, TypeAdapter(CheckedGrid))
    table = root / GRID_INTENSITY_FILE
    if not table.exists():
        errors.append(f"{GRID_INTENSITY_FILE.as_posix()}: missing; run `python -m build import-ember`")
    return errors, grids, load_grid_intensities(table) if table.exists() else {}


def resolve(grids: Mapping[str, Grid], table: GridIntensities) -> tuple[list[str], dict[str, GridIntensity]]:
    """Each grid's intensity from Ember's table, by name; one error per grid that has none (on-site, or a geography
    Ember has no value for)."""
    errors: list[str] = []
    resolved: dict[str, GridIntensity] = {}
    for name, grid in sorted(grids.items()):
        try:
            resolved[name] = grid_intensity(grid, table, GRID_YEAR)
        except ValueError as error:
            errors.append(f"{error}; see docs/workflows/add-grid.md")
    return errors, resolved


def write_grid_emissions(root: Path, names: list[str] | None = None) -> GridRun:
    """python -m build grid-emissions: write the intensity: of each named grid (every grid when none is named) whose
    stored value would change. Writes nothing if there are errors."""
    errors, grids, table = _grids_and_table(root)
    unknown = sorted(set(names or []) - set(grids))
    errors += [f"grids/{name}.yaml: no such grid file" for name in unknown]
    if errors:
        return GridRun(errors, [])
    wanted = {name: grids[name] for name in (names or grids)}
    errors, resolved = resolve(wanted, table)
    if errors:
        return GridRun(errors, [])
    written = []
    for name in sorted(resolved):
        path = root / "sources" / "grids" / f"{name}.yaml"
        text = path.read_text(encoding="utf-8")
        new = grid_text(text, resolved[name])
        if new != text:
            path.write_text(new, encoding="utf-8")
            written.append(path)
    return GridRun([], written)


def check_grid_emissions(root: Path) -> GridRun:
    """python -m build check-grid-emissions: one message per grid whose stored intensity: is missing or differs from
    what grid-emissions would write now from the committed snapshot, naming what moved. Writes nothing."""
    errors, grids, table = _grids_and_table(root)
    if errors:
        return GridRun(errors, [])
    errors, resolved = resolve(grids, table)
    if errors:
        return GridRun(errors, [])
    messages = []
    for name in sorted(resolved):
        stored = grids[name].get("intensity")
        if stored is None:
            messages.append(
                f"grids/{name}.yaml: is missing the intensity field; run `python -m build grid-emissions {name}`"
            )
        elif stored != resolved[name]:
            moved = [key for key in resolved[name] if stored.get(key) != resolved[name][key]]
            messages.append(
                f"grids/{name}.yaml: its intensity is out of date ({', '.join(moved)}); "
                f"run `python -m build grid-emissions {name}`"
            )
    return GridRun(messages, [])
