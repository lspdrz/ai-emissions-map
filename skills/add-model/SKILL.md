---
name: add-model
description: Use when a route serves a model missing from EcoLogits' catalogue (validate reports "not in EcoLogits or sources/models/"), or a model card contradicts the catalogue's parameter counts. Adds sources/models/<slug>.yaml with cited counts.
---

# Add a model

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-model.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- Check the EcoLogits catalogue before adding anything.
- Take parameter counts from the developer's own model card; never from memory.

## Scripts to run
```bash
uv run python -m build.fetch_source <model card url>
uv run python -m build.validate
```

## Stop and escalate
Unpublished architecture or active parameters; a modified (for example quantized) variant whose
counts are unclear.
