# Add a facility

## Use this when
A route's primary evidence names a specific data center that has no file in `sources/facilities/`.
Facilities are shared: if the building already has a record, cite that one.

## Inputs you need
- The operator (who runs the building), and the site's name and city.
- Its ownership: `owned`, `colocation`, `hpc_center` or `gpu_cloud`.
- Its grid zone.
- **Primary** evidence locating it: the operator's own page about the facility.

## Files this changes
1. `sources/facilities/<slug>.yaml`, new.

## Procedure
1. **Check for an existing record:** `grep -rln "<city>\|<operator>" sources/facilities/`.
2. **Pick the slug** `<operator>-<site>` (for example `infomaniak-d4`), per
   [`../reference/identity.md`](../reference/identity.md#facilities).
3. **Capture the evidence**: `uv run python -m build.fetch_source <url>` (add `--browser` for a
   page that renders only with JavaScript). Paste the printed entry and write `shows` per
   [`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md#an-evidence-entry).
4. **Find the grid zone.** For most countries it is the ISO country code (`CH`, `DE`). Some
   countries are split into subnational zones (the United States by balancing area, Japan by
   region): use the zone covering the facility's location, and check the spelling against the
   zone codes in `sources/snapshots/cloud_regions.csv`.
5. **Write the file:**
   ```yaml
   name: alpinehost-alp-1
   display_name: Alpine Host DC 1 (Zurich)
   operator: alpinehost
   ownership: owned
   grid_zone: CH
   last_verified: "2026-10-11"
   location_evidence:
   - url: https://alpinehost.example/datacenters
     shows: 'Data center list: "ALP-1, Zurich, Switzerland, owned and operated by Alpine Host"'
     accessed: "2026-10-11"
     http_status: 200
     content_sha256: <from fetch_source>
     kind: primary
     capture: auto
   ```
   `last_verified` is the date you confirmed the location against the evidence.

## Validation
```bash
uv run python -m build.validate
```
It must print `0 error(s)`. With a local grid file in `sources/snapshots/grid/`, it also checks
that the zone exists in the grid data; without one, check the zone code by hand.

## Expected PR contents
The facility file, usually together with the route that cites it.

## Stop and escalate when
- The only evidence is press or a third-party list: a facility needs primary evidence, so record
  the route at the level the primary sources support instead.
- One site draws on two grid zones: that is two records, one per unit; ask the maintainer.
- You cannot tell who operates the building.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/location-disclosure.md`](../reference/location-disclosure.md)
