# Contributing to the AI Emissions Map

All curation happens through pull requests that edit the YAML files in `sources/`. CI validates
every PR. The code is [MIT licensed](LICENSE); the license of the dataset has not been chosen yet.

## Quick start

```bash
uv sync
uv run python -m build.validate   # must print "0 error(s)"
uv run pytest -m "not ecologits and not browser"
```

No API keys are needed to edit sources or run validation.

## What to change, and how

Find your task in [`docs/README.md`](docs/README.md) and follow its workflow. In short:

| Path | What it holds |
|---|---|
| `sources/organizations/<slug>.yaml` | An organization, with the `routes:` roster it serves |
| `sources/routes/<org>-<model>.yaml` | Where the organization serves one model, with evidence |
| `sources/facilities/<slug>.yaml` | A physical data center, shared by every route served from it |
| `sources/models/<slug>.yaml` | Parameter counts for a model EcoLogits does not know |

Every location claim needs the organization's own publications as evidence, captured with
`uv run python -m build.fetch_source <url>` and quoted in `shows`. Press coverage is recorded for
context but never establishes a location. The rules are in [`docs/reference/`](docs/reference/).

## What not to commit

- `build/*.json`: generated outputs.
- Anything in `sources/snapshots/grid/` except its README. Grid data stays local to each
  maintainer.

## Organizations on the map

If your organization is on the map and something is wrong or missing, open a
"Respond as a provider" issue. Corrections with evidence, new location disclosures and response
statements of up to 300 words are all welcome.
