---
name: refresh-organization
description: Use when a release is coming, when validate warns that an organization's location evidence is stale, or when an organization reports a change. Re-verifies its routes' and facilities' sources and re-dates the claims that still hold.
---

# Refresh an organization

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/refresh-organization.md` and follow it.** Rules:
`docs/reference/evidence-and-freshness.md`.

## Agent orchestration
- Dry run first, then `--write`; `build.reverify` re-dates only claims whose primary sources all
  confirm.
- Every `HELD` source needs a person's judgment: recapture, downgrade, or escalate.

## Scripts to run
```bash
uv run python -m build.reverify --org <slug>
uv run python -m build.reverify --org <slug> --write
uv run python -m build.validate --release-date <next release date>
```

## Stop and escalate
A change that would lower the organization's rating; a source contradicting a published claim.
