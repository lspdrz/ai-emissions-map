"""A route's carbon score: full SCI, (E x I) + M per 1,000 output tokens, with its parts kept separately.

E and M come from EcoLogits for the parameter counts in the model's record; I is EcoLogits' electricity mix for the
country of each grid the route's location resolves to (life-cycle, from Our World in Data). Every value is computed
as a Range and stored as {low, high}, rounded to 6 places.
"""

from __future__ import annotations

from collections.abc import Mapping

import pycountry
from ecologits.electricity_mix_repository import electricity_mixes
from ecologits.impacts.llm import compute_llm_impacts
from ecologits.utils.range_value import RangeValue

from build.constants.config import CARBON_BAND_UPPER, OUTPUT_TOKENS, PUE
from build.schemas.carbon_score import CarbonScore, Interval
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
            if_electricity_mix_gwp=0.0,  # grid emissions are computed from the grids' countries, not here
            if_electricity_mix_wue=0.0,
            datacenter_pue=pue,
            datacenter_wue=0.0,
        )
        energies.extend(v * 1000 for v in _bounds(impacts.energy.value))  # kWh -> Wh
        embodied.extend(v * 1000 for v in _bounds(impacts.embodied.gwp.value))  # kg -> g
    return Range(min(energies), max(energies)), Range(min(embodied), max(embodied))


def ecologits_grid_intensity(country: str) -> float | None:
    """The carbon intensity, gCO2e/kWh, of EcoLogits' electricity mix for a country (ISO 3166-1 alpha-2): its life-cycle
    value from Our World in Data, per country. None when EcoLogits has no mix for it. Tests replace it with their own
    intensities (monkeypatch)."""
    found = pycountry.countries.get(alpha_2=country)
    mix = electricity_mixes.find_electricity_mix(found.alpha_3) if found else None
    return mix.gwp * 1000 if mix else None  # kgCO2e/kWh -> gCO2e/kWh


def grid_intensity(grid: Grid) -> float:
    """The intensity a score uses for a grid: EcoLogits' mix for its country.

    ValueError for an on-site grid (a facility's own generation, which a country's mix does not describe) or a
    country EcoLogits has no mix for; validation refuses both before any score."""
    if grid.get("supply") == "onsite":
        raise ValueError(f"grids/{grid['name']}.yaml: an on-site grid has no EcoLogits country mix")
    intensity = ecologits_grid_intensity(grid["country"])
    if intensity is None:
        raise ValueError(f"grids/{grid['name']}.yaml: EcoLogits has no electricity mix for {grid['country']!r}")
    return intensity


def _interval(r: Range) -> Interval:
    """A range as a carbon_score: field stores it, rounded to 6 places."""
    return {"low": round(r.low, 6), "high": round(r.high, 6)}


def carbon_score(model: Model, grids: Mapping[str, Grid]) -> CarbonScore:
    """A route's carbon score, (E x I) + M per 1,000 output tokens, with its parts and its grids, as its carbon_score:
    field stores it. `model` is the record of the model the route serves; `grids` the grid files its location resolves
    to (none when the location is undisclosed)."""
    energy, embodied = ecologits_estimate(model)
    if not grids:
        return CarbonScore(
            grids=[],
            energy_wh=_interval(energy),
            embodied_g=_interval(embodied),
            intensity_g_per_kwh=None,
            score_g=None,
            band=None,
        )
    names = sorted(grids)
    intensities = [grid_intensity(grids[g]) for g in names]
    intensity = Range(min(intensities), max(intensities))
    score = energy.times(intensity).scale(1 / 1000).plus(embodied)  # Wh x g/kWh / 1000 = g
    return CarbonScore(
        grids=names,
        energy_wh=_interval(energy),
        embodied_g=_interval(embodied),
        intensity_g_per_kwh=_interval(intensity),
        score_g=_interval(score),
        band=list(band_span(score, CARBON_BAND_UPPER)),
    )
