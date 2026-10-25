"""A route's carbon intensity: full SCI, (E x I) + M per 1,000 output tokens, with its parts kept separately.

E and M come from EcoLogits for the parameter counts in the model's record; I is each resolved grid's intensity
(build/grid_emissions.py: Ember's yearly value for its subdivision or country), for the grids the route's location
resolves to. Every value is computed as a Range and stored as {low, high}, rounded to 6 places.
"""

from __future__ import annotations

from collections.abc import Mapping

from ecologits.impacts.llm import compute_llm_impacts
from ecologits.utils.range_value import RangeValue

from build.constants.config import CARBON_BAND_UPPER, OUTPUT_TOKENS, PUE
from build.schemas.carbon_intensity import CarbonIntensity, Interval
from build.schemas.grid import GridIntensity
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
            if_electricity_mix_gwp=0.0,  # grid emissions are computed from the Ember table, not here
            if_electricity_mix_wue=0.0,
            datacenter_pue=pue,
            datacenter_wue=0.0,
        )
        energies.extend(v * 1000 for v in _bounds(impacts.energy.value))  # kWh -> Wh
        embodied.extend(v * 1000 for v in _bounds(impacts.embodied.gwp.value))  # kg -> g
    return Range(min(energies), max(energies)), Range(min(embodied), max(embodied))


def _interval(r: Range) -> Interval:
    """A range as a carbon_intensity: field stores it, rounded to 6 places."""
    return {"low": round(r.low, 6), "high": round(r.high, 6)}


def carbon_intensity(model: Model, grids: Mapping[str, GridIntensity]) -> CarbonIntensity:
    """A route's carbon intensity, (E x I) + M per 1,000 output tokens, with its parts and its grids, as its
    carbon_intensity: field stores it. `model` is the record of the model the route serves; `grids` the intensity of
    each grid its location resolves to, by grid name (none when the location is undisclosed)."""
    energy, embodied = ecologits_estimate(model)
    if not grids:
        return CarbonIntensity(
            grids=[],
            energy_wh=_interval(energy),
            embodied_g=_interval(embodied),
            grid_intensity_g_per_kwh=None,
            sci_g=None,
            band=None,
        )
    names = sorted(grids)
    values = [grids[g]["g_per_kwh"] for g in names]
    intensity = Range(min(values), max(values))
    sci = energy.times(intensity).scale(1 / 1000).plus(embodied)  # Wh x g/kWh / 1000 = g
    return CarbonIntensity(
        grids=names,
        energy_wh=_interval(energy),
        embodied_g=_interval(embodied),
        grid_intensity_g_per_kwh=_interval(intensity),
        sci_g=_interval(sci),
        band=list(band_span(sci, CARBON_BAND_UPPER)),
    )
