# AI Emissions Map documentation

Start here. The repository is organized around the task you arrived to do. Find your task below,
open the one workflow it points to, and follow it. Each workflow names the rules it relies on and
the exact checks to run.

## The doors

| I want to… | Workflow | Skill |
|---|---|---|
| Add an organization that serves AI models | [`workflows/add-organization.md`](workflows/add-organization.md) | `add-organization` |
| Add the grid a route draws from | [`workflows/add-grid.md`](workflows/add-grid.md) | `add-grid` |
| Add the record for a model a route serves | [`workflows/add-model.md`](workflows/add-model.md) | `add-model` |
| Record where an organization serves a model | [`workflows/add-route.md`](workflows/add-route.md) | `add-route` |
| Re-check an organization's evidence | [`workflows/refresh-organization.md`](workflows/refresh-organization.md) | `refresh-organization` |

Changing or retiring an existing record has no workflow yet: edit the file surgically (never load
and re-dump it) and follow [`reference/identity.md`](reference/identity.md) for renames.

## The kinds of document

- **[`METHODOLOGY.md`](METHODOLOGY.md)** is the canonical statement of how routes' carbon intensities are
  calculated and organizations rated, and the normative home of the carbon intensity.
- **`workflows/`** answers *how do I accomplish this task?*, one per task, all in the same template.
- **`reference/`** answers *what rules govern the task?* A rule lives in one place; workflows link
  to it rather than restating it:
  [`identity.md`](reference/identity.md) (slugs, organizations and routes, renaming),
  [`evidence-and-freshness.md`](reference/evidence-and-freshness.md) (what counts, how it is
  recorded, how long it stays current),
  and [`location-disclosure.md`](reference/location-disclosure.md) (route ratings, candidates,
  organization ratings, gaps, and how a serving-locations file becomes routes).
- **[`serving-locations/`](serving-locations/README.md)** is the serving-locations format for organizations that
  want to publish one: its JSON Schema, a README and examples.
