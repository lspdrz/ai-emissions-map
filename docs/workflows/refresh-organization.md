# Refresh an organization

## Use this when
Someone reports that an organization's source has changed or disappeared, or the organization tells you
something has changed.

## Inputs you need
- The organization's slug.
- What was reported, if anything: the route and the source in question.

## Files this changes
1. `sources/routes/<org>-*.yaml`: evidence, and the location when a claim no longer holds.

## Procedure
1. **Re-read every source** on the organization's routes. For each,
   check that the passage quoted in `shows` is still on the page.
2. **Source still says it:** leave the entry as it is.
3. **Page moved or reworded, claim still true:** replace the entry with the new page, quote the
   passage that now establishes the claim in `shows`, and set `accessed` to today.
4. **Claim no longer true:** change the candidates and `facilities:` to what the remaining primary
   evidence supports, down to no candidates.
5. **If the organization publishes a serving-locations file**, read it again and compare it with the
   routes (see [`../reference/location-disclosure.md`](../reference/location-disclosure.md#serving-locations-files)).

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` rewrites the carbon intensities and ratings the corrections move; `release` rewrites `web/data/data.json`.
Both must end without `ERROR:` lines; commit everything they write.

## Expected PR contents
The edited route files, and one line per changed claim on what changed and why.

## Stop and escalate when
- A change would lower the organization's rating: tell the maintainer before the release, because
  the organization is owed notice.
- A source contradicts a claim that has been published.

## Relevant reference material
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
