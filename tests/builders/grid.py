from typing import Any

from pydantic import TypeAdapter

from build.schemas.grid import CheckedGrid, Grid, GridIntensity

_GRID = TypeAdapter(CheckedGrid)


def make_grid(name: str = "ch", country: str = "CH", zone: str | None = "CH", **overrides: Any) -> Grid:
    """A public grid, located by its zone and country. By default Switzerland."""
    record: dict[str, Any] = {"name": name, "display_name": name.upper(), "country": country}
    if zone is not None:
        record["zone"] = zone
    return _GRID.validate_python(record | overrides)


def make_grid_intensity(g_per_kwh: float = 30.0, year: int = 2025, geography: str = "CH") -> GridIntensity:
    """A grid's resolved intensity, as score writes it in the grid's intensity: field. By default Switzerland, 2025."""
    return GridIntensity(g_per_kwh=g_per_kwh, year=year, geography=geography, source="Ember")
