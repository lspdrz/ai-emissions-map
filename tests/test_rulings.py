"""The rulings log keeps its shape: append-only in date order, and every reference resolves.

docs/rulings/log.yaml is what an agent reads before asking the maintainer anything, so a malformed
entry is worse than a missing one. The rules are in docs/rulings/README.md.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
REQUIRED = ("id", "date", "by", "venue", "question", "ruling", "status", "executor")
VENUES = {"session", "issue", "pr-review"}
STATUSES = {"in-force", "deferred", "replaced"}
EXECUTORS = {"agent", "maintainer", "none"}
ID = re.compile(r"^R-(\d{4}-\d{2}-\d{2})-[a-z]+$")


@pytest.fixture(scope="module")
def rulings() -> list[dict]:
    return yaml.safe_load((REPO / "docs" / "rulings" / "log.yaml").read_text(encoding="utf-8"))["rulings"]


def test_the_log_parses_and_has_entries(rulings):
    assert rulings


def test_every_entry_carries_the_required_fields(rulings):
    missing = [(r.get("id"), f) for r in rulings for f in REQUIRED if not str(r.get(f) or "").strip()]
    assert not missing, f"entries missing a required field: {missing}"


def test_dates_are_quoted_strings(rulings):
    bad = [r["id"] for r in rulings if not isinstance(r["date"], str)]
    assert not bad, f"unquoted dates: {bad}"


def test_enumerated_fields_take_declared_values(rulings):
    bad = [(r["id"], field, r.get(field)) for r in rulings
           for field, allowed in (("venue", VENUES), ("status", STATUSES), ("executor", EXECUTORS))
           if r.get(field) not in allowed]
    assert not bad, f"undeclared values: {bad}"


def test_ids_are_unique_and_carry_their_date(rulings):
    ids = [r["id"] for r in rulings]
    assert len(ids) == len(set(ids)), "a ruling id is reused"
    for r in rulings:
        m = ID.match(r["id"])
        assert m, f"{r['id']} is not R-<YYYY-MM-DD>-<letter>"
        assert m.group(1) == r["date"], f"{r['id']} disagrees with its date {r['date']}"


def test_entries_are_appended_in_date_order_and_not_from_the_future(rulings):
    dates = [date.fromisoformat(r["date"]) for r in rulings]
    assert dates == sorted(dates), "rulings are not in date order; the log is append-only"
    assert max(dates) <= date.today(), "a ruling is dated in the future"


def test_replacement_is_recorded_on_both_sides(rulings):
    ids = {r["id"] for r in rulings}
    for r in rulings:
        if r["status"] == "replaced":
            assert r.get("replaced_by") in ids, f"{r['id']} is replaced by nothing that exists"
        else:
            assert not r.get("replaced_by"), f"{r['id']} names a replacement but is {r['status']}"


def test_every_home_a_ruling_lands_in_exists(rulings):
    missing = [(r["id"], p) for r in rulings for p in r.get("lands_in") or [] if not (REPO / p).exists()]
    assert not missing, f"lands_in paths that do not exist: {missing}"


def _tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [REPO / line for line in out.splitlines() if (REPO / line).is_file()]


def test_no_tracked_file_names_a_private_note():
    # The names come from the maintainer's local .notes/, so no committed file has to spell them out.
    # In a clone there is no .notes/, and nothing to check.
    notes = REPO / ".notes"
    if not notes.exists():
        pytest.skip("no local .notes/")
    stems = {p.stem for p in notes.rglob("*") if p.is_file()}
    hits = sorted({f"{p.relative_to(REPO)}: {stem}" for p in _tracked_files()
                   for stem in stems if stem in p.read_text(encoding="utf-8", errors="replace")})
    assert not hits, f"tracked files that name a private note: {hits}"


def test_no_secret_or_grid_data_file_is_tracked():
    tracked = [str(p.relative_to(REPO)) for p in _tracked_files()]
    assert ".env" not in tracked
    grid = [t for t in tracked if t.startswith("sources/snapshots/grid/") and t != "sources/snapshots/grid/README.md"]
    assert not grid, f"grid data is tracked: {grid}"
