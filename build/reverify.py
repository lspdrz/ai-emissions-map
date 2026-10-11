"""Re-verify location evidence: re-fetch each cited source and re-date the claims it still supports.

A source confirms when its fresh fetch is byte-identical to the recorded hash, or when every passage its
`shows` quotes (text in double quotes) still appears on the page. A location claim (a route's
`location`, or a facility) is re-dated to today only when every one of its primary sources confirms;
confirmed sources also get the fresh `accessed`, `http_status` and `content_sha256`. Anything else -
a changed page, a dead link, a manual capture - leaves the claim untouched and goes in the report for a
person. Locations with confidence `unknown`, and aggregator routes, have nothing to re-verify.

Dry run by default; `--write` edits sources/ in place with build.yamledit.

Usage:
    uv run python -m build.reverify                 # report only
    uv run python -m build.reverify --oldest 10 --write
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from build.fetch_source import fetch, normalize
from build.validate import ROOT, load_sources
from build.yamledit import set_scalars

_QUOTED = re.compile(r'"([^"]{8,})"')


def confirms(entry: dict, result: dict) -> tuple[bool, str]:
    """Whether a fresh fetch still supports a recorded evidence entry, and why."""
    if result["error"]:
        return False, result["error"]
    if result["http_status"] is not None and result["http_status"] >= 400:
        return False, f"HTTP {result['http_status']}"
    if result["content_sha256"] == entry["content_sha256"]:
        return True, "unchanged"
    quotes = [normalize(q).lower() for q in _QUOTED.findall(entry["shows"])]
    if not quotes:
        return False, "page changed; shows quotes nothing to look for"
    text = normalize(result["text"]).lower()
    if all(q in text for q in quotes):
        return True, "page changed; quoted text still present"
    return False, "page changed; quoted text not found"


def _claims(data: dict) -> list[tuple[str, tuple, str, list]]:
    """(file, path to the claim's last_verified, its date, [(path to evidence entry, entry)]) per claim."""
    claims = []
    for name, f in data["facilities"].items():
        evidence = [(("location_evidence", i), e) for i, e in enumerate(f["location_evidence"])]
        claims.append((f"facilities/{name}.yaml", ("last_verified",), f["last_verified"], evidence))
    for name, r in data["routes"].items():
        loc = r.get("location")
        if not loc or loc["confidence"] == "unknown":
            continue
        evidence = [(("location", "evidence", i), e) for i, e in enumerate(loc["evidence"])]
        claims.append((f"routes/{name}.yaml", ("location", "last_verified"), loc["last_verified"], evidence))
    return sorted(claims, key=lambda c: (c[2], c[0]))


def reverify(root: Path, today: date, fetcher=fetch, write: bool = False, oldest: int | None = None,
             only: list[str] | None = None) -> list[dict]:
    """Re-fetch the evidence of the oldest claims; return one report row per source checked."""
    claims = [c for c in _claims(load_sources(root)) if only is None or c[0] in only]
    if oldest is not None:
        claims = claims[:oldest]
    report: list[dict] = []
    for file, date_path, _, evidence in claims:
        updates: dict[tuple, object] = {}
        primary_ok: list[bool] = []
        for path, entry in evidence:
            result = fetcher(entry["url"], entry.get("capture", "auto"))
            ok, detail = confirms(entry, result)
            report.append({"file": file, "url": entry["url"], "kind": entry["kind"], "confirmed": ok, "detail": detail})
            if entry["kind"] == "primary":
                primary_ok.append(ok)
            if ok:
                updates[path + ("accessed",)] = today.isoformat()
                updates[path + ("content_sha256",)] = result["content_sha256"]
                if result["http_status"] is not None and "http_status" in entry:
                    updates[path + ("http_status",)] = result["http_status"]
        if write and primary_ok and all(primary_ok):
            updates[date_path] = today.isoformat()
            target = root / "sources" / file
            with target.open(encoding="utf-8", newline="") as fh:   # newline="": keep the file's line endings
                text = fh.read()
            with target.open("w", encoding="utf-8", newline="") as fh:
                fh.write(set_scalars(text, updates))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.reverify", description=__doc__.splitlines()[0])
    parser.add_argument("--oldest", type=int, help="only the N claims verified longest ago")
    parser.add_argument("--write", action="store_true", help="re-date confirmed claims in sources/")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    report = reverify(ROOT, date.today(), write=args.write, oldest=args.oldest)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for row in report:
            mark = "ok  " if row["confirmed"] else "HELD"
            print(f"{mark} {row['file']}  {row['url']}  ({row['detail']})")
        held = sum(not r["confirmed"] for r in report)
        print(f"{len(report) - held} source(s) confirmed, {held} need a person")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
