"""Gate: the committed web/data/data.json is current with what it was built from, and keeps to its contract.

Current: its meta.inputs_sha equals the hash of the records, build/'s code and the EcoLogits version now, so a pull
request that changes any of them without rerunning `python -m build release` fails. Within its contract: every field
is one the site displays, so a hand edit that adds one fails. CI runs it.

    uv run python -m build check-site-data
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from build.generate_site_data import check_contract
from build.release import DATA_FILE, inputs_sha

RUN = "run `python -m build release`"


class SiteDataCheck(NamedTuple):
    errors: list[str]
    written: list[Path]  # always empty: the gate writes nothing


def check_site_data(root: Path) -> SiteDataCheck:
    """python -m build check-site-data: one message if data.json is missing, unreadable or out of date, and one per
    field outside its contract. Writes nothing."""
    try:
        data = json.loads((root / DATA_FILE).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return SiteDataCheck([f"{DATA_FILE.as_posix()}: is missing; {RUN}"], [])
    except json.JSONDecodeError:
        return SiteDataCheck([f"{DATA_FILE.as_posix()}: is not valid JSON (a merge conflict?); {RUN}"], [])
    errors = []
    if data.get("meta", {}).get("inputs_sha") != inputs_sha(root):
        errors.append(
            f"{DATA_FILE.as_posix()}: is out of date: sources/ or build/ changed since the last release; {RUN}"
        )
    errors += [f"{DATA_FILE.as_posix()}: {problem}" for problem in check_contract(data)]
    return SiteDataCheck(errors, [])
