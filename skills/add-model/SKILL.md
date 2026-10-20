---
name: add-model
description: Use when a route serves a model with no record in sources/models/ (`build score` reports "has no sources/models/"). Writes a record with the parameter counts the developer publishes, cited, or, where the developer has not released the architecture, EcoLogits' estimate with its catalogue as the evidence.
---

# Add a model

A thin wrapper. The procedure lives in the workflow; this file does not restate it.

## Required reading
**Read `docs/workflows/add-model.md` and follow it.** Rules: `docs/reference/identity.md`.

## Agent orchestration
- The developer first: parameter counts from its own publications (card, weights, report), read yourself;
  never from memory.
- Only when the developer publishes none, EcoLogits' estimate: copied exactly from the installed catalogue (the
  workflow prints it), with the catalogue at the installed version as `corroborating` evidence. No other
  estimate stands in for the developer's figures.

## Scripts to run
```bash
uv run python -m build score     # checks, writes the disclosure_rating: and carbon_score: fields
uv run python -m build release   # writes web/data/data.json; commit everything both write
```

## Stop and escalate
Neither the developer nor EcoLogits gives the counts; unpublished architecture or active parameters; a
modified (for example quantized) variant whose counts are unclear; a record citing an older EcoLogits catalogue
than the installed one (that is an EcoLogits upgrade).
