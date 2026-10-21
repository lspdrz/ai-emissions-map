"""A grid: where a route's electricity comes from. sources/grids/<slug>.yaml.

A grid file records location only (docs/workflows/add-grid.md): its zone, its country and its supply. Its carbon
intensity is not curated: every score uses EcoLogits' electricity mix for the grid's country (build/carbon_score.py).
"""

from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import AfterValidator, Field, with_config

from build.schemas.common import RECORD, NonEmptyStr, Slug


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
            description="ISO 3166-1 alpha-2: the country whose EcoLogits electricity mix gives the grid's intensity",
        ),
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


def _consistent(grid: Grid) -> Grid:
    if grid.get("supply") == "onsite" and "zone" in grid:
        raise ValueError("an onsite grid has no zone")
    return grid


# Grid with its rules that span fields: what build checks a grid file against.
CheckedGrid = Annotated[Grid, AfterValidator(_consistent)]
