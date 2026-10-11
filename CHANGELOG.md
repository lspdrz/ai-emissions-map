# Changelog

All notable changes to this repository are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Record a change
under `## [Unreleased]`, in the same PR that makes it, only when it is notable and user-facing: a
new organization or route, a methodology or schema change, a new workflow or skill. One line per
entry, in plain past tense.

## [Unreleased]

### Added
- Carbon scores for routes (full Software Carbon Intensity per 1,000 output tokens, as a range and
  a band) and location disclosure ratings for routes and organizations.
- Imports with provenance: yearly grid intensity (kept local) and the cloud region to grid zone
  mapping from the Green Software Foundation.
- Evidence capture (`build.fetch_source`), re-verification (`build.reverify`, with `--org`), and
  the serving-locations disclosure format with its checker (`build.disclosure`).
- The methodology, reference rules, workflows and skills for adding organizations, facilities,
  models and routes and refreshing an organization; the rulings log; CI validation.
