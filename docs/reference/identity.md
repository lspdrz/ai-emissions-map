# Identity

How records are named and how they refer to each other. The types in
[`build/schemas/`](../../build/schemas/) define every field; `build score` enforces everything below.

## One record, one file, one slug

- Every curated record is one YAML file, `sources/<kind>/<slug>.yaml`, where `<kind>` is
  `organizations`, `grids`, `routes` or `models`.
- The filename stem is the slug, and the record's `name` must equal it. Slugs are lowercase
  kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Only `<slug>.yaml` files belong in those directories; any other file, or a subfolder, is a load
  error. Dotfiles are ignored.
- There are no UUIDs. The slug is the identity.

## Renaming and retiring

A slug is permanent once published. To rename a record, or to retire one (a route that is no
longer served, for example), stop and ask the maintainer.

## Organizations

`sources/organizations/<slug>.yaml`. The slug names the organization as a provider of AI serving
(`infomaniak`, `together`), not one of its products. `type` is one of:

| `type` | Meaning |
|---|---|
| `model_lab` | Develops models and serves them through its own API |
| `inference_host` | Serves models that others developed |
| `cloud` | A general cloud platform that offers model APIs |
| `public_compute` | A publicly funded compute center |

## Routes

A route is one organization serving one model. Its slug is `<org>-<model>`
(`infomaniak-apertus-70b`), and its `org:` field names the organization that serves it, whose slug
begins the route's. A route without `org:`, or naming an organization with no file, is an error.
An organization's routes are the routes that name it.

The `<model>` part is the slug of the model's record in `sources/models/`
(`together-codellama-13b-hf` serves the model recorded as `codellama-13b-hf`). If two of an
organization's models would give the same route slug, keep the model's owner as well
(`together-meta-llama-codellama-13b-hf`).

- `model` is the model actually served: the slug of its record in `sources/models/`. If
  the provider offers it under another name, `served_as` records that name and
  `served_model_evidence` shows the two are the same model.
- `location.label` is optional: where the route runs, in words for readers ("United States (9
  regions)"). Without it the site shows a count of the grids it resolves to.
- One route per organization and model. Where the location is uncertain across several places,
  those places are candidates on one route, not separate routes. Where the customer can choose
  among several locations (regional or jurisdictional endpoints), each choice is a separate route
  with a qualifier, `<org>-<model>-<qualifier>` (for example `-eu`, `-de`), and the route used
  unless the customer chooses otherwise carries `default: true` and has no qualifier. Where the
  organization serves the model through more than one service, the service's name comes first,
  `<org>-<model>-<service>[-<qualifier>]` (`google-gemini-3-5-flash-vertex`,
  `google-gemini-3-5-flash-vertex-eu`). At most one route per
  organization and model is the default. The label is for readers: every route counts in the
  organization's rating.

## Grids

`sources/grids/<slug>.yaml` is one grid a route may draw from, shared by every route on it. For a public grid
the slug is its zone code in lower case (`US-CAL-CISO` is `us-cal-ciso`), and `zone:` holds the code itself,
which cloud regions resolve through; no two grid files claim one zone. A facility that runs on its own
generation has an on-site grid, `<operator>-<site>-onsite`, with `supply: onsite` and no `zone`. Facilities
themselves have no record: a route names its buildings in `location.facilities`.

## Models

Every model a route serves has a record, `sources/models/<slug>.yaml`, so the parameter counts
behind every score are visible in the repository, each with evidence for where they come from:

- **From the developer**, whenever the developer publishes them: its model card, the published weights, its
  report or announcement, cited as `primary`.
- **From EcoLogits' estimate**, only where the developer has not released the architecture (EcoLogits marks
  the model `model-arch-not-released`): the counts are copied from its catalogue, which is cited at the
  installed version as `corroborating`.

A record's slug is the developer's name for the model (for a model on Hugging Face, its repository name without
the owner), lowercased, with every character outside `a-z0-9` turned into a hyphen and repeated hyphens
collapsed (`meta-llama/CodeLlama-13b-hf` → `codellama-13b-hf`, Gemini 3.5 Flash → `gemini-3-5-flash`).

## Dates

Dates are ISO 8601 strings, quoted in YAML (`"2026-10-11"`). Validation rejects unquoted dates,
which YAML would otherwise read as date objects.
