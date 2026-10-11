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
    uv run python -m build.reverify --org alpinehost   # one organization's routes and their facilities
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path

from build.fetch_source import fetch, normalize
from build.validate import ROOT, load_sources
from build.yamledit import set_scalars

_QUOTED = re.compile(r'"([^"]{8,})"')


class ReverifyError(Exception):
    pass


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


def org_claim_files(data: dict, org: str) -> list[str]:
    """The claim files an organization's refresh covers: its routes, then the facilities they cite."""
    if org not in data["organizations"]:
        raise ReverifyError(f"no organization {org!r} in sources/organizations/")
    routes, facilities = [], set()
    for name in data["organizations"][org].get("routes") or []:
        if name not in data["routes"]:
            continue  # a roster entry with no file is build.validate's error to report
        routes.append(f"routes/{name}.yaml")
        for candidate in (data["routes"][name].get("location") or {}).get("candidates", []):
            kind, _, slug = candidate.partition(":")
            if kind == "facility":
                facilities.add(f"facilities/{slug}.yaml")
    return sorted(routes) + sorted(facilities)


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
            new = set_scalars(text, updates)   # raises before anything is written if the edit cannot be proven
            temp = target.with_name(f".{target.name}.reverify")
            with temp.open("w", encoding="utf-8", newline="") as fh:
                fh.write(new)
            os.replace(temp, target)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.reverify", description=__doc__.splitlines()[0])
    parser.add_argument("--org", help="only this organization's routes and the facilities they cite")
    parser.add_argument("--oldest", type=int, help="only the N claims verified longest ago")
    parser.add_argument("--write", action="store_true", help="re-date confirmed claims in sources/")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    only = None
    if args.org:
        try:
            only = org_claim_files(load_sources(args.root), args.org)
        except ReverifyError as e:
            print(f"ERROR: {e}")
            return 1
    report = reverify(args.root, date.today(), write=args.write, oldest=args.oldest, only=only)
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
