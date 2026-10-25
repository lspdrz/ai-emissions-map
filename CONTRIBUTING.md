# Contributing to the AI Emissions Map

All curation happens through pull requests that edit the YAML files in `sources/`. CI validates
every PR. The code is [MIT licensed](LICENSE); the license of the dataset has not been chosen yet.

## Quick start

```bash
uv sync
uv run python -m build score     # check sources/ and write the disclosure_rating: and carbon_intensity: fields your change moves
uv run python -m build release   # write web/data/data.json; commit everything both write
uv run pytest
```

No API keys are needed to edit sources or run validation.

## What to change, and how

Find your task in [`docs/README.md`](docs/README.md) and follow its workflow. In short:

| Path | What it holds |
|---|---|
| `sources/organizations/<slug>.yaml` | An organization |
| `sources/routes/<org>-<model>.yaml` | Where the organization serves one model, with evidence |
| `sources/grids/<slug>.yaml` | A grid routes draw from: its zone, country and subdivision (US state or Chinese province); its intensity is Ember's value for them |
| `sources/models/<slug>.yaml` | A model: its parameter counts, copied from EcoLogits (with its id) or curated with evidence |

Every location claim needs the organization's own publications as evidence, read and
quoted in `shows`. Press coverage is recorded for
context but never establishes a location. The rules are in [`docs/reference/`](docs/reference/).

## What not to commit

- Hand edits to the `intensity:`, `disclosure_rating:` and `carbon_intensity:` fields, or anything below the comments that mark them
  as generated: change the facts above them and run `python -m build grid-emissions --write` (for a grid) or
  `python -m build score`.

## Organizations on the map

If your organization is on the map and something is wrong or missing, open a
"Respond as a provider" issue. Corrections with evidence and new location disclosures are welcome.
