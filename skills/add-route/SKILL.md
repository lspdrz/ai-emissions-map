---
name: add-route
description: Use when recording where an organization serves a model on the AI Emissions Map — researching its primary sources, capturing evidence, choosing location confidence and candidates, and adding the route to the organization's roster.
---

# Add a route

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-route.md` and follow it.** Rules:
`docs/reference/location-disclosure.md`, `docs/reference/evidence-and-freshness.md`,
`docs/reference/identity.md`.

## Agent orchestration
- Research is targeted: find the organization's own pages; press is corroborating only.
- Capture every source with `build.fetch_source`, and write each `shows` by hand, quoting the page
  exactly in double quotes.
- Edit the organization's `routes:` list in place; never load and re-dump a file in `sources/`.
- Needs a facility or a model that does not exist yet → `add-facility` / `add-model` first.

## Scripts to run
```bash
uv run python -m build.disclosure <url> --org <org>    # if the organization publishes a file
uv run python -m build.fetch_source [--browser] <url>
uv run python -m build.validate
uv run python -m build.validate --release-date <next release date>
```

## Stop and escalate
Press-only location; conflicting primary sources; a cloud region missing from
`sources/snapshots/cloud_regions.csv`; different defaults per customer.
