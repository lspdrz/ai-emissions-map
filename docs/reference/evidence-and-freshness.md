# Evidence and freshness

Every claim the map makes about where a route runs, how carbon-intensive a grid is, or how large a model is
rests on cited sources. This document says which sources count, how one is recorded, and how a
claim is corrected.

## Primary and corroborating

- **Primary:** the organization's own publications (hosting pages, documentation, region lists,
  trust centers, subprocessor lists, data-processing agreements, announcements, its
  [serving-locations file](../serving-locations/README.md)), or a facility operator's own documents about
  that facility.
- **Corroborating:** press, analysts and third-party datasets. They are recorded for context and
  are never sufficient on their own. A location known only from the press is undisclosed
  (no candidates, rated D). The one exception is a route's speed, which OpenRouter's figures may set
  ([below](#a-routes-speed)).
- A developer's statement about where it serves a model establishes nothing about where another
  provider serves the same weights.

## A facility's PUE

A facility's PUE rests on primary sources only: the organization's own publications (its serving-locations file
included) or the facility operator's documents about that building. A third party's figure is never sufficient.

- **It counts** when it is the facility's total energy over its IT energy, measured over twelve months: a calendar
  year's figure, or the trailing twelve months a live dashboard shows. `period_end` records the last day of those
  twelve months.
- **It does not count** when it is a design or target figure, a single month (a "best month"), a real-time reading,
  an average across several of the organization's facilities, or an upper bound ("less than 1.1"). Record such a
  figure in the route's comments, not in the facility's `pue:`.
- **A cloud region's PUE** is not curated: it comes from the cloud provider's own reports, as the Green Software
  Foundation normalizes them in `sources/snapshots/cloud_regions.csv`.

## A route's speed

A route's `speed:` is its service's measured `tokens_per_second` and `time_to_first_token_s`, both required.

- **From the provider**, primary: its own published figures for that service.
- **Otherwise from OpenRouter**, corroborating: the one third party whose figure may set a speed, measured on its
  own traffic (validation refuses any other third-party site). Read the model's providers page,
  `https://openrouter.ai/<model>/providers`, in a browser (it renders in JavaScript), and quote the Performance
  chart's **one-week average** for the provider and, where it shows one, the region of the route (such as "Google
  Vertex (EU)"): `Throughput` as `tokens_per_second` and `Latency` as `time_to_first_token_s`. Not the providers
  table, whose P50 is a rolling five-minute window, and not `E2E latency`, the whole request.
- **No endpoint for the route's service** (a regional option OpenRouter does not list separately): record nothing,
  and EcoLogits estimates the speed. Another service's figure is never borrowed.
- **The figures move.** A refresh reads them again and updates the values, the quote and `accessed`.

## An evidence entry

```yaml
- url: https://example.com/docs/regions
  shows: 'Regions page: "example-70b is served exclusively from Example Zurich 1"'
  accessed: "2026-09-20"
  kind: primary
```

| Field | Meaning |
|---|---|
| `url` | The page that was read |
| `shows` | The passage the claim rests on, quoted exactly from the page inside double quotes, with a few words of context outside them. The site shows quoted passages of at least 8 characters |
| `accessed` | The date the page was read |
| `kind` | `primary` or `corroborating` |
| `anomaly` | Optional. A publication that contradicts itself or another primary source |

**Anomalies.** Credit what the publication plainly discloses, record the contradiction in
`anomaly`, and ask the organization to clarify. Never silently correct a published figure.

## Recording a source

Read the page, quote the passage that establishes the claim in `shows`, and set `accessed` to the day
it was read. Never quote from memory. A page that renders only with JavaScript is read in a browser.

## Corrections

- There is no verification window: a source stands until it is shown to have changed or disappeared.
- A correction comes as a pull request. It updates the evidence (a new page, a new quotation, today's
  `accessed`) or, when the claim no longer holds, changes the location's candidates and `facilities:` to
  what the remaining primary evidence supports, down to no candidates.
