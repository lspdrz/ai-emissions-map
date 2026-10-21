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
    intensity_g_per_kwh: Interval | None  # I: Ember's life-cycle value for each grid's subdivision or country
    intensity_years: list[int]  # the years of the Ember values I uses, sorted; empty when not scored
    score_g: Interval | None  # (E x I) + M: the carbon score, life-cycle
    band: list[int] | None  # lowest and highest band of score_g
