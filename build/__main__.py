"""The commands: python -m build score, then python -m build release.

score   checks sources/ and the cloud-region table, and writes every disclosure_rating: and carbon_score: whose
        value changed.
        Run it after changing facts in sources/, and commit what it writes.
release validates sources/ and writes web/data/data.json from it, with the hash of its inputs. It computes
        nothing. Run it last, and commit what it writes.
check-carbon-scores, check-disclosure-ratings
        the CI gates: recompute every stored score and rating from the committed files, without writing
        anything, and fail on any that differs from what score would write.
check-site-data
        the CI gate on web/data/data.json: fails if it is out of date with what it was built from, or leaves
        its contract.
import-ember
        refreshes sources/snapshots/grid_intensity.csv from Ember's three yearly downloads (see
        sources/snapshots/README.md). Run score and release after it, and commit everything they write.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from build.constants.config import ROOT
from build.check_carbon_scores import check_carbon_scores
from build.check_disclosure_ratings import check_disclosure_ratings
from build.check_site_data import SiteDataCheck, check_site_data
from build.import_ember import Import, import_ember
from build.release import Release, release
from build.score import ScoreRun, score


def _score(args: argparse.Namespace) -> ScoreRun:
    return score(args.root)


def _release(args: argparse.Namespace) -> Release:
    return release(args.root, date.today())


def _check_carbon_scores(args: argparse.Namespace) -> ScoreRun:
    return check_carbon_scores(args.root)


def _check_disclosure_ratings(args: argparse.Namespace) -> ScoreRun:
    return check_disclosure_ratings(args.root)


def _check_site_data(args: argparse.Namespace) -> SiteDataCheck:
    return check_site_data(args.root)


def _import_ember(args: argparse.Namespace) -> Import:
    return import_ember(args.root, args.global_csv, args.us_csv, args.china_csv, date.today())


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(prog="python -m build", description=(__doc__ or "").partition("\n")[0])
    commands = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="{score,release,check-carbon-scores,check-disclosure-ratings,check-site-data,import-ember}",
    )
    for name, run, done, about in (
        ("score", _score, "nothing changed", "check sources/, write the disclosure_rating: and carbon_score: fields"),
        ("release", _release, "nothing changed", "validate sources/ and write web/data/data.json; computes nothing"),
        (
            "check-carbon-scores",
            _check_carbon_scores,
            "0 error(s)",
            "CI gate: every route's stored carbon score is what score would write now",
        ),
        (
            "check-disclosure-ratings",
            _check_disclosure_ratings,
            "0 error(s)",
            "CI gate: every stored disclosure letter and rating is what score would write now",
        ),
        (
            "check-site-data",
            _check_site_data,
            "0 error(s)",
            "CI gate: web/data/data.json is current with what it was built from and keeps to its contract",
        ),
        (
            "import-ember",
            _import_ember,
            "nothing changed",
            "refresh sources/snapshots/grid_intensity.csv from Ember's yearly downloads",
        ),
    ):
        command = commands.add_parser(name, parents=[common], help=about, description=about)
        command.set_defaults(run=run, done=done)
        if name == "import-ember":
            command.add_argument("--global-csv", type=Path, required=True, help="Ember's global yearly release")
            command.add_argument("--us-csv", type=Path, required=True, help="Ember's US-state yearly release")
            command.add_argument("--china-csv", type=Path, required=True, help="Ember's China-province yearly release")
    args = parser.parse_args(argv)
    run = args.run(args)
    errors, written = run.errors, run.written
    for e in errors:
        print("ERROR:", e)
    for p in written:
        print("wrote", p.relative_to(args.root).as_posix())
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    if not written:
        print(args.done)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
