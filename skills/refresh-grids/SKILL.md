---
name: refresh-grids
description: Use when a new year of grid data is published and the map should move to it. Adds the year to every file in sources/grids/, then moves GRID_YEAR and rescores.
---

# Refresh the grids

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/refresh-grids.md` and follow it.** Values are read as `docs/workflows/add-grid.md` says.

## Agent orchestration
- Edit each grid file in place, as text; keep the earlier years.
- Move `GRID_YEAR` in its own commit, after the values, with the tests' year (the workflow says which).

## Scripts to run
```bash
uv run python -m build score
uv run python -m build release   # commit everything both write
```

## Stop and escalate
A value that moves by more than 30% from the year before; fewer than half the grids with the new year.
