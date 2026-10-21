from typing import Any, cast

from pydantic import TypeAdapter

from build.schemas.grid import CheckedGrid, Grid, GridYear, Intensity
from tests.builders.evidence import make_evidence

_GRID = TypeAdapter(CheckedGrid)


def make_intensity(direct: float | None = 30.0, lifecycle: float | None = 45.0, **overrides: Any) -> Intensity:
    """One basis of one year: consumption-based values in CO2e, on a primary source. None leaves a value out."""
    value: dict[str, Any] = {
        "gas": "co2e",
        "source": "Example Grid Operator",
        "evidence": [
            make_evidence(url="https://grid-operator.example/annual-review", shows='Annual review: "30 gCO2e/kWh"')
        ],
    }
    if direct is not None:
        value["direct"] = direct
    if lifecycle is not None:
        value["lifecycle"] = lifecycle
    return cast(Intensity, value | overrides)


def make_grid(
    name: str = "ch",
    country: str = "CH",
    zone: str | None = "CH",
    values: dict[str, GridYear] | None = None,
    **overrides: Any,
) -> Grid:
    """A public grid with a consumption-based value for 2025. By default Switzerland."""
    record: dict[str, Any] = {
        "name": name,
        "display_name": name.upper(),
        "country": country,
        "values": {"2025": {"consumption": make_intensity()}} if values is None else values,
    }
    if zone is not None:
        record["zone"] = zone
    return _GRID.validate_python(record | overrides)
