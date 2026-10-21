# Add a grid

## Use this when
A route needs a grid that has no file in `sources/grids/`: `python -m build score` reports "maps to zone 'XX',
which has no grid file" for a cloud region, or "grid 'xx' has no grids/xx.yaml" for a `grid:` candidate. Also
when a facility draws on its own generation rather than the public grid (an on-site grid).

## Inputs you need
- The zone code: for a cloud region, the `zone` column of `sources/snapshots/cloud_regions.csv`; otherwise
  Electricity Maps' code for the area (its map names every zone).
- The country the zone lies in (ISO 3166-1 alpha-2) and, for a grid in the United States or China, the state or
  province its facility is in.

A grid file records where a grid is. Its intensity is Ember's value for its subdivision (a US state, a Chinese
province) where it names one, else for its country, from
`sources/snapshots/grid_intensity.csv` (see [`../METHODOLOGY.md`](../METHODOLOGY.md)).

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
4. **For a grid in the United States or China, set the subdivision**: the state or province of the facility or cloud
   region the route uses, as the part of its ISO 3166-2 code after the country (`VA` for Virginia, US-VA; `GD` for
   Guangdong, CN-GD). Grids can cross state and province lines; name the one where the facility is, and say in
   `comments` when the grid spans others. Without a subdivision, the grid uses the national value. Ember publishes no
   other subdivisions on the same basis, so leave it out elsewhere (step 6 refuses one it has no value for).
5. **Write the file:**
   ```yaml
   name: fr
   display_name: France
   zone: FR
   country: FR
   ```
   A US grid:
   ```yaml
   name: us-mida-pjm
   display_name: PJM Interconnection
   zone: US-MIDA-PJM
   country: US
   subdivision: VA
   comments: PJM spans thirteen states; the facility is in Virginia.
   ```
6. **Write its intensity:** `uv run python -m build grid-emissions <slug>` (for example `us-mida-pjm`). It looks up
   Ember's value for the grid's subdivision, or else its country, for the release's year or the latest earlier one,
   and writes it at the end of the file below a comment saying it is written by the command: the value, its year and
   the geography it is for (`CH`, `US-VA`, `CN-GD`). Never edit the `intensity:` field by hand. The command refuses a
   grid whose country or subdivision has no Ember value, and an on-site grid (which no country or subdivision average
   can value).

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` reads the grid's `intensity:` (it refuses a grid without one, naming the command to run) and rewrites the score
of every route on the grid; `release` rewrites `web/data/data.json`. Both must end without `ERROR:` lines; commit
everything they write. `score` also refuses a grid no route uses, so add the grid together with the route that needs
it. CI runs `uv run python -m build check-grid-emissions`, which fails if a stored `intensity:` is not what step 6
would write now.

## Expected PR contents
The grid file with the `intensity:` step 6 wrote, usually with the route that needs it, the `disclosure_rating:` and
`carbon_score:` fields that moved and `web/data/data.json`.

## Stop and escalate when
- Ember has no value for the country or subdivision (`grid-emissions` says so).
- The grid is on-site: the method cannot score it yet.
- The zone's boundary does not match where the facility is, or a site draws on two zones.

## Relevant reference material
[`../METHODOLOGY.md`](../METHODOLOGY.md) ·
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
