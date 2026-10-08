"""Energy (E) and embodied emissions (M) per 1,000 output tokens: a property of the model only (spec §8)."""

from __future__ import annotations

from typing import Protocol

from build.config import OUTPUT_TOKENS, PUE
from build.ranges import Range


class EnergyModel(Protocol):
    def estimate(self, model: str, spec: dict) -> tuple[Range, Range]:
        """Return (energy in Wh per 1k output tokens, embodied gCO2e per 1k output tokens).

        `spec` is the model's entry from build.models.model_specs.
        """
        ...


class FixedEnergyModel:
    """Table-driven model for tests and offline runs, keyed by model id."""

    def __init__(self, table: dict[str, tuple[Range, Range]]):
        self.table = table

    def estimate(self, model: str, spec: dict) -> tuple[Range, Range]:
        return self.table[model]


def _bounds(value) -> tuple[float, float]:
    """EcoLogits returns floats or RangeValue objects with .min/.max."""
    if hasattr(value, "min"):
        return float(value.min), float(value.max)
    return float(value), float(value)


class EcoLogitsEnergyModel:
    """Pinned EcoLogits with one PUE range for all routes and its own generation-speed estimate (no latency input)."""

    def estimate(self, model: str, spec: dict) -> tuple[Range, Range]:
        from ecologits.impacts.llm import compute_llm_impacts
        from ecologits.utils.range_value import RangeValue

        pue = RangeValue(min=PUE[0], max=PUE[1])
        energies: list[float] = []
        embodied: list[float] = []
        for active, total in ((spec["active_b"].low, spec["total_b"].low), (spec["active_b"].high, spec["total_b"].high)):
            impacts = compute_llm_impacts(
                model_active_parameter_count=active,
                model_total_parameter_count=total,
                output_token_count=OUTPUT_TOKENS,
                if_electricity_mix_adpe=0.0,
                if_electricity_mix_pe=0.0,
                if_electricity_mix_gwp=0.0,  # grid emissions are computed from Electricity Maps, not here
                if_electricity_mix_wue=0.0,
                datacenter_pue=pue,
                datacenter_wue=0.0,
            )
            energies.extend(v * 1000 for v in _bounds(impacts.energy.value))  # kWh -> Wh
            embodied.extend(v * 1000 for v in _bounds(impacts.embodied.gwp.value))  # kg -> g
        return Range(min(energies), max(energies)), Range(min(embodied), max(embodied))
