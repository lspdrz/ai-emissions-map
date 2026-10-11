---
name: add-facility
description: Use when a route's primary evidence names a specific data center that has no record in sources/facilities/. Adds the shared facility record (operator, ownership, grid zone) with primary evidence.
---

# Add a facility

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-facility.md` and follow it.** Rules: `docs/reference/identity.md`,
`docs/reference/evidence-and-freshness.md`.

## Agent orchestration
- Search `sources/facilities/` first: facilities are shared between tenants.
- Capture the operator's own page with `build.fetch_source` (`--browser` for JavaScript-only
  pages) and write `shows` yourself, quoting the page exactly.

## Scripts to run
```bash
uv run python -m build.fetch_source <url>
uv run python -m build.validate
```

## Stop and escalate
Press-only evidence; a site spanning two grid zones; an unknown operator.
