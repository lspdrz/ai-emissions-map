---
name: refresh-organization
description: Use when an organization's source is reported changed or gone, or when an organization reports a change. Re-reads its routes' sources and corrects the claims that no longer hold.
---

# Refresh an organization

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/refresh-organization.md` and follow it.** Rules:
`docs/reference/evidence-and-freshness.md`.

## Agent orchestration
- Read each page yourself and check the quoted passage is still there; never guess from memory.
- A claim that no longer holds is downgraded to what the remaining primary evidence supports.

## Scripts to run
```bash
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_intensity: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
A change that would lower the organization's rating; a source contradicting a published claim.
