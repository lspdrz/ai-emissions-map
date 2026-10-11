# Refresh an organization

## Use this when
Before a release; when `build.validate --release-date` warns that an organization's evidence is
stale; or when an organization tells you something has changed.

## Inputs you need
- The organization's slug.

## Files this changes
1. `sources/routes/<org>-*.yaml`: dates and digests (by `build.reverify --write`), and by hand any
   claim that no longer holds.
2. `sources/facilities/<slug>.yaml` for the facilities its routes cite.

## Procedure
1. **Dry run:** `uv run python -m build.reverify --org <slug>`. Each source is `ok` (unchanged, or
   its quoted text is still on the page) or `HELD` with a reason.
2. **Write what confirmed:** `uv run python -m build.reverify --org <slug> --write`. This re-dates
   only claims whose primary sources all confirmed.
3. **Work through every `HELD` source by hand:**
   - *Page moved or reworded, claim still true:* capture the new page with `build.fetch_source`,
     replace the entry, rewrite `shows`, and set the claim's `last_verified` to today.
   - *Claim no longer true:* change the candidates and the confidence to what the primary evidence
     now supports, possibly down to `unknown`.
   - *Manual capture:* save the page again, recapture with `--manual`, and re-date the claim if it
     still holds.
4. **If the organization publishes a serving-locations file**, read it again:
   `uv run python -m build.disclosure <disclosure_url> --org <slug>`.

## Validation
```bash
uv run python -m build.validate --release-date <next release date>
```
It must print `0 error(s)` and no stale-evidence warning for this organization.

## Expected PR contents
The re-dated and edited route and facility files, and one line per changed claim on what changed
and why.

## Stop and escalate when
- A change would lower the organization's rating: tell the maintainer before the release, because
  the organization is owed notice.
- A source contradicts a claim that has been published.

## Relevant reference material
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
