"""Types shared inside build/ that are not records: what load_sources returns, and what the commands return to
__main__. A record in sources/ has its schema in build/schemas/ instead, which Pydantic validates; nothing here is
validated. Imports nothing from build/ but schemas/."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple, TypedDict

from build.schemas.grid import Grid
from build.schemas.model import Model
from build.schemas.organization import Organization
from build.schemas.route import Route
from build.schemas.score import OrgRating, RouteScore


class CloudRegion(TypedDict):
    """A cloud region as load_cloud_regions reads it from the cloud-region table: the grid zones it draws on, sorted,
    and its published PUE (None when it has none)."""

    zones: list[str]
    pue: float | None


class Sources(TypedDict):
    """Everything load_sources returns: each record keyed by its filename stem."""

    organizations: dict[str, Organization]
    grids: dict[str, Grid]
    routes: dict[str, Route]
    models: dict[str, Model]
    stray_files: list[str]


class ScoreRun(NamedTuple):
    """What python -m build score returns, and the CI gates check-carbon-intensities and check-disclosure-ratings compare."""

    errors: list[str]
    written: list[Path]  # with write=False: the files that would be written
    data: Mapping[str, Any] = {}  # the records as read, and every computed field: what the CI gates
    routes: Mapping[str, RouteScore] = {}  # compare (empty when there are errors)
    orgs: Mapping[str, OrgRating] = {}


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
