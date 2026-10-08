import pytest

from build.energy import EcoLogitsEnergyModel, FixedEnergyModel
from build.ranges import Range


def spec(active, total):
    return {"active_b": Range.point(active), "total_b": Range.point(total), "source": "curated"}


def test_fixed_model_returns_table_values():
    model = FixedEnergyModel({"m": (Range(0.5, 0.6), Range(0.05, 0.06))})
    assert model.estimate("m", spec(70, 70)) == (Range(0.5, 0.6), Range(0.05, 0.06))


def test_fixed_model_rejects_unknown():
    with pytest.raises(KeyError):
        FixedEnergyModel({}).estimate("x", spec(1, 1))


# Reference values from EcoLogits 0.11.2, PUE 1.1-1.6, no latency input (verified 2026-10-08).
@pytest.mark.ecologits
@pytest.mark.parametrize("active,total,low,high,embodied", [
    (8, 8, 0.0817, 0.1189, 0.0073),
    (70, 70, 0.6027, 0.8767, 0.0566),
    (41, 675, 3.7897, 5.5123, 0.3503),
])
def test_matches_pinned_ecologits(active, total, low, high, embodied):
    energy, m = EcoLogitsEnergyModel().estimate("x", spec(active, total))
    assert energy.low == pytest.approx(low, abs=0.002)
    assert energy.high == pytest.approx(high, abs=0.002)
    assert m.low == pytest.approx(embodied, abs=0.0005)


@pytest.mark.ecologits
def test_closed_model_parameter_range_widens_estimate():
    closed = {"active_b": Range(100, 300), "total_b": Range(100, 300), "source": "ecologits"}
    energy, _ = EcoLogitsEnergyModel().estimate("closed", closed)
    small, _ = EcoLogitsEnergyModel().estimate("s", spec(100, 100))
    large, _ = EcoLogitsEnergyModel().estimate("l", spec(300, 300))
    assert energy.low == pytest.approx(small.low) and energy.high == pytest.approx(large.high)
