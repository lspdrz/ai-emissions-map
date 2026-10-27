---
name: add-route
description: Use when recording where an organization serves a model on the AI Emissions Map — researching its primary sources, capturing evidence, choosing the grids it may draw from, and writing the route file.
---

# Add a route

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-route.md` and follow it.** Rules:
`docs/reference/location-disclosure.md`, `docs/reference/evidence-and-freshness.md`,
`docs/reference/identity.md`.

## Agent orchestration
- Research is targeted: find the organization's own pages; press is corroborating only.
- Read every source yourself and quote it exactly in `shows`, in double quotes; never quote from
  memory.
- Needs a grid or a model that does not exist yet → `add-grid` / `add-model` first.
- Names facilities → look for each one's PUE measured over twelve months (workflow step 5); a design figure, best
  month or fleet average goes in the comments, not in `pue:`.

## Scripts to run
```bash
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_intensity: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
Press-only location; conflicting primary sources; a cloud region missing from
`sources/snapshots/cloud_regions.csv`; different defaults per customer.
