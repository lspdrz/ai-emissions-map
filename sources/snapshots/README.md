# Snapshots

Data from outside the map that the build reads. Each file has a `.provenance.json` beside it saying where
it came from, when, and under what licence.

- `cloud_regions.csv`: which grid zone(s) each cloud region draws power from. Committed.
- `grid_intensity.csv`: Ember's yearly intensity of electricity generation (gCO2e/kWh) for each country, US state
  and Chinese province: the grid intensity (I) of every score. Committed. Ember's data is CC-BY-4.0: credit Ember wherever it is shown.

## Refreshing the cloud-region table

The table is a pinned copy of the Green Software Foundation's `Cloud_Region_Metadata.csv`, from
https://github.com/Green-Software-Foundation/real-time-cloud. To refresh it:

1. **Pin a commit.** Take the file at a specific commit of that repository, never a branch:
   `https://raw.githubusercontent.com/Green-Software-Foundation/real-time-cloud/<commit>/Cloud_Region_Metadata.csv`.
   It needs the columns `year`, `cloud-provider`, `cloud-region`, `em-zone-id` and `location`.
2. **Keep three providers,** renamed: `Amazon Web Services` → `aws`, `Microsoft Azure` → `azure`,
   `Google Cloud` → `gcp`. Any other provider is skipped.
3. **For each region, use the most recent year that has an `em-zone-id`.** Keep every zone that region
   lists in that year: a region drawing on several zones (Azure `northeurope`: Finland and Ireland) has
   one row per zone, and its routes get a range. A region with no `em-zone-id` in any year is skipped.
4. **Write `cloud_regions.csv`** with the columns `vendor,region,zone,year,location`, sorted by provider
   and region, zones sorted within a region.
5. **Write `cloud_regions.provenance.json`** with `source`, `repository`, `commit`, `url` (the pinned raw
   URL), `licence` ("see the source repository's License.md"), `retrieved` (today), `sha256` (of the file
   as downloaded), and `skipped`: one `{vendor, region, reason}` per region left out.
6. **Check and review.** Run `uv run python -m build score`, then
   `uv run python -m build release`, and read the diff: a region whose zone changed moves the scores of every route that names it.

Committed files say only "see the source repository's License.md" about this data's licence.

## Refreshing the grid-intensity table

The table is built from [Ember](https://ember-energy.org/)'s three yearly releases by `python -m build import-ember`,
which keeps the emissions intensity of total generation for every country (keyed by its ISO 3166-1 alpha-2 code), every
US state and every Chinese province (keyed by its ISO 3166-2 code, such as `US-VA` or `CN-GD`), for every year Ember
publishes. Ember's Indian states are left out: that release counts CO2 only, on another basis. To refresh it:

1. **Download the three releases by hand** into a folder outside the repository (Ember updates them about twice a
   month):
   - global: https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv
   - US states: https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/generation/outputs/release_us_subnational_generation_yearly.csv
   - China provinces: https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/generation/outputs/release_chn_subnational_generation_yearly.csv
2. **Import them:** `uv run python -m build import-ember --global-csv <global.csv> --us-csv <us.csv> --china-csv
   <china.csv>`. It writes `grid_intensity.csv` and `grid_intensity.provenance.json` (the three URLs with each
   download's `sha256`, the licence, `retrieved` (today), the row count, and `skipped`: one `{area, code, reason}` per
   area left out: a country without an ISO 3166-1 alpha-2 code, or a release's national total, which is not an
   ISO 3166-2 subdivision). It then rewrites every grid's `intensity:` from the new table, as
   `python -m build grid-emissions` does.
3. **Check and review.** Run `uv run python -m build score`, then `uv run python -m build release`, and read the diff:
   Ember revises recent years, so scores can move. Say in the pull request that they move with the new data.

To move every score to a newer year of data, change `GRID_YEAR` in `build/constants/config.py` in its own pull request
once Ember publishes most countries for that year; until then each geography uses its latest earlier year.
