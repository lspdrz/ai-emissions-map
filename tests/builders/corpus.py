from collections.abc import Iterable, Mapping
from typing import Any, cast

from build.schemas.grid import Grid
from build.schemas.model import Model
from build.schemas.organization import Organization
from build.schemas.route import Route
from build.types import Sources


def make_corpus(
    *,
    organizations: list[Organization] | None = None,
    grids: list[Grid] | None = None,
    routes: list[Route] | None = None,
    models: list[Model] | None = None,
    stray_files: list[str] | None = None,
) -> Sources:
    """Records in the shape load_sources returns, keyed by name. A list left out is empty: the corpus holds only the
    records the test gives it."""
    return cast(
        Sources,
        make_raw_corpus(
            organizations=organizations, grids=grids, routes=routes, models=models, stray_files=stray_files
        ),
    )


def make_raw_corpus(
    *,
    organizations: Iterable[Mapping[str, Any]] | None = None,
    grids: Iterable[Mapping[str, Any]] | None = None,
    routes: Iterable[Mapping[str, Any]] | None = None,
    models: Iterable[Mapping[str, Any]] | None = None,
    stray_files: list[str] | None = None,
) -> dict[str, Any]:
    """Like make_corpus, but its records may be broken (see tests.builders.broken): what files on disk can hold,
    and so what build.validate.validate_sources receives."""
    return {
        "organizations": {r["name"]: r for r in organizations or []},
        "grids": {r["name"]: r for r in grids or []},
        "routes": {r["name"]: r for r in routes or []},
        "models": {r["name"]: r for r in models or []},
        "stray_files": stray_files or [],
    }
