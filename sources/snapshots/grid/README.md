# Grid intensity (local only)

This directory holds the yearly grid carbon-intensity snapshots that `build.serialize` reads
(`<year>.csv`, with `<year>.provenance.json` beside it). **Nothing in it except this README is committed**:
`.gitignore` excludes every other file, whether real or mock.

The data comes from Electricity Maps. Its free historical datasets are published under the ODbL, but
this project does not redistribute Electricity Maps data in its repository. Each maintainer obtains it
under their own access and imports it locally:

    uv run python -m build.import_grid --year <year> --retrieved <download date> <yearly CSVs, one per zone>

A file named `*.MOCK.csv` is a placeholder made for development, not Electricity Maps data; its
provenance file says `"mock": true` and how it was made.
