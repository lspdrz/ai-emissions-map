"""Everything load_sources returns: each record keyed by its filename stem."""

from typing import TypedDict

from build.schemas.grid import Grid
from build.schemas.model import Model
from build.schemas.organization import Organization
from build.schemas.route import Route


class Sources(TypedDict):
    organizations: dict[str, Organization]
    grids: dict[str, Grid]
    routes: dict[str, Route]
    models: dict[str, Model]
    stray_files: list[str]
