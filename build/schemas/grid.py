"""A grid: where a route's electricity comes from. sources/grids/<slug>.yaml.

A grid file records location only (docs/workflows/add-grid.md): its zone, its country (and subdivision, such as a US
state or Chinese province) and its supply. Its carbon intensity is not curated: `python -m build score` writes Ember's yearly value for the grid's subdivision
where it names one, else its country, at the end of the file as its `intensity:` field (build/grid_emissions.py).
"""

from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import AfterValidator, Field, with_config

from build.schemas.common import RECORD, NonEmptyStr, Slug


class GridIntensity(TypedDict):
    """A grid's intensity, as `build.grid_emissions.grid_intensity` resolves it from Ember's table and a grid's
    `intensity:` field stores it."""

    g_per_kwh: float  # I: Ember's life-cycle intensity of generation, gCO2e/kWh
    year: int  # the year of the value: GRID_YEAR, or the geography's latest earlier year
    geography: str  # the Ember geography it is for: a country (CH) or a subdivision (US-VA, CN-GD)
    source: Literal["Ember"]


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
    country: Annotated[
        str,
        Field(
            pattern=r"^[A-Z]{2}$",
            description="ISO 3166-1 alpha-2: the country whose Ember value gives the grid's intensity",
        ),
    ]
    subdivision: NotRequired[
        Annotated[
            str,
            Field(
                pattern=r"^[A-Z0-9]{1,3}$",
                description="The ISO 3166-2 subdivision within the country (VA for US-VA, GD for CN-GD) whose Ember "
                "value gives the grid's intensity; validation checks Ember has one",
            ),
        ]
    ]
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
    comments: NotRequired[str]
    intensity: NotRequired[
        Annotated[
            GridIntensity,
            Field(description="Written by `python -m build score` from Ember's table; part of curation"),
        ]
    ]


def _consistent(grid: Grid) -> Grid:
    if grid.get("supply") == "onsite" and "zone" in grid:
        raise ValueError("an onsite grid has no zone")
    return grid


# Grid with its rules that span fields: what build checks a grid file against.
CheckedGrid = Annotated[Grid, AfterValidator(_consistent)]
