# Add an organization

## Use this when
An organization that serves models in the map's scope has no file in `sources/organizations/`. To
record where it serves a model, use [`add-route.md`](add-route.md) afterwards (or in the same PR).

## Inputs you need
- Its name and homepage, and the country where it is based, if that is clear.
- Its `type` (see [`../reference/identity.md`](../reference/identity.md#organizations)).
- A contact page for the pre-publication notice and right of reply.
- Whether it publishes a serving-locations file.

## Files this changes
1. `sources/organizations/<slug>.yaml`, new.
2. Route files and the roster, if you add routes in the same PR ([`add-route.md`](add-route.md)).

## Procedure
1. **Check it is not already there**, under its slug or as an alias:
   `ls sources/organizations/` and `grep -rn "<name>" sources/organizations/`.
2. **Pick the slug** per [`../reference/identity.md`](../reference/identity.md): lowercase
   kebab-case, naming the organization, not a product.
3. **Look for a serving-locations file** at `https://<domain>/.well-known/ai-serving-locations.json`.
   If one exists, record it as `disclosure_url`.
4. **Write the file.** New files may be written whole:
   ```yaml
   name: alpinehost
   display_name: Alpine Host
   type: inference_host
   homepage: https://alpinehost.example
   country: CH
   ids: { ossd: null, hf_provider: null, openrouter: null }
   contact: { url: https://alpinehost.example/contact, notified: null }
   routes: []
   ```
   `ids` holds the organization's names on Hugging Face's provider list and on OpenRouter where it
   has them. `notified` stays `null` until the pre-publication notice is sent.
5. **If it has a serving-locations file**, read it:
   `uv run python -m build.disclosure <disclosure_url> --org <slug>`.
   Its proposals feed [`add-route.md`](add-route.md).

## Validation
```bash
uv run python -m build.validate
```
It must print `0 error(s)`. The warning "has no routes and will not be rated" is expected until its
routes are added.

## Expected PR contents
The new organization file, plus any routes added with it. Nothing under `build/` or
`sources/snapshots/grid/`.

## Stop and escalate when
- You are not sure the organization is in the map's scope: ask the maintainer.
- It only resells other providers' endpoints: it is an `aggregator`, and its routes need
  `upstreams` (see [`../reference/location-disclosure.md`](../reference/location-disclosure.md#aggregator-routes)).
- The serving-locations file fails its schema: record nothing from it, and tell the maintainer.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md) ·
[`../reference/disclosure-formats.md`](../reference/disclosure-formats.md)
