# Add a route

## Use this when
You are recording where an organization serves a model. The organization must already have a record in
`sources/organizations/` ([`add-organization.md`](add-organization.md)), and the model must have a record in
`sources/models/` ([`add-model.md`](add-model.md)).

## Inputs you need
- The organization's slug, and the slug of the record in `sources/models/` for the model it **actually** serves.
- The organization's own pages that say where it serves that model, and, for any facility they name, the
  pages that give its PUE.

## Files this changes
1. `sources/routes/<org>-<model>.yaml`, new (with a qualifier for each location a customer can choose, step 6).
2. A new grid ([`add-grid.md`](add-grid.md)) or model ([`add-model.md`](add-model.md)), when the route
   needs one.

## Procedure
1. **Confirm the model served.** If the provider offers it under another name, record that name as
   `served_as` and add `served_model_evidence` showing they are the same model.
2. **Research the location, most authoritative first:** the organization's serving-locations file
   (read as in [`add-organization.md`](add-organization.md)); its documentation and region pages;
   its trust center, subprocessor list or data-processing agreement (often JavaScript-only: read it in a
   browser); its announcements. Press and analyst reports are corroborating only.
3. **Record every source you rely on:** read the page and quote, in `shows`, the passage that establishes the
   claim, inside double quotes; set `accessed` to today
   ([`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md)).
4. **Choose the candidates** per [`../reference/location-disclosure.md`](../reference/location-disclosure.md):
   the grids the route may draw from, as `cloud:<vendor>:<region>` (it must be in
   `sources/snapshots/cloud_regions.csv`) or `grid:<slug>` (a file in `sources/grids/`). When the primary
   evidence names the buildings, list each in `facilities:` by its `name`, in words, and give the grid they draw
   from as the candidate. Nobody writes the route's rating: `score` generates it from the candidates, their grids, the
   facilities and the evidence.
5. **Record each named facility's PUE**, when the route lists `facilities:`. Look, most authoritative first, in the
   organization's serving-locations file (a location's `pue`), then in the organization's and the facility
   operator's own pages (efficiency or sustainability pages, a live PUE dashboard's trailing twelve months). Record
   it on the facility as `pue:`:
   ```yaml
     facilities:
     - name: "Example Zurich 1, Zurich"
       pue:
         value: 1.18
         period_end: "2026-09-30"
         evidence:
         - url: https://example.com/datacenters/zurich-1
           shows: 'Zurich 1 efficiency page: "PUE 1.18 over the last 12 months"'
           accessed: "2026-10-11"
           kind: primary
   ```
   `period_end` is the last day of the twelve months the value covers (a calendar year's is its 31 December). Only
   a value measured over twelve months counts
   ([`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md#a-facilitys-pue)); record
   nothing for a facility without one. A cloud region's PUE is not researched: `score` reads it from
   `sources/snapshots/cloud_regions.csv`. `score` uses the published PUE only when every candidate has one, and the
   fallback range (1.1–1.6) otherwise.
6. **Write the route**, named `<org>-<model>` with the model part made into a slug per
   [`../reference/identity.md`](../reference/identity.md#routes) (`example-host` serving
   `example-lab/Example-Coder-13B-hf` is `example-host-example-coder-13b-hf`):
   ```yaml
   name: example-ai-example-70b
   org: example-ai
   model: example-70b
   location:
     facilities:
     - name: "Example Zurich 1, Zurich"
     candidates: ["grid:ch"]
     evidence:
     - url: https://example.com/docs/regions
       shows: 'Regions page: "example-70b is served exclusively from Example Zurich 1"'
       accessed: "2026-10-11"
       kind: primary
   ```
   Add `label:` under `location:` with where it runs in words, as a reader would say it.
   - **Nothing disclosed:** `candidates: []`, and any press coverage as `corroborating` evidence.
   - **Locations the customer can choose** (regional or jurisdictional endpoints): one route per
     choice, `<org>-<model>-<qualifier>`. Mark the one used unless the customer chooses otherwise
     with `default: true`; it is the route without a qualifier. A model served through more than one
     service puts the service's name first, `<org>-<model>-<service>[-<qualifier>]`
     ([`identity.md`](../reference/identity.md#routes)).

## Validation
Write the route's `disclosure_rating:` and `carbon_intensity:` and its organization's `disclosure_rating:`, then the
website's data:
```bash
uv run python -m build score
uv run python -m build release
```
`score` lists the files it wrote: the new route and its organization, each ending with those fields below a
comment saying they are generated (never edit below it); `release` writes `web/data/data.json`. Both must end
without `ERROR:` lines; commit everything they write. CI recomputes every stored carbon intensity and rejects a data file
that no longer matches `sources/`. If `score` reports a zone or grid with no grid file, follow
[`add-grid.md`](add-grid.md), then run both again.

## Expected PR contents
The route file, any grid (with the `intensity:` `grid-emissions` wrote) or model it needed, the `disclosure_rating:` and `carbon_intensity:` fields `score` wrote,
the organization's `disclosure_rating:`, and `web/data/data.json`. One short note per route on the evidence that
settled its candidates, and, for a route with facilities, on the PUE found for each or why there is none.

## Stop and escalate when
- Only the press says where it runs: record no candidates, and do not add any on press evidence.
- Two primary sources disagree: record both, describe the conflict in that evidence entry's `anomaly`, credit what is
  plainly disclosed, and tell the maintainer.
- The cloud region is not in `sources/snapshots/cloud_regions.csv`: do not invent a zone; ask the
  maintainer to refresh the table (see `sources/snapshots/README.md`).
- The provider lets customers choose where requests run, but has no default you can identify:
  record every choice as a route and ask the maintainer which one, if any, to mark
  `default: true` (see [`../reference/identity.md`](../reference/identity.md#routes)).

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
