# AGENTS.md

Guidance for coding agents and people working in this repository.

## Project overview

The AI Emissions Map gives every AI serving route (an organization serving a model from a
location) a **carbon score**, and every organization a **location disclosure rating** (A–E). The
score is the full Software Carbon Intensity per 1,000 output tokens: energy and embodied emissions
from EcoLogits, grid carbon intensity of the route's location. Locations are the only thing curators
research; everything else is calculated. The rules are in [`docs/methodology.md`](docs/methodology.md)
and [`docs/reference/`](docs/reference/).

## Directory map

```
sources/organizations/   one file per organization, with its routes: roster
sources/facilities/      one file per physical data center, shared by tenants
sources/routes/          one file per route, <org>-<model>.yaml
sources/models/          one record per model a route serves: copied from EcoLogits, or curated
sources/snapshots/       imported data, each file with a <stem>.provenance.json
  cloud_regions.csv      cloud region -> grid zone(s), from the Green Software Foundation (committed)
  grid/                  yearly grid intensity: LOCAL ONLY, never committed (see its README)
build/                   Python modules; each is `python -m build.<module>` and answers --help
build/*.json             generated outputs, never committed
docs/                    methodology, workflows, reference rules, schemas, rulings
skills/                  thin agent skills over docs/workflows/; .claude/skills/ links to them
tests/                   pytest; fixtures hold invented values
```

## The `build/` modules

- **Core:** `config` (methodology constants), `utils`, `ranges` (the `Range` value class),
  `validate` (load and check `sources/`), `models` (parameter counts), `evidence` (the
  verification window), `grid` (intensity and location → zone resolution), `energy` (EcoLogits
  adapter), `compute` (route scores), `rate` (route levels, organization ratings), `serialize`
  (writes `build/routes.json` and `build/organizations.json`).
- **Imports:** `import_grid` (yearly grid files, local only), `import_cloud_regions` (pinned GSF
  commit).
- **Evidence:** `fetch_source` (capture a page: `auto`, `browser`, `manual`), `reverify`
  (re-fetch and re-date claims that still hold), `yamledit` (surgical value edits),
  `disclosure` (read an organization's serving-locations file).

## The data model in one minute

Records are plain dicts as `yaml.safe_load` reads them. The filename stem is the slug; renames go
through `aliases:`; there are no UUIDs. Each route is on exactly one organization's roster.
Evidence entries carry `shows` (an exact quote), `capture`, a hash and `kind`; `last_verified` sits
on the claim. Details: [`docs/reference/identity.md`](docs/reference/identity.md),
[`docs/reference/evidence-and-freshness.md`](docs/reference/evidence-and-freshness.md),
[`docs/reference/location-disclosure.md`](docs/reference/location-disclosure.md).

## Writing to `sources/`

- A **new** file may be written whole.
- An **existing** file is edited in place: by hand in the text, or by a tool through
  `build.yamledit.set_scalars`, which changes exact value spans and proves nothing else changed.
  **Never load-modify-dump** a file in `sources/`: it destroys comments, quoting and layout.
- Run `uv run python -m build.validate` after every change; it must print `0 error(s)`.

## EcoLogits

EcoLogits is a pinned Python dependency (`ecologits==…` in `pyproject.toml`, locked in `uv.lock`).
Its model catalogue ships inside the installed package, and `build.energy` runs it in-process:
nothing is fetched over the network. Every model a route serves has a record in `sources/models/`;
`source: ecologits` records copy the package, and `build.validate` fails if they stop matching it.

**Upgrading EcoLogits** is its own PR:

1. Change the pin in `pyproject.toml`, then `uv lock` and `uv sync`.
2. `uv run python -m build.validate` lists every model record that changed, with old and new values.
3. `uv run python -m build.models --sync` rewrites those records; the PR shows each change as a diff.
4. Run the tests, and say in the PR and the changelog that scores move with the new version.

## Traps

- **Grid data is never committed, real or mock.** `sources/snapshots/grid/` is gitignored except
  its README. Each maintainer imports it locally. CI has none, so `build.validate` skips zone
  checks there and real scores cannot be built in CI. `*.MOCK.csv` files are development
  placeholders: never publish numbers built from them.
- About the cloud-region data's license, committed files say only "see the source repository's
  License.md".
- `build.fetch_source` leaves `shows` as a `TODO:` placeholder; validation fails until a person
  quotes the page.
- Dates are quoted strings in YAML; an unquoted date fails the schema.
- Organizations have no Gap Map identifier; that link was dropped.
- Tests: `uv run pytest`; `-m "not ecologits and not browser"` for the fast loop. Browser capture
  needs `uv sync --group browser && uv run playwright install chromium`.
- In zsh, never name a shell variable `path`: it is tied to `PATH`.
