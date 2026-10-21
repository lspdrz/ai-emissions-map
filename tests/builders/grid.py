from typing import Any

from pydantic import TypeAdapter

from build.schemas.grid import CheckedGrid, Grid, GridIntensity

_GRID = TypeAdapter(CheckedGrid)


_DEFAULT: Any = object()  # make_grid's intensity when none is passed: a value for its geography


def make_grid(
    name: str = "ch",
    country: str = "CH",
    zone: str | None = "CH",
    intensity: GridIntensity | None = _DEFAULT,
    **overrides: Any,
) -> Grid:
    """A public grid, located by its zone and country, with the intensity: grid-emissions would have written (30
    gCO2e/kWh for 2025, for its subdivision or country). By default Switzerland. intensity=None leaves it out."""
    record: dict[str, Any] = {"name": name, "display_name": name.upper(), "country": country}
    if zone is not None:
        record["zone"] = zone
    record |= overrides
    if intensity is _DEFAULT:
        geography = f"{country}-{record['subdivision']}" if "subdivision" in record else country
        intensity = make_grid_intensity(geography=geography)
    if intensity is not None:
        record["intensity"] = intensity
    return _GRID.validate_python(record)


def make_grid_intensity(g_per_kwh: float = 30.0, year: int = 2025, geography: str = "CH") -> GridIntensity:
    """A grid's resolved intensity, as grid-emissions writes it in its intensity: field. By default Switzerland, 2025."""
    return GridIntensity(g_per_kwh=g_per_kwh, year=year, geography=geography, source="Ember")
