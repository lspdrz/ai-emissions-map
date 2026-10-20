# Snapshots

Data from outside the map that the build reads. Each file has a `.provenance.json` beside it saying where
it came from, when, and under what licence.

- `cloud_regions.csv`: which grid zone(s) each cloud region draws power from. Committed.

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
