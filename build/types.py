"""Types shared inside build/ that are not records: what the commands return to __main__. A record in sources/ has its
schema in build/schemas/ instead, which Pydantic validates; nothing here is validated. Imports nothing from build/."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class GridRun(NamedTuple):
    """What python -m build grid-emissions returns: each grid whose stored intensity differs (or, with --write, the
    grid files it wrote)."""

    errors: list[str]
    written: list[Path]


class Release(NamedTuple):
    """What python -m build release returns: its errors, and web/data/data.json if it wrote it."""

    errors: list[str]
    written: list[Path]


class SiteDataCheck(NamedTuple):
    """What python -m build check-site-data returns: its errors."""

    errors: list[str]
    written: list[Path]  # always empty: the gate writes nothing


class Import(NamedTuple):
    """What a snapshot import (python -m build import-ember, import-cloud-regions) returns: its errors, and the files
    whose content it changed."""

    errors: list[str]
    written: list[Path]
