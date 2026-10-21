"""A grid's carbon intensity: Ember's yearly value for the grid's subdivision (a US state, a Chinese province) or else
its country, from the committed snapshot sources/snapshots/grid_intensity.csv. `python -m build score` writes it at the
end of each grid file as its `intensity:` field, and every route's carbon score reads it from there.
"""

from __future__ import annotations

from collections.abc import Mapping

from build.schemas.grid import Grid, GridIntensity

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
