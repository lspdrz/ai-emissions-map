"""A route's carbon intensity, as `build.carbon_intensity.carbon_intensity` computes it and a route's
`carbon_intensity:` field stores it."""

from typing import TypedDict


class Interval(TypedDict):
    low: float
    high: float


class CarbonIntensity(TypedDict):
    grids: list[str]  # the grid files the location resolves to
    energy_wh: Interval  # E, Wh per 1,000 output tokens
    embodied_g: Interval  # M, gCO2e per 1,000 output tokens
    grid_intensity_g_per_kwh: Interval | None  # I: Ember's life-cycle value for each grid's subdivision or country
    sci_g: Interval | None  # (E x I) + M: the carbon intensity (SCI), life-cycle
    band: list[int] | None  # lowest and highest band of sci_g
