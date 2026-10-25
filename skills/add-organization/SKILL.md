---
name: add-organization
description: Use when an organization that serves AI models should be added to the AI Emissions Map and has no file in sources/organizations/ yet. Creates the organization record and checks for a serving-locations file; routes come from add-route.
---

# Add an organization

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-organization.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- Check for an existing record before creating one.
- Look for `https://<domain>/.well-known/ai-serving-locations.json`; if it exists, set
  `disclosure_url` and read it as the workflow describes.
- Offer to continue with `add-route` for each in-scope model.

## Scripts to run
```bash
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_intensity: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
Scope unclear; an organization that only forwards requests to other providers (an aggregator,
out of scope: add nothing); a serving-locations file that fails its schema. See the workflow's "Stop and escalate when".
