"""A route's carbon score, as `build.carbon_score.carbon_score` computes it and a route's `carbon_score:` field stores
it."""

from typing import TypedDict


class Interval(TypedDict):
    low: float
    high: float


class CarbonScore(TypedDict):
    grids: list[str]  # the grid files the location resolves to
    energy_wh: Interval  # E, Wh per 1,000 output tokens
    embodied_g: Interval  # M, gCO2e per 1,000 output tokens
    intensity_g_per_kwh: Interval | None  # I: EcoLogits' life-cycle electricity mix for each grid's country
    score_g: Interval | None  # (E x I) + M: the carbon score, life-cycle
    band: list[int] | None  # lowest and highest band of score_g
