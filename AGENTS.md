# AGENTS.md

Guidance for coding agents and people working in this repository.

## Project overview

The AI Emissions Map gives every AI serving route (an organization serving a model, by default or in
a region the customer chooses) a **carbon score**, and every organization a **location disclosure rating** (A–D). The
score is the full Software Carbon Intensity per 1,000 output tokens: energy and embodied emissions
from EcoLogits, and grid carbon intensity from EcoLogits' electricity mix for the country of the route's location. Locations are the only thing curators
research; everything else is calculated. The rules are in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
and [`docs/reference/`](docs/reference/).

## Start here

1. **This file is the repo map**: layout, the `build/` modules, the data model, how to write to `sources/`, and
   the traps. Read it.
2. **[`docs/README.md`](docs/README.md) routes your task to its workflow.** Follow the workflow; do not improvise
   a procedure one already carries.
3. **Use the registered skill for that workflow.** They live under `.claude/skills/` (symlinks into `skills/`);
   if your tool does not list them, read `skills/<name>/SKILL.md` directly.

## Conventions

- `uv` for everything Python: `uv run python -m build score`, then `uv run python -m build release`, after every
  change to `sources/` or `build/`.
  If a pyenv `VIRTUAL_ENV` is set in your shell, prefix commands with `VIRTUAL_ENV=`.
- American English, plain prose.
- The maintainer reviews every commit: ask before committing, showing the message; no
  `Co-Authored-By` trailer; never push without asking.
- Plans, specs and working notes never go in the repository.

## Directory map

```
sources/organizations/   one file per organization
sources/grids/           one file per grid a route may draw from: its zone and country (location only, no values)
sources/routes/          one file per route, <org>-<model>.yaml, naming its organization in org:
sources/models/          one record per model a route serves: the developer's counts, or EcoLogits' estimate, cited
sources/snapshots/       imported data, each file with a <stem>.provenance.json
  cloud_regions.csv      cloud region -> grid zone(s), from the Green Software Foundation (committed)
build/                   Python modules; the command is `python -m build` (see --help)
docs/                    methodology, workflows, reference rules, serving-locations/ (the format to publish)
skills/                  thin agent skills over docs/workflows/; .claude/skills/ links to them
web/                     the Next.js site; web/data/data.json is written by build and committed
tests/                   pytest, laid out like build/; each test builds its data with tests/builders/
                         (records valid by construction; tests/builders/broken.py to break one)
```

## The `build/` modules

```
build/
  constants/config.py    the method's fixed numbers and the repository root
  schemas/               the shape and rules of each record (Pydantic TypedDicts)
  utils/                 range, bands
  carbon_score.py        a model + a route's grid files -> its carbon score (EcoLogits, each grid's value)
  disclosure_rating.py   a route's location -> its rating; an organization's route ratings -> its rating
  load_sources.py        reading sources/ and the cloud-region table from disk
  validate.py            every check on the records, against each other and the cloud-region table
  score.py               python -m build score: compute the disclosure_rating:/carbon_score: fields, write them
  generate_site_data.py  web/data/data.json: its contract and its content
  release.py             python -m build release: validate sources/, write web/data/data.json with the hash of its
                         inputs (meta.inputs_sha); computes nothing
  check_carbon_scores.py CI gate: every route's stored carbon score is current
  check_disclosure_ratings.py  CI gate: every stored route and organization rating is current
  check_site_data.py     CI gate: web/data/data.json is current with its inputs and keeps to its contract
  __main__.py            the commands: python -m build score, release, and the three gates check-carbon-scores,
                         check-disclosure-ratings, check-site-data
```

- **Core:** `carbon_score` (EcoLogits energy and embodied emissions, EcoLogits' electricity mix for each grid's
  country, the score of each route) and `disclosure_rating` (route ratings, generated from the location;
  organization ratings).
  Around them: `load_sources` and `validate` (reading and checking `sources/`), `score` (the `score`
  command: resolves each route's grid files, computes and writes each route's `disclosure_rating:` and
  `carbon_score:` and each organization's `disclosure_rating:`), `generate_site_data` (the shape of
  `web/data/data.json`), `release` (the `release` command: validates and publishes, with the hash of what it reads,
  computing nothing), `check_carbon_scores` and `check_disclosure_ratings` (what the CI gates compare: every
  stored score and rating against what `score` would write now), `check_site_data` (the CI gate on
  `web/data/data.json`: its hash and its contract), and `__main__` (the five commands). The
  scoring modules never import the others.
  Curation (research, evidence, model records, cloud regions) is done by following
  `docs/workflows/`, not by code.
- **`constants/`:** `config` (the methodology constants). A constant used by one module stays in
  that module.
- **`utils/`:** pure helpers, no I/O. `range` (the `Range` value class), `bands` (carbon bands).
- **`schemas/`:** the shape of every record in `sources/`, one file per record (`route`,
  `evidence`, `organization`, `grid`, `model`, plus `common`, `carbon_score`, `disclosure_rating`, `score` and `sources`):
  `TypedDict`s that pyright checks and Pydantic validates. Records stay plain dicts.
- **Import rules** (`pyproject.toml`, checked in CI by `uv run ruff check` and
  `uv run lint-imports`): `constants/` and `schemas/` import nothing from `build/`; `utils/`
  imports only other `utils/`; every other module may import them, never the
  other way round. Imports are absolute and at the top of the file, with no exceptions.
- **Types** are checked in CI by `uv run pyright` (standard mode, `build/` and `tests/`).
- **Formatting** is `uv run ruff format`, 120 columns (`pyproject.toml`); CI fails on any file it would change. The
  VS Code Ruff extension formats to the same width on save.

## The data model in one minute

Records are plain dicts as `yaml.safe_load` reads them. The filename stem is the slug; there are no UUIDs, and a
published slug is permanent. Each route names its organization in `org:`.
Evidence entries carry `url`, `shows` (an exact quote), `accessed` and `kind`; there is no verification
window (a source stands until a pull request corrects it). Details: [`docs/reference/identity.md`](docs/reference/identity.md),
[`docs/reference/evidence-and-freshness.md`](docs/reference/evidence-and-freshness.md),
[`docs/reference/location-disclosure.md`](docs/reference/location-disclosure.md).

## Writing to `sources/`

- A **new** file may be written whole.
- An **existing** file is edited in place, in the text.
  **Never load-modify-dump** a file in `sources/`: it destroys comments, quoting and layout.
- After changing facts run `uv run python -m build score`, then `uv run python -m build release`, and commit
  everything they write.

## EcoLogits

EcoLogits is a pinned Python dependency (`ecologits==…` in `pyproject.toml`, locked in `uv.lock`).
It runs in-process in `build.carbon_score`: nothing is fetched over the network. Every model a route serves has a record in `sources/models/`;
its counts come from the developer, or, where the developer has not released the architecture, from EcoLogits'
estimate, with the catalogue at the installed version as the evidence.

**Upgrading EcoLogits** is its own PR:

1. Change the pin in `pyproject.toml`, then `uv lock` and `uv sync`.
2. Find every model record citing the old catalogue (`grep -rl "ecologits/blob/<old version>" sources/models/`).
   For each, read the model's entry in the new catalogue (docs/workflows/add-model.md, step 3), update its counts
   if they moved, and point its evidence at the new version, with its quote and today's date. Then
   `uv run python -m build score`, whose diff shows every score that moved (EcoLogits' electricity mixes move with
   it too), and `uv run python -m build release`.
   Commit everything.
3. Run the tests, and say in the PR that scores move with the new version.

## Traps

- **Scores and ratings are fields written by `python -m build score`** at the end of route files
  (`disclosure_rating:`, `carbon_score:`) and organization files (`disclosure_rating:`), below a comment saying they
  are generated. `score` rewrites everything below that comment, so anything written there by hand is lost.
  Change the facts above them and rerun `score`; `release` copies them as they are. CI recomputes every
  stored value (`python -m build check-carbon-scores`, `check-disclosure-ratings`) and fails on any that differs.
- **`web/data/data.json` records `meta.inputs_sha`,** the hash of the records (grid files included),
  `build/`'s code and the EcoLogits version. CI fails when it no longer matches
  (`python -m build check-site-data`): run the release after changing anything in
  `sources/` or `build/`, code included, and commit what it writes. On a merge conflict
  in `web/data/data.json`, take either side and run the release again.
- **Grid intensities are not curated**: a grid file in `sources/grids/` holds only its zone, country, supply and
  whether it is subdivided. Every score uses EcoLogits' life-cycle electricity mix for the grid's country
  (`build.carbon_score.grid_intensity`), so zones in one country share a value. `score` refuses a grid whose
  country EcoLogits has no mix for, and an on-site grid. Agents never read Electricity Maps' site.
- **A route's rating is generated, never written**: from its candidates, their grids, its
  `facilities` and its evidence. There is no `confidence` field.
- **The site's data file is committed, and holds only what the site displays:** per-route results,
  each score with its E, I and M. It is `noindex` while `DRAFT` in `build/constants/config.py` is true.
- **The website deploys from `web/` only.** Vercel's Root Directory is `web`, and every push
  deploys. Every data pull request carries its `web/data/data.json` diff and publishes on merge.
- About the cloud-region data's license, committed files say only "see the source repository's
  License.md".
- Dates are quoted strings in YAML; an unquoted date fails validation.
- Organizations have no Gap Map identifier; that link was dropped.
- Tests: `uv run pytest`. No test runs EcoLogits: a test that computes a score sets its own E and M with
  `monkeypatch.setattr("build.carbon_score.ecologits_estimate", ...)`, and the tests of `ecologits_estimate` replace
  `compute_llm_impacts` with a fake. An EcoLogits change that moves a score shows in `build score`'s diff, and the CI
  gate `check-carbon-scores` fails until it is committed. Every record a test uses is built, and every mock set,
  inside the test itself, so everything its result depends on is visible there: no records built at import
  (module-level constants), no shared fixtures that mock.
- In zsh, never name a shell variable `path`: it is tied to `PATH`.
