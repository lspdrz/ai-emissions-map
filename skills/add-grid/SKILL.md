---
name: add-grid
description: Use when `python -m build score` reports a cloud region or grid candidate with no file in sources/grids/, or a facility draws on its own generation. Adds the grid file with its yearly consumption-based direct intensity, read from a published page with evidence.
---

# Add a grid

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-grid.md` and follow it.** Rules: `docs/reference/identity.md`,
`docs/reference/evidence-and-freshness.md`.

## Agent orchestration
- Search published pages first: the grid operator, the national agency, open datasets. Read each page and quote
  the number exactly in `shows`.
- Never open Electricity Maps' site; when no page gives a consumption-based direct value, stop and tell the maintainer.
- Several zones can be researched in parallel; one writer writes the files.

## Scripts to run
```bash
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_score: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
No published consumption-based direct value; sources that disagree by more than 10%; a zone that does not match the facility.
