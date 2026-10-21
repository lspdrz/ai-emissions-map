# Add a grid

## Use this when
A route needs a grid that has no file in `sources/grids/`: `python -m build score` reports "maps to zone 'XX',
which has no grid file" for a cloud region, or "grid 'xx' has no grids/xx.yaml" for a `grid:` candidate. Also
when a facility draws on its own generation rather than the public grid (an on-site grid).

## Inputs you need
- The zone code: for a cloud region, the `zone` column of `sources/snapshots/cloud_regions.csv`; otherwise
  Electricity Maps' code for the area (its map names every zone).
- The country the zone lies in (ISO 3166-1 alpha-2).

A grid file records where a grid is. Its intensity is EcoLogits' electricity mix for
its country (see [`../METHODOLOGY.md`](../METHODOLOGY.md)).

## Files this changes
1. `sources/grids/<slug>.yaml`, new.

## Procedure
1. **Name the file.** The slug is the zone code in lower case (`US-CAL-CISO` is `us-cal-ciso`). An on-site grid
   is `<operator>-<site>-onsite`, with `supply: onsite` and no `zone`. The rules are in
   [`../reference/identity.md`](../reference/identity.md#grids).
2. **Is the zone subdivided?** Set `subdivided: true` only for an aggregate zone that contains finer zones (Sweden
   `SE` over `SE-SE1` to `SE-SE4`): naming it does not determine the grid. This affects the route's disclosure
   rating.
3. **Set the country** the zone lies in. For a zone that crosses a border, use the country of the facility, and say
   so in `comments`.
4. **Write the file:**
   ```yaml
   name: fr
   display_name: France
   zone: FR
   country: FR
   ```

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` rewrites the score of every route on the grid; `release` rewrites `web/data/data.json`. Both must end
without `ERROR:` lines; commit everything they write. `score` refuses a grid whose country EcoLogits has no mix for,
an on-site grid (which a country's mix cannot value), and a grid no route uses, so add the grid together with the
route that needs it.

## Expected PR contents
The grid file, usually with the route that needs it, the `disclosure_rating:` and `carbon_score:` fields that moved and
`web/data/data.json`.

## Stop and escalate when
- EcoLogits has no electricity mix for the country (`score` says so).
- The grid is on-site: the method cannot score it yet.
- The zone's boundary does not match where the facility is, or a site draws on two zones.

## Relevant reference material
[`../METHODOLOGY.md`](../METHODOLOGY.md) ·
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
