# Location disclosure

How precisely a route's location establishes where its electricity comes from, how that becomes the
route's rating, and how an organization is rated. Which sources count is in
[`evidence-and-freshness.md`](evidence-and-freshness.md); how the location then enters the carbon
score is in the [methodology](../METHODOLOGY.md).

## A route's rating

A route's rating measures how precisely the **primary** evidence determines where the route's electricity comes from.
Nobody writes it: `python -m build score` generates it from the location's candidates, the grids they resolve
to, its `facilities` and its evidence, taking the first row that applies:

| The disclosure establishes | Rating | Points |
|---|---|---|
| Nothing: no candidates, or no primary evidence (unknown, or the press only) | D | 0 |
| The facilities, named in `facilities:`, so their actual supply can be checked | A | 3 |
| One grid that is not `subdivided` | B | 2 |
| More than one possible grid, or one `subdivided` grid | C | 1 |

The points serve only to average an organization's routes (below); they are `DISCLOSURE_POINTS` in
`build/constants/config.py`.

A building earns more than its grid because only the building tells whether the electricity comes from the
public grid at all: a facility may run on its own generation (an on-site grid, `supply: onsite`). Naming a cloud
region counts only for the grid it resolves to.

## Candidates

Each candidate resolves to one or more grid files in `sources/grids/`:

| Candidate | Resolves through |
|---|---|
| `grid:<slug>` | `sources/grids/<slug>.yaml` directly |
| `cloud:<vendor>:<region>` | `sources/snapshots/cloud_regions.csv` (`vendor` is `aws`, `azure` or `gcp`) to its zone codes, then to the grid files whose `zone:` is that code. A region may span several zones, and the route's score is then a range across them |

Two candidates on the same grid count as one grid. A route whose evidence names its buildings lists them in
`location.facilities`, in words, and gives the grid they draw from as its candidate: the public grid's zone, or
the facility's on-site grid.

## Providers that may run anywhere in their network

When a provider states only that a request may be processed in any of its locations (a "global"
endpoint, for example), the candidates are every region the provider lists for that model, which makes the
rating C. The score is a range across all of them. When it commits to a jurisdiction (the United States, the European Union, a
single country), the candidates are all of its regions within that jurisdiction, because the
commitment is to the jurisdiction, not to the region the endpoint is named after.

## Organization rating

An organization's rating is the mean of its routes' points, each route counting equally, rounded to
the nearest rating with ties rounding down (1.5 → C). It is always shown with the spread, for
example "C (2 routes at B, 1 at D)". An organization with no routes is not rated.

A route's rating and an organization's rating answer different questions. Each route is rated on
how precisely its own location is disclosed. The organization is rated on all the ways it lets
customers use its models, so where a customer can choose among regions or jurisdictions, every
choice is a route and counts. The route marked `default: true` is the one used unless the
customer chooses; it is shown as such, and counts like any other.

## Gaps

Each route below A states what is missing, in one of these forms:

- "The grid is disclosed, not the facility." (B)
- "The grid is not determined: several are possible." (C)
- "Location not disclosed by the provider." (D)

## Serving-locations files

An organization can publish its locations as a [serving-locations file](../serving-locations/README.md), on its
own domain at `/.well-known/ai-serving-locations.json`, and is recorded with it as `disclosure_url`. A curator
reads the file, checks it against its schema, and compares it with the curated routes; a route that changes cites
the file as primary evidence, like any other page.

- **Each `routing` entry is one route,** named as [`identity.md`](identity.md#routes) says: the entry marked
  `"default": true` is `<org>-<model>` with `default: true`, and every other entry is `<org>-<model>-<name>`.
- **Each of its `locations` is a candidate on that route:** a `facility` is named in `location.facilities` with
  the grid it draws from, a `region` becomes a `cloud:` candidate, and a `grid_zone` a `grid:` candidate. The
  route's rating then follows [the ladder](#a-routes-rating).
- **A model the file leaves out** is rated from the organization's other publications, like any model without a
  file.
- **The file stands like any source:** it is read again when the organization is refreshed, and until a
  correction shows it no longer holds. A file that is gone or no longer matches leaves its routes to the best
  other primary evidence, or to D.
