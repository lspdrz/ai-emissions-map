# Add an organization

## Use this when
An organization that serves models in the map's scope has no file in `sources/organizations/`. To
record where it serves a model, use [`add-route.md`](add-route.md) afterwards (or in the same PR).

## Inputs you need
- Its name and homepage, and the country where it is based, if that is clear.
- Its `type` (see [`../reference/identity.md`](../reference/identity.md#organizations)).
- A contact page.
- Whether it publishes a serving-locations file.

## Files this changes
1. `sources/organizations/<slug>.yaml`, new.
2. Route files, if you add routes in the same PR ([`add-route.md`](add-route.md)).

## Procedure
1. **Check it is not already there**, under its slug or another name:
   `ls sources/organizations/` and `grep -rn "<name>" sources/organizations/`.
2. **Pick the slug** per [`../reference/identity.md`](../reference/identity.md): lowercase
   kebab-case, naming the organization, not a product.
3. **Look for a serving-locations file** at `https://<domain>/.well-known/ai-serving-locations.json`.
   If one exists, record it as `disclosure_url`.
4. **Write the file.** New files may be written whole:
   ```yaml
   name: example-ai
   display_name: Example AI
   type: inference_host
   homepage: https://example.com
   country: CH
   ids: { ossd: null, hf_provider: null, openrouter: null }
   contact: { url: https://example.com/contact }
   ```
   `ids` holds the organization's names on Hugging Face's provider list and on OpenRouter where it
   has them.
   Add `description:`, one or two plain sentences on what it discloses about where it serves.
5. **If it has a serving-locations file**, fetch it and check it against
   [`../serving-locations/serving-locations.v1.schema.json`](../serving-locations/serving-locations.v1.schema.json) by
   reading it. For each model, each `routing` entry is one route: the one marked `"default": true` is
   `<org>-<model>` with `default: true`, and every other entry is `<org>-<model>-<name>`. Its `locations` give the route's candidates: named facilities go in
   `facilities:` with the grid they draw from, cloud regions become `cloud:` candidates, and grid zones `grid:`
   candidates.
   Write the routes with [`add-route.md`](add-route.md), citing the file as primary evidence.

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` writes the organization's `disclosure_rating:`; `release` writes `web/data/data.json`. Both must end without `ERROR:` lines; commit everything they write.
An organization with no routes yet has no rating.

## Expected PR contents
The new organization file, plus any routes and grids added with it. Nothing under `build/`; the files `score`
and `release` wrote are included.

## Stop and escalate when
- You are not sure the organization is in the map's scope: ask the maintainer.
- It only forwards requests to other providers (an aggregator): it is out of scope;
  add nothing.
- The serving-locations file fails its schema: record nothing from it, and tell the maintainer.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
