"""A route's carbon score, as `build.carbon_score.carbon_score` computes it and a route's `carbon_score:` field stores it,
and the grid values it is computed from."""

from typing import Literal, TypedDict


class GridValue(TypedDict):
    """The one value of a grid a score uses, chosen in build/carbon_score.py: the grid's consumption-based value for
    the newest year up to the scoring year that has a direct figure."""

    year: int
    intensity: float  # the direct figure the score uses, gCO2(e)/kWh
    lifecycle: float | None  # the life-cycle figure recorded with it, for the life-cycle score
    gas: Literal["co2e", "co2"]


# What a reader must be told about a grid's value, without it changing which value is used: CO2 only, or a year more
# than the maximum grid age older than the scoring year.
Flag = Literal["gas", "year"]


class Interval(TypedDict):
    low: float
    high: float


class CarbonScore(TypedDict):
    grids: list[str]  # the grid files the location resolves to
    energy_wh: Interval  # E, Wh per 1,000 output tokens
    embodied_g: Interval  # M, gCO2e per 1,000 output tokens
    intensity_g_per_kwh: Interval | None  # I: the grids' consumption-based direct values
    score_g: Interval | None  # (E x I) + M: the carbon score
    score_lifecycle_g: Interval | None  # the same with life-cycle factors, shown alongside
    band: list[int] | None  # lowest and highest band of score_g
    flags: dict[Flag, list[str]]  # what a reader must be told, and the grids it concerns
