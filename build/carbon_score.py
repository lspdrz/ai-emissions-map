"""A route's carbon score: full SCI, (E x I) + M per 1,000 output tokens, with its parts kept separately.

E and M come from EcoLogits for the parameter counts in the model's record; I comes from the grid files the route's
location resolves to. Every value is computed as a Range and stored as {low, high}, rounded to 6 places.
"""

from __future__ import annotations

from collections.abc import Mapping
from ecologits.impacts.llm import compute_llm_impacts
from ecologits.utils.range_value import RangeValue

from build.constants.config import CARBON_BAND_UPPER, GRID_YEAR, MAX_GRID_AGE, OUTPUT_TOKENS, PUE
from build.schemas.carbon_score import CarbonScore, Flag, GridValue, Interval
from build.schemas.grid import Grid
from build.schemas.model import Model
from build.utils.bands import band_span
from build.utils.range import Range


def _bounds(value) -> tuple[float, float]:
    """(low, high) of a number, a {min, max} dict (a model record's parameter count) or an object with .min and .max
    (EcoLogits' RangeValue)."""
    if isinstance(value, dict):
        return float(value["min"]), float(value["max"])
    if hasattr(value, "min"):
        return float(value.min), float(value.max)
    return float(value), float(value)


def ecologits_estimate(model: Model) -> tuple[Range, Range]:
    """(energy in Wh, embodied gCO2e) per 1,000 output tokens for the parameter counts in this model's record, from
    the pinned EcoLogits, with one PUE range for all routes and its own generation-speed estimate (no latency input).
    Tests replace it with their own E and M (monkeypatch)."""
    pue = RangeValue(min=PUE[0], max=PUE[1])
    energies: list[float] = []
    embodied: list[float] = []
    active_low, active_high = _bounds(model["active_b"])
    total_low, total_high = _bounds(model["total_b"])
    for active, total in ((active_low, total_low), (active_high, total_high)):
        impacts = compute_llm_impacts(
            model_active_parameter_count=active,
            model_total_parameter_count=total,
            output_token_count=OUTPUT_TOKENS,
            if_electricity_mix_adpe=0.0,
            if_electricity_mix_pe=0.0,
            if_electricity_mix_gwp=0.0,  # grid emissions are computed from the grid files, not here
            if_electricity_mix_wue=0.0,
            datacenter_pue=pue,
            datacenter_wue=0.0,
        )
        energies.extend(v * 1000 for v in _bounds(impacts.energy.value))  # kWh -> Wh
        embodied.extend(v * 1000 for v in _bounds(impacts.embodied.gwp.value))  # kg -> g
    return Range(min(energies), max(energies)), Range(min(embodied), max(embodied))


def grid_value(grid: Grid, scoring_year: int) -> GridValue:
    """The one value of `grid` a score uses: its consumption-based value with a direct figure, for the newest year up
    to `scoring_year` (GRID_YEAR when scoring). A year after scoring_year is never used; production-based values and
    life-cycle figures never stand in.

    ValueError if the grid has no such value, which validation refuses before any score."""
    for year in sorted((int(year) for year in grid["values"] if int(year) <= scoring_year), reverse=True):
        intensity = grid["values"][str(year)].get("consumption")
        if intensity is not None and "direct" in intensity:
            return GridValue(
                year=year,
                intensity=intensity["direct"],
                lifecycle=intensity.get("lifecycle"),
                gas=intensity["gas"],
            )
    raise ValueError(f"grids/{grid['name']}.yaml: no consumption-based direct value for {scoring_year} or earlier")


def value_flags(value: GridValue, scoring_year: int, max_age: int) -> list[Flag]:
    """What a reader must be told about a value, without it changing which value is used: CO2 only, or a year more
    than `max_age` (MAX_GRID_AGE when scoring) years older than `scoring_year` (GRID_YEAR when scoring)."""
    flags: list[Flag] = []
    if value["gas"] == "co2":
        flags.append("gas")
    if value["year"] < scoring_year - max_age:
        flags.append("year")
    return flags


def _interval(r: Range) -> Interval:
    """A range as a carbon_score: field stores it, rounded to 6 places."""
    return {"low": round(r.low, 6), "high": round(r.high, 6)}


def carbon_score(model: Model, grids: Mapping[str, Grid]) -> CarbonScore:
    """A route's carbon score, (E x I) + M per 1,000 output tokens, with its parts, its grids and its flags, as its
    carbon_score: field stores it. `model` is the record of the model the route serves; `grids` the grid files its
    location resolves to (none when the location is undisclosed)."""
    energy, embodied = ecologits_estimate(model)
    if not grids:
        return CarbonScore(
            grids=[],
            energy_wh=_interval(energy),
            embodied_g=_interval(embodied),
            intensity_g_per_kwh=None,
            score_g=None,
            score_lifecycle_g=None,
            band=None,
            flags={},
        )
    names = sorted(grids)
    grid_values = {g: grid_value(grids[g], GRID_YEAR) for g in names}
    intensity = Range(
        min(v["intensity"] for v in grid_values.values()),
        max(v["intensity"] for v in grid_values.values()),
    )
    score = energy.times(intensity).scale(1 / 1000).plus(embodied)  # Wh x g/kWh / 1000 = g
    lifecycles = [v["lifecycle"] for v in grid_values.values() if v["lifecycle"] is not None]
    lifecycle = (
        energy.times(Range(min(lifecycles), max(lifecycles))).scale(1 / 1000).plus(embodied)
        if len(lifecycles) == len(grid_values)
        else None
    )
    flags: dict[Flag, list[str]] = {}
    for g in names:
        for f in value_flags(grid_values[g], GRID_YEAR, MAX_GRID_AGE):
            flags.setdefault(f, []).append(g)
    return CarbonScore(
        grids=names,
        energy_wh=_interval(energy),
        embodied_g=_interval(embodied),
        intensity_g_per_kwh=_interval(intensity),
        score_g=_interval(score),
        score_lifecycle_g=_interval(lifecycle) if lifecycle else None,
        band=list(band_span(score, CARBON_BAND_UPPER)),
        flags=dict(sorted(flags.items())),
    )
