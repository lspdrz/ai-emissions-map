# Add a grid

## Use this when
A route needs a grid that has no file in `sources/grids/`: `python -m build score` reports "maps to zone 'XX',
which has no grid file" for a cloud region, or "grid 'xx' has no grids/xx.yaml" for a `grid:` candidate. Also
when a facility draws on its own generation rather than the public grid (an on-site grid).

## Inputs you need
- The zone code: for a cloud region, the `zone` column of `sources/snapshots/cloud_regions.csv`; otherwise
  Electricity Maps' code for the area (its map names every zone).
- The country (ISO 3166-1 alpha-2).
- For the scoring year (`GRID_YEAR` in `build/constants/config.py`), or the latest year before it: the zone's
  yearly **consumption-based** carbon intensity with **direct** (operational) emission factors, its life-cycle
  figure where the same page publishes one, and the page each number is read from.

## Files this changes
1. `sources/grids/<slug>.yaml`, new.

## Procedure
1. **Name the file.** The slug is the zone code in lower case (`US-CAL-CISO` is `us-cal-ciso`). An on-site grid
   is `<operator>-<site>-onsite`, with `supply: onsite` and no `zone`. The rules are in
   [`../reference/identity.md`](../reference/identity.md#grids).
2. **Is the zone subdivided?** Set `subdivided: true` only for an aggregate zone that contains finer zones (Sweden
   `SE` over `SE-SE1` to `SE-SE4`): naming it does not determine the grid.
3. **Find the value online.** Search published pages for the zone's yearly consumption-based direct intensity for
   the scoring year (or the latest year before it): the grid operator, the national energy or environment agency,
   and open datasets (Open Grid Emissions for the United States). Read the page itself. A consumption-based value
   traces imports and exports; a production-based value counts only what the grid generates, and is not used. A
   direct figure counts what power plants emit while generating; record a life-cycle figure only from the same page
   and for the same value as the direct one.
4. **If no page gives a consumption-based direct value, stop and tell the maintainer**: the grid cannot be added
   yet, and the route that needs it waits. Electricity Maps' public map shows life-cycle values only, which never
   stand in for a direct one. Agents never read Electricity Maps' site: it blocks automated readers.
5. **Record the value under `consumption`**, with `direct`, `lifecycle` where the page gives one, `gas` (`co2e`, or
   `co2` when the source counts carbon dioxide only; the score uses it and flags it), `source` (who published it)
   and evidence per
   [`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md#an-evidence-entry). Quote the
   number in `shows`. Years are quoted strings. A value published for a fiscal
   year is keyed by the calendar year holding most of its months, the year it ends on a tie (April 2024 to March
   2025 is `"2024"`; July 2023 to June 2024 is `"2024"`); say which fiscal year in `comments`.
6. **Write the file:**
   ```yaml
   name: fr
   display_name: France
   zone: FR
   country: FR
   values:
     "2025":
       consumption:
         direct: 20.0
         gas: co2e
         source: Example Grid Operator
         evidence:
         - url: https://grid-operator.example/annual-review-2025/emissions
           shows: 'Annual review 2025: "the carbon intensity of consumption, taking electricity trading with other countries into account, was 20.0 gCO2e/kWh"'
           accessed: "2026-10-16"
           kind: primary
   ```

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` rewrites the score of every route on the grid; `release` rewrites `web/data/data.json`. Both must end
without `ERROR:` lines; commit everything they write. `score` refuses a grid without a consumption-based direct
value, and a grid no route uses, so add the grid together with the route that needs it.

## Expected PR contents
The grid file, usually with the route that needs it, the `disclosure_rating:` and `carbon_score:` fields that moved and `web/data/data.json`.
One line per grid on where its value came from.

## Stop and escalate when
- No published page gives a consumption-based direct value (step 4).
- Two consumption-based direct values disagree by more than 10%: record the grid operator's or national agency's,
  note the other in `comments`, and tell the maintainer.
- The zone's boundary does not match where the facility is, or a site draws on two zones.

## Relevant reference material
[`../METHODOLOGY.md`](../METHODOLOGY.md) ·
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
