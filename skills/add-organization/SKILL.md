---
name: add-organization
description: Use when an organization that serves AI models should be added to the AI Emissions Map and has no file in sources/organizations/ yet. Creates the organization record and checks for a serving-locations file; routes come from add-route.
---

# Add an organization

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-organization.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- Check for an existing record and aliases before creating one.
- Look for `https://<domain>/.well-known/ai-serving-locations.json`; if it exists, set
  `disclosure_url` and run `build.disclosure` on it.
- Offer to continue with `add-route` for each in-scope model.

## Scripts to run
```bash
uv run python -m build.disclosure <url> --org <slug>   # only if it publishes a file
uv run python -m build.validate
```

## Stop and escalate
Scope unclear; an organization that only resells others' endpoints (an aggregator); a
serving-locations file that fails its schema. See the workflow's "Stop and escalate when".
