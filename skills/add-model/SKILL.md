---
name: add-model
description: Use when a route serves a model with no record in sources/models/ (validate reports "has no sources/models/"). Writes the record from EcoLogits with build.models --add, or a curated record with cited counts when EcoLogits lacks the model or its model card contradicts EcoLogits.
---

# Add a model

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-model.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- EcoLogits first: if the catalogue has the model, write the record with `build.models --add`;
  never type its numbers by hand.
- Only a model EcoLogits lacks, or one its developer's model card contradicts, gets a curated
  record, with parameter counts from that card; never from memory.

## Scripts to run
```bash
uv run python -m build.models --add <ecologits id>
uv run python -m build.fetch_source <model card url>   # curated records only
uv run python -m build.validate
```

## Stop and escalate
Unpublished architecture or active parameters; a modified (for example quantized) variant whose
counts are unclear; an EcoLogits record reported out of date (that is an EcoLogits upgrade).
