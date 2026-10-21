"""Types shared inside build/ that are not records: what the commands pass between them. A record in sources/ has its
schema in build/schemas/ instead, which Pydantic validates; nothing here is validated. Imports nothing from build/."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class Import(NamedTuple):
    """What a snapshot import (python -m build import-ember, import-cloud-regions) returns: its errors, and the files
    whose content it changed."""

    errors: list[str]
    written: list[Path]
