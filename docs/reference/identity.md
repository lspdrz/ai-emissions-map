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

The `<model>` part is the model's id made into a slug. A `sources/models/` slug is used as it is.
An EcoLogits id is reduced to its last path segment (the repository name, without the owner),
lowercased, with every character outside `a-z0-9` turned into a hyphen and repeated hyphens
collapsed: `meta-llama/CodeLlama-13b-hf` served by `together` is `together-codellama-13b-hf`. If two
of an organization's models would give the same slug, keep the owner as well
(`together-meta-llama-codellama-13b-hf`).

- `model` is the model actually served: an EcoLogits catalogue id or a `sources/models/` slug. If
  the provider offers it under another name, `served_as` records that name and
  `served_model_evidence` shows the two are the same model.
- One route per organization and model. Where the location is uncertain across several places,
  those places are candidates on one route, not separate routes. A different default location that
  a customer can choose (a pinnable region) is a separate route with a qualifier:
  `<org>-<model>-<qualifier>`.
- An aggregator's route has `upstreams` (other organizations' routes serving the same model)
  instead of a location.

## Facilities

`sources/facilities/<slug>.yaml` is one physical data center or campus, shared by every route
served from it. Its slug is `<operator>-<site>`. There is one record per unit with a distinct grid
zone. `operator` is whoever runs the building (an organization slug where it has one); tenants are
not listed, because they follow from the routes that cite the facility.

## Models

`sources/models/<slug>.yaml` exists only for a model EcoLogits lacks, or where the developer's own
model card contradicts EcoLogits. A curated file takes precedence over an EcoLogits entry with the
same id, so it can only shadow an EcoLogits id that is itself kebab-case.

## Dates

Dates are ISO 8601 strings, quoted in YAML (`"2026-10-11"`). The schemas reject unquoted dates,
which YAML would otherwise read as date objects.
