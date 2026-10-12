# Add a route

## Use this when
You are recording where an organization serves a model. The organization must already exist
([`add-organization.md`](add-organization.md)), and the model must be in EcoLogits or
`sources/models/` ([`add-model.md`](add-model.md)).

## Inputs you need
- The organization's slug and the id of the model it **actually** serves.
- The organization's own pages that say where it serves that model.

## Files this changes
1. `sources/routes/<org>-<model>.yaml`, new.
2. `sources/organizations/<org>.yaml`: the route's slug added to `routes:`.
3. A new facility ([`add-facility.md`](add-facility.md)) or model ([`add-model.md`](add-model.md)),
   when the route needs one.

## Procedure
1. **Confirm the model served.** If the provider's name for it differs from the model id, record
   the name as `served_as` and add `served_model_evidence` showing they are the same model.
2. **Research the location, most authoritative first:** the organization's serving-locations file
   (`uv run python -m build.disclosure <url> --org <org>`); its documentation and region pages;
   its trust center, subprocessor list or data-processing agreement (often JavaScript-only: use
   `--browser`); its announcements. Press and analyst reports are corroborating only.
3. **Capture every source you rely on** with `uv run python -m build.fetch_source <url>`, paste the
   entry, and write `shows`, quoting the exact passage in double quotes
   ([`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md)).
4. **Choose the candidates and the confidence** per
   [`../reference/location-disclosure.md`](../reference/location-disclosure.md):
   `facility:<slug>`, `cloud:<vendor>:<region>` (it must be in
   `sources/snapshots/cloud_regions.csv`) or `zone:<code>`. The confidence is the level the
   primary evidence establishes for the least precise candidate.
5. **Write the route**, named `<org>-<model>` with the model part made into a slug per
   [`../reference/identity.md`](../reference/identity.md#routes) (`together` serving
   `meta-llama/CodeLlama-13b-hf` is `together-codellama-13b-hf`), with `last_verified` set to today:
   ```yaml
   name: alpinehost-test-70b
   model: test-70b
   location:
     confidence: facility
     candidates: ["facility:alpinehost-alp-1"]
     last_verified: "2026-10-11"
     evidence:
     - url: https://alpinehost.example/docs/regions
       shows: 'Regions page: "test-70b is served exclusively from ALP-1"'
       accessed: "2026-10-11"
       http_status: 200
       content_sha256: <from fetch_source>
       kind: primary
       capture: auto
   ```
   - **Nothing disclosed:** `confidence: unknown`, `candidates: []`, and any press coverage as
     `corroborating` evidence.
   - **Aggregator:** replace `location` with `upstreams` (routes serving the same model, each
     with a positive `weight`) and primary `upstream_evidence`.
   - **Locations the customer can choose** (regional or jurisdictional endpoints): one route per
     choice, `<org>-<model>-<qualifier>`. Mark the one used unless the customer chooses otherwise
     with `default: true`; usually it is the route without a qualifier.
6. **Add the slug to the organization's `routes:` list.** Edit the text in place. Never load the
   YAML and dump it back, which would destroy comments and layout.

## Validation
```bash
uv run python -m build.validate
uv run python -m build.validate --release-date <next release date>
```
Both must print `0 error(s)`; the second also warns if the evidence would be stale by then. With a
local grid file you can preview the score:
`uv run python -m build.serialize --release-date <date>` writes `build/routes.json`. Never commit
it, and never publish numbers built from a `*.MOCK.csv` grid file.

## Expected PR contents
The route file, the one-line roster change, and any facility or model it needed. One short note
per route on the evidence that settled its confidence.

## Stop and escalate when
- Only the press says where it runs: record `unknown`, and do not upgrade it on press evidence.
- Two primary sources disagree: record both, describe the conflict in `anomaly`, credit what is
  plainly disclosed, and tell the maintainer.
- The cloud region is not in `sources/snapshots/cloud_regions.csv`: do not invent a zone; ask the
  maintainer to update the import.
- The provider lets customers choose where requests run, but has no default you can identify:
  record every choice as a route and ask the maintainer which one, if any, to mark
  `default: true` (see [`../reference/identity.md`](../reference/identity.md#routes)).

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md) ·
[`../reference/disclosure-formats.md`](../reference/disclosure-formats.md)
