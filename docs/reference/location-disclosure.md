# Location disclosure

How precisely a route's location is established, how that becomes a letter, and how an
organization is rated. Which sources count is in
[`evidence-and-freshness.md`](evidence-and-freshness.md); how the location then enters the carbon
score is in the [methodology](../methodology.md).

## Confidence levels

A route's `location.confidence` is the level its **primary** evidence establishes:

| `confidence` | What the primary evidence establishes | Letter | Value |
|---|---|---|---|
| `facility` | The named data center or centers | A | 4 |
| `region` | A cloud region or provider region | B | 3 |
| `country` | A single country | C | 2 |
| `country_set` | Several possible countries | D | 1 |
| `unknown` | Nothing, or the press only | E | 0 |

Where candidates differ in precision, the least precise one decides.

## Candidates

Each candidate resolves to one or more grid zones:

| Candidate | Resolves through |
|---|---|
| `facility:<slug>` | The facility's `grid_zone` |
| `cloud:<vendor>:<region>` | `sources/snapshots/cloud_regions.csv` (`vendor` is `aws`, `azure` or `gcp`). A region may span several zones, and the route's score is then a range across them |
| `zone:<code>` | The grid zone directly: usually a country code; some countries have subnational zones |

`build.validate` checks that confidence claims no more than the candidates show: `facility` needs
every candidate to be a `facility:`, and `region` needs every candidate to be a `facility:` or a
`cloud:`. Whether the candidates span one country (`country`) or several (`country_set`) is not
checked yet; get it right by hand.

## Providers that may run anywhere in their network

When a provider states only that a request may be processed in any of its locations (a "global"
endpoint, for example), the candidates are every region the provider lists for that model, and the
confidence is `country_set`, or `country` if they all lie in one country. The score is a range
across all of them. When it commits to a jurisdiction (the United States, the European Union, a
single country), the candidates are its regions for that model within the jurisdiction.

## Aggregator routes

An aggregator route lists `upstreams`: routes of other organizations that serve the same model,
each with a positive `weight`, backed by primary `upstream_evidence` (the aggregator's published
routing configuration). There may be no cycles. The route takes the level of its least-disclosed
upstream, is scored only if every upstream is scored, and reports the union of their ranges. The
weights are displayed but not used to average, because they describe intended routing, not
measured traffic.

## Organization rating

An organization's rating is the mean value of all its routes, each counting equally, rounded to
the nearest letter with ties rounding down (2.5 → C). It is always shown with the spread, for
example "C (2 routes at B, 1 at E)". An organization with no routes is not rated.

A route's level and an organization's rating answer different questions. Each route is rated on
how precisely its own location is disclosed. The organization is rated on all the ways it lets
customers use its models, so where a customer can choose among regions or jurisdictions, every
choice is a route and counts. The route marked `default: true` is the one used unless the
customer chooses; it is shown as such, and counts like any other.

## Gaps

Each route below A states what is missing, in one of these forms:

- "Location disclosed to a region, not a specific facility."
- "Location disclosed only to a country."
- "Location disclosed only as a set of possible countries."
- "Location not disclosed by the provider."
- "Reported in press, not disclosed by the provider."
- "Location evidence not re-verified within 90 days of the release."
- "An upstream route's location is undisclosed or unverified."

## Serving-locations files

An organization can publish its locations as a [serving-locations file](disclosure-formats.md) and
record it as `disclosure_url`. `uv run python -m build.disclosure <url-or-file> --org <slug>` checks
the file, works out the level each model's default routing discloses, and compares it with the
curated routes. It proposes and never edits: a curator who accepts a proposal cites the file as
primary evidence on the route, like any other page.
