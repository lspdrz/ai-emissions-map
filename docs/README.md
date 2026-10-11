# AI Emissions Map documentation

Start here. The repository is organized around the task you arrived to do. Find your task below,
open the one workflow it points to, and follow it. Each workflow names the rules it relies on and
the exact checks to run.

## The doors

| I want to… | Workflow | Skill |
|---|---|---|
| Add an organization that serves AI models | [`workflows/add-organization.md`](workflows/add-organization.md) | `add-organization` |
| Add a physical data center | [`workflows/add-facility.md`](workflows/add-facility.md) | `add-facility` |
| Add a model that EcoLogits does not know | [`workflows/add-model.md`](workflows/add-model.md) | `add-model` |
| Record where an organization serves a model | [`workflows/add-route.md`](workflows/add-route.md) | `add-route` |
| Re-check an organization's evidence | [`workflows/refresh-organization.md`](workflows/refresh-organization.md) | `refresh-organization` |

Changing or retiring an existing record has no workflow yet: edit the file surgically (never load
and re-dump it) and follow [`reference/identity.md`](reference/identity.md) for renames.

## The kinds of document

- **[`methodology.md`](methodology.md)** is the canonical statement of how routes are scored and
  organizations rated, and the normative home of the carbon score. The site will render it.
- **`workflows/`** answers *how do I accomplish this task?*, one per task, all in the same template.
- **`reference/`** answers *what rules govern the task?* A rule lives in one place; workflows link
  to it rather than restating it:
  [`identity.md`](reference/identity.md) (slugs, rosters, aliases),
  [`evidence-and-freshness.md`](reference/evidence-and-freshness.md) (what counts, how it is
  recorded, how long it stays current),
  [`location-disclosure.md`](reference/location-disclosure.md) (confidence levels, candidates,
  ratings, gaps) and
  [`disclosure-formats.md`](reference/disclosure-formats.md) (the files organizations can publish).
- **`schemas/`** holds the JSON Schemas for the files in `sources/` and for the serving-locations
  format.
- **`rulings/`** is the maintainer's decision log: every ruling an agent could not make, who made
  it, why, and where the rule it changed now lives. Read it before asking the maintainer anything.
  The format is in [`rulings/README.md`](rulings/README.md).
