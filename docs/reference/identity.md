# Identity

How records are named, how they refer to each other, and how a name is retired. The JSON Schemas in
[`../schemas/`](../schemas/) define every field; `build.validate` enforces everything below.

## One record, one file, one slug

- Every curated record is one YAML file, `sources/<kind>/<slug>.yaml`, where `<kind>` is
  `organizations`, `facilities`, `routes` or `models`.
- The filename stem is the slug, and the record's `name` must equal it. Slugs are lowercase
  kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Only `<slug>.yaml` files belong in those directories; any other file, or a subfolder, is a load
  error. Dotfiles are ignored.
- There are no UUIDs. The slug is the identity.

## Renaming and retiring

A slug is permanent once published. To rename a record, create the file under the new slug, list
the old slug in its `aliases:`, and remove the old file. An alias may not be the live slug of
another record, and no two records may claim the same alias. A route that is no longer served is
retired the same way: its slug moves into the `aliases:` of the route that replaced it. If nothing
replaced it, stop and ask the maintainer.

## Organizations

`sources/organizations/<slug>.yaml`. The slug names the organization as a provider of AI serving
(`infomaniak`, `together`), not one of its products. `type` is one of:

| `type` | Meaning |
|---|---|
| `model_lab` | Develops models and serves them through its own API |
| `inference_host` | Serves models that others developed |
| `cloud` | A general cloud platform that offers model APIs |
| `public_compute` | A publicly funded compute center |
| `aggregator` | Routes requests to other providers' routes |

Every organization carries a `routes:` roster listing the routes it serves.

## Routes

A route is one organization serving one model. Its slug is `<org>-<model>`
(`infomaniak-apertus-70b`), and it appears on exactly one `routes:` roster: that of the
organization whose slug begins it. A route on no roster or on two, or a roster entry with no file,
is an error.

The `<model>` part is the slug of the model's record in `sources/models/`
(`together-codellama-13b-hf` serves the model recorded as `codellama-13b-hf`). If two of an
organization's models would give the same route slug, keep the model's owner as well
(`together-meta-llama-codellama-13b-hf`).

- `model` is the model actually served: the slug of its record in `sources/models/`. If
  the provider offers it under another name, `served_as` records that name and
  `served_model_evidence` shows the two are the same model.
- `location.label` is optional: where the route runs, in words for readers ("United States (9
  regions)"). Without it the site shows a count of grid zones.
- One route per organization and model. Where the location is uncertain across several places,
  those places are candidates on one route, not separate routes. Where the customer can choose
  among several locations (regional or jurisdictional endpoints), each choice is a separate route
  with a qualifier, `<org>-<model>-<qualifier>` (for example `-eu`, `-de`), and the route used
  unless the customer chooses otherwise carries `default: true`. At most one route per
  organization and model is the default. The label is for readers: every route counts in the
  organization's rating.
- An aggregator's route has `upstreams` (other organizations' routes serving the same model)
  instead of a location.

## Facilities

`sources/facilities/<slug>.yaml` is one physical data center or campus, shared by every route
served from it. Its slug is `<operator>-<site>`. There is one record per unit with a distinct grid
zone. `operator` is whoever runs the building (an organization slug where it has one); tenants are
not listed, because they follow from the routes that cite the facility.

## Models

Every model a route serves has a record, `sources/models/<slug>.yaml`, so the parameter counts
behind every score are visible in the repository. A record says where its numbers come from:

- **`source: ecologits`**, the default whenever EcoLogits has the model. The record copies the
  pinned EcoLogits package (`ecologits: {id, version}`, architecture, parameter counts), is written
  by `python -m build.models --add <ecologits id>`, and needs no evidence. `build.validate` checks
  it still matches the installed package, so upgrading EcoLogits shows every changed model as a
  diff (`python -m build.models --sync` applies it).
- **`source: curated`**, for a model EcoLogits lacks, or whose developer's own model card
  contradicts EcoLogits. Its counts come from the developer, with evidence.

A record's slug is the EcoLogits id's last path segment (the repository name, without the owner),
lowercased, with every character outside `a-z0-9` turned into a hyphen and repeated hyphens
collapsed (`meta-llama/CodeLlama-13b-hf` → `codellama-13b-hf`, `gemini-3.5-flash` →
`gemini-3-5-flash`); a curated model's slug is its developer's name for it, formed the same way.

## Dates

Dates are ISO 8601 strings, quoted in YAML (`"2026-10-11"`). The schemas reject unquoted dates,
which YAML would otherwise read as date objects.
