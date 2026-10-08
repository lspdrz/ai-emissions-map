# AI Emissions Map

Carbon scores for AI serving routes (EcoLogits energy × Electricity Maps grid intensity, plus EcoLogits
embodied emissions) and location-disclosure ratings for the organizations that run them.
The layout follows [os-ai-map](https://github.com/currentai-org/os-ai-map): curated YAML in `sources/`,
JSON Schemas in `docs/schemas/`, code in `build/`.

## Commands

    uv sync
    uv run pytest                          # all tests (add -m "not ecologits" to skip the real EcoLogits runs)
    uv run python -m build.validate        # validate sources/ (must print "0 error(s)")
    uv run python -m build.serialize --release-date 2026-10-08   # sources/ -> build/routes.json, build/organizations.json

Grid snapshots (`sources/snapshots/grid/*.csv`) and cloud regions (`sources/cloud_regions.csv`) come from the
ingestion step (Plan 2). Until then, run `build.serialize` with `--grid` and `--cloud` pointing at prepared CSVs.
Do not commit `build/*.json`; they are generated.
