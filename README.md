# AI Emissions Map

Carbon scores for AI serving routes (EcoLogits energy × Electricity Maps grid intensity, plus EcoLogits
embodied emissions) and location-disclosure ratings for the organizations that run them.
The layout follows [os-ai-map](https://github.com/currentai-org/os-ai-map): curated YAML in `sources/`,
imported data in `sources/snapshots/`, JSON Schemas in `docs/schemas/`, code in `build/`.

## Documentation

Start at [`docs/README.md`](docs/README.md), which routes each task to its workflow. The method is
in [`docs/methodology.md`](docs/methodology.md). Agents start at [`CLAUDE.md`](CLAUDE.md).

## Commands

    uv sync
    uv run pytest                          # all tests (-m "not ecologits and not browser" for the fast loop)
    uv run python -m build.validate        # validate sources/ (must print "0 error(s)")
    uv run python -m build.serialize --release-date 2026-10-08   # sources/ -> build/routes.json, build/organizations.json

Do not commit `build/*.json`; they are generated.

## Models

    uv run python -m build.models --add <ecologits id>   # a model record copied from the pinned EcoLogits
    uv run python -m build.models --sync                 # after upgrading EcoLogits: update every record

## Imported data (`sources/snapshots/`)

Each import writes a `.provenance.json` beside its data: where it came from, when, and a content hash.
Grid-intensity snapshots (`sources/snapshots/grid/`) stay local and are never committed: we do not
redistribute Electricity Maps data in this repository (see `sources/snapshots/grid/README.md`).

    # Grid intensity: download the yearly, consumption-based CSVs (one per zone) from the Electricity Maps
    # data portal (free account, ODbL), then:
    uv run python -m build.import_grid --year 2025 --retrieved <download date> ~/Downloads/*_2025_yearly.csv
    # Cloud region -> grid zone, from the Green Software Foundation real-time-cloud repository, pinned:
    uv run python -m build.import_cloud_regions --commit <sha>

## Evidence

    uv run python -m build.fetch_source <url>                  # evidence entry to paste; write `shows` yourself
    uv run python -m build.fetch_source --browser <url>        # pages that only render with JavaScript
    uv run python -m build.fetch_source --manual page.html --url <url>   # a page you saved by hand
    uv run python -m build.reverify [--org <slug>] [--oldest N] [--write]   # re-fetch evidence, re-date what holds
    uv run python -m build.disclosure <url-or-file> [--org <slug>]       # read a serving-locations file

`shows` quotes the page in double quotes; re-verification looks for those quoted passages when a page's
bytes have changed. Browser capture needs `uv sync --group browser && uv run playwright install chromium`.
Organizations can publish where they serve each model as a serving-locations file
(`docs/schemas/serving-locations.v1.schema.json`, suggested at `/.well-known/ai-serving-locations.json`).
