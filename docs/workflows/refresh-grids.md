# Refresh the grids

## Use this when
A new year of grid data is published and the map should move to it. Every score uses one year,
`GRID_YEAR` in `build/constants/config.py`; a grid without a consumption-based direct value for that year uses
its latest earlier one, flagged on its routes when it is more than `MAX_GRID_AGE` (2) years older.

## Inputs you need
- The new year's consumption-based direct values (and their life-cycle figures, where published) for every file in
  `sources/grids/`, read as
  [`add-grid.md`](add-grid.md) steps 3 to 5 say.

## Files this changes
1. Every `sources/grids/<slug>.yaml`: a new year under `values`.
2. `build/constants/config.py`: `GRID_YEAR`, and the tests that assume it (below).
3. Every route and organization file whose `disclosure_rating:` or `carbon_score:` moves, and `web/data/data.json`.

## Procedure
1. **Add the new year to each grid file**, under `values`, as [`add-grid.md`](add-grid.md) steps 3 to 5 say. A
   value published for a fiscal year is keyed by the calendar year holding most of its months, the year it ends on
   a tie.
   Keep the earlier years: they are the fallback, and the record of what earlier releases used.
2. **Move `GRID_YEAR`** in `build/constants/config.py` once most grids have the new year. Grids still without
   it keep their latest earlier value, flagged on their routes once it is more than `MAX_GRID_AGE` years older.
   Move the tests' year with it, in the same commit:
   `tests/builders/grid.py` writes its values for the current year, and the tests of grid values, flags and the
   scoring year (`tests/test_carbon_score.py`, `tests/constants/test_config.py`, among others) expect it; run
   `uv run pytest` to find every one.
3. **Say in the PR that scores move** with the new data.

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` rewrites every route whose score moved; `release` rewrites `web/data/data.json`. Both must end without
`ERROR:` lines; commit everything they write. A new year moves almost every score: open it as its own pull
request.

## Expected PR contents
The grid files, the `GRID_YEAR` change, every `disclosure_rating:` and `carbon_score:` field that moved, `web/data/data.json`.

## Stop and escalate when
- A grid's new value moves by more than 30% from the year before: check the source, and tell the maintainer.
- Fewer than half the grids have the new year: wait before moving `GRID_YEAR`.

## Relevant reference material
[`add-grid.md`](add-grid.md) ·
[`../METHODOLOGY.md`](../METHODOLOGY.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md)
