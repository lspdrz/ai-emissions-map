# Evidence and freshness

Every claim the map makes about where a route runs, where a facility is, or how large a model is
rests on cited sources. This document says which sources count, how one is recorded, and how long a
claim stays current.

## Primary and corroborating

- **Primary:** the organization's own publications (hosting pages, documentation, region lists,
  trust centers, subprocessor lists, data-processing agreements, announcements, its
  [serving-locations file](disclosure-formats.md)), or a facility operator's own documents about
  that facility.
- **Corroborating:** press, analysts and third-party datasets. They are recorded for context and
  are never sufficient on their own. A location known only from the press is undisclosed
  (confidence `unknown`).
- A developer's statement about where it serves a model establishes nothing about where another
  provider serves the same weights.

## An evidence entry

```yaml
- url: https://alpinehost.example/docs/regions
  shows: 'Regions page: "test-70b is served exclusively from ALP-1"'
  accessed: "2026-09-20"
  http_status: 200
  content_sha256: 4444444444444444444444444444444444444444444444444444444444444444
  kind: primary
  capture: auto
```

| Field | Meaning |
|---|---|
| `url` | The page that was read |
| `shows` | The passage the claim rests on, quoted exactly from the page inside double quotes, with a few words of context outside them. Each quoted passage should be at least 8 characters long, because re-verification looks for it. A person writes it: `build.fetch_source` leaves a `TODO:` placeholder, and validation fails until it is replaced |
| `accessed` | The date the page was read |
| `http_status` | The HTTP status of that read; required unless `capture: manual` |
| `content_sha256` | The hash of what was captured |
| `kind` | `primary` or `corroborating` |
| `capture` | `auto` (plain HTTP; hash over the response bytes), `browser` (headless Chromium for pages that render only with JavaScript; hash over the visible text), or `manual` (a page saved by hand when neither works; hash over the file) |
| `anomaly` | Optional. A publication that contradicts itself or another primary source |

**Anomalies.** Credit what the publication plainly discloses, record the contradiction in
`anomaly`, and ask the organization to clarify. Never silently correct a published figure.

## Capturing a source

```bash
uv run python -m build.fetch_source <url>                            # plain HTTP
uv run python -m build.fetch_source --browser <url>                  # JavaScript-only pages
uv run python -m build.fetch_source --manual page.html --url <url>   # a page saved by hand
```

Each prints an evidence entry to paste into the record; then write `shows`. Browser capture needs
`uv sync --group browser && uv run playwright install chromium`.

## Freshness

- `last_verified` belongs to the claim, not to each entry: a route's `location.last_verified`, or a
  facility's `last_verified`. It is the date on which someone (or `build.reverify`) confirmed that
  the claim as a whole still holds against its evidence. Re-confirming a conclusion is stronger
  than re-opening a URL.
- A route's location counts for a release only if its `last_verified` falls within the 90 days up
  to and including the release date, and it rests on at least one primary source. A date after the
  release does not count. A route that fails this is shown unscored at E, with the gap "Location
  evidence not re-verified within 90 days of the release", and is never called undisclosed.
- `uv run python -m build.validate --release-date <date>` warns about each such route.

## Re-verification

`build.reverify` re-fetches each source in its recorded capture mode. A source confirms if its
content is byte-identical to the recorded hash, or if every passage `shows` quotes is still on the
page; a `shows` with no quoted passage confirms only on identical bytes. A claim is re-dated to
today only when **every** primary source on it confirms, and confirmed entries also get the fresh
`accessed`, `http_status` and hash. Anything else (a changed page, a dead link, a manual capture)
leaves the claim untouched and is reported for a person. Locations with confidence `unknown`, and
aggregator routes, have nothing to re-verify.

```bash
uv run python -m build.reverify                    # report only, every claim
uv run python -m build.reverify --org <slug>       # one organization's routes and their facilities
uv run python -m build.reverify --oldest 10 --write
```

`--write` edits `sources/` through `build.yamledit`, which changes only the dated values and proves
nothing else moved.
