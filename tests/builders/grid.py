from typing import Any

from pydantic import TypeAdapter

from build.schemas.grid import CheckedGrid, Grid

_GRID = TypeAdapter(CheckedGrid)


def make_grid(name: str = "ch", country: str = "CH", zone: str | None = "CH", **overrides: Any) -> Grid:
    """A public grid, located by its zone and country. By default Switzerland."""
    record: dict[str, Any] = {"name": name, "display_name": name.upper(), "country": country}
    if zone is not None:
        record["zone"] = zone
    return _GRID.validate_python(record | overrides)
