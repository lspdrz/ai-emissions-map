# AI Emissions Map

The AI Emissions Map estimates the emissions of AI **serving routes** (an organization serving a model) and rates how precisely each organization discloses where its routes run.

- **Carbon score**: the Software Carbon Intensity (SCI, ISO/IEC 21031) of generating 1,000 output tokens,
  `(E × I) + M`. Energy (E) and embodied hardware emissions (M) are estimated with EcoLogits from the model's
  parameter counts; grid intensity (I) is the annual consumption-based carbon intensity, with direct emission
  factors, of each grid the route may draw from.
- **Location disclosure rating**: A to D per route, generated from its cited location (A names the facility, B one
  grid, C several possible grids, D undisclosed). An organization's rating is the mean of its routes'.

Every input is curated as YAML in `sources/`, each claim with its evidence; the Python pipeline in `build/` computes
the scores and ratings and writes `web/data/data.json`.[^layout] A static site in `web/` presents the data at <https://ai-emissions-map.vercel.app>.

## Documentation

Start at [`docs/README.md`](docs/README.md), which routes each task to its workflow. The method is
in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Agents start at [`CLAUDE.md`](CLAUDE.md).

## Local development

### Requirements

- [uv](https://docs.astral.sh/uv/)
- [Node.js](https://nodejs.org/) 24

### Setup

```bash
git clone https://github.com/lspdrz/ai-emissions-map.git
cd ai-emissions-map

# The data pipeline
uv sync                              # install the Python dependencies
uv run python -m build score         # check sources/, write each route's and organization's scores and ratings
uv run python -m build release       # validate and write web/data/data.json
uv run pytest                        # run the tests

# The website
cd web
npm install
npm run dev                          # http://localhost:3000
```

## Adding sources

New organizations, routes, grids and models are added by pull request.

1. **Fork the repository** and set it up as above.
2. **Follow the workflow for your change.** [`docs/README.md`](docs/README.md) lists one per task: adding an
   organization, a route, a grid or a model. Each says which files to write and which sources count.
3. **Cite every claim.** Read each page yourself and quote the passage that supports the claim in `shows`, with
   the date you read it ([`docs/reference/evidence-and-freshness.md`](docs/reference/evidence-and-freshness.md)).
4. **Regenerate the results:** run `uv run python -m build score`, then `uv run python -m build release`. Never
   edit the generated `disclosure_rating` and `carbon_score` fields or `web/data/data.json` by hand.
5. **Check:** `uv run pytest` passes.
6. **Commit everything**: your files, the fields that the `score` command wrote and `web/data/data.json`.
7. **Open a pull request against `main`.** Describe what you added and the evidence for each source.

## License

MIT. See [`LICENSE`](LICENSE).

[^layout]: This project, especially the data-sourcing and format, was inspired by Current AI's [os-ai-map](https://github.com/currentai-org/os-ai-map).
