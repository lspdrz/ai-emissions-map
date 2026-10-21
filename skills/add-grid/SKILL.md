---
name: add-grid
description: Use when `python -m build score` reports a cloud region or grid candidate with no file in sources/grids/, or a facility draws on its own generation. Adds the grid file with its zone and country.
---

# Add a grid

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-grid.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- A grid file is location only: zone, country, subdivision (US state or Chinese province), whether it is
  subdivided, its supply.
- Several zones can be added in parallel; one writer writes the files.

## Scripts to run
```bash
uv run python -m build grid-emissions --write <slug>   # writes the grid's intensity: from Ember's snapshot
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_score: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
Ember has no value for the country or subdivision; an on-site grid; a zone that does not match the facility.
