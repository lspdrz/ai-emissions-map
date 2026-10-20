"""A grid: where a route's electricity comes from, with its yearly carbon intensity. sources/grids/<slug>.yaml.

Curated like every other record (docs/workflows/add-grid.md): each value is read from a published page and
recorded with its evidence and its method (basis, factors, gases)."""

from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import AfterValidator, Field, with_config

from build.schemas.common import RECORD, NonEmptyStr, Slug
from build.schemas.evidence import Evidence, has_primary

GCO2PerKWh = Annotated[float, Field(ge=0)]
Year = Annotated[str, Field(pattern=r"^\d{4}$", description="The year, quoted in YAML")]


@with_config(RECORD)
class Intensity(TypedDict):
    direct: NotRequired[
        Annotated[GCO2PerKWh, Field(description="gCO2(e)/kWh, direct (operational) factors: what the score uses")]
    ]
    lifecycle: NotRequired[Annotated[GCO2PerKWh, Field(description="gCO2(e)/kWh, life-cycle factors: shown alongside")]]
    gas: Annotated[Literal["co2e", "co2"], Field(description="co2 when the source counts carbon dioxide only")]
    source: Annotated[NonEmptyStr, Field(description="Who published the value")]
    evidence: list[Evidence]


def _measured(intensity: Intensity) -> Intensity:
    if "direct" not in intensity and "lifecycle" not in intensity:
        raise ValueError("needs direct or lifecycle")
    if not has_primary(intensity["evidence"]):
        raise ValueError("needs at least one primary source")
    return intensity


CheckedIntensity = Annotated[Intensity, AfterValidator(_measured)]


@with_config(RECORD)
class GridYear(TypedDict):
    consumption: NotRequired[CheckedIntensity]
    production: NotRequired[CheckedIntensity]


def _has_a_basis(year: GridYear) -> GridYear:
    if not year:
        raise ValueError("needs consumption or production")
    return year


@with_config(RECORD)
class Grid(TypedDict):
    name: Annotated[
        Slug, Field(description="The slug: the lowercased zone code where there is one; equals the filename stem")
    ]
    display_name: NonEmptyStr
    zone: NotRequired[
        Annotated[
            str,
            Field(
                pattern=r"^[A-Za-z0-9_-]+$", description="Electricity Maps' zone code; cloud regions resolve through it"
            ),
        ]
    ]
    country: Annotated[str, Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")]
    subdivided: NotRequired[
        Annotated[
            bool,
            Field(
                description="An aggregate zone with finer zones inside it (SE over SE1-SE4): naming it does not "
                "determine the grid"
            ),
        ]
    ]
    supply: NotRequired[
        Annotated[
            Literal["public", "onsite"],
            Field(description="onsite: a facility's own generation, not the public grid. Default public"),
        ]
    ]
    values: Annotated[dict[Year, Annotated[GridYear, AfterValidator(_has_a_basis)]], Field(min_length=1)]
    comments: NotRequired[str]


def _consistent(grid: Grid) -> Grid:
    if grid.get("supply") == "onsite" and "zone" in grid:
        raise ValueError("an onsite grid has no zone")
    return grid


# Grid with its rules that span fields: what build checks a grid file against.
CheckedGrid = Annotated[Grid, AfterValidator(_consistent)]
