# AI Emissions Map

Carbon scores for AI serving routes (EcoLogits energy × grid carbon intensity read from published sources, plus
EcoLogits embodied emissions) and location-disclosure ratings for the organizations that run them.
The layout follows [os-ai-map](https://github.com/currentai-org/os-ai-map): curated YAML in `sources/`,
imported data in `sources/snapshots/`, record types in `build/schemas/`, code in `build/`.

## Documentation

Start at [`docs/README.md`](docs/README.md), which routes each task to its workflow. The method is
in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Agents start at [`CLAUDE.md`](CLAUDE.md).

## Commands

    uv sync
    uv run pytest                          # all tests
    uv run ruff check && uv run lint-imports   # import rules for build/ (see pyproject.toml)
    uv run ruff format                         # one formatting, 120 columns (checked in CI)
    uv run pyright                             # type checks for build/ and tests/
    uv run python -m build score             # check sources/, write the disclosure_rating: and carbon_score: fields
    uv run python -m build release           # validate and write web/data/data.json; commit both commands' output

## Imported data (`sources/snapshots/`)

Each snapshot has a `.provenance.json` beside it: where it came from, when, and under what licence.

- `cloud_regions.csv` (committed): cloud region -> grid zone, a pinned copy of the Green Software
  Foundation's real-time-cloud table, refreshed by hand as `sources/snapshots/README.md` describes.

Grid intensities are not imported: each grid a route uses has a curated file in `sources/grids/`, its values
read from published pages with evidence; see `docs/workflows/add-grid.md`.

## Evidence

Each evidence entry is the page's `url`, the passage it shows quoted in `shows` (in double quotes), the date it
was read (`accessed`) and its `kind`; see `docs/reference/evidence-and-freshness.md`.
Organizations can publish where they serve each model as a serving-locations file
(`docs/serving-locations/`, suggested at `/.well-known/ai-serving-locations.json`).
