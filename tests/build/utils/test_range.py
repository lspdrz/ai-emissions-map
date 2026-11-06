import pytest

from build.utils.range import Range


def test_a_negative_end_is_refused():
    with pytest.raises(ValueError) as error:
        Range(-1.0, 1.0)
    assert str(error.value) == "Range values must be non-negative, got -1.0..1.0"


def test_a_low_end_above_the_high_end_is_refused():
    with pytest.raises(ValueError) as error:
        Range(2.0, 1.0)
    assert str(error.value) == "Range low 2.0 exceeds high 1.0"


def test_a_point_is_a_range_with_equal_ends():
    assert Range.point(3.0) == Range(3.0, 3.0)


def test_times_multiplies_the_low_ends_and_the_high_ends():
    product = Range(0.5, 0.6).times(Range(40.0, 330.0))
    assert (product.low, product.high) == (20.0, pytest.approx(198.0))


def test_plus_adds_the_low_ends_and_the_high_ends():
    total = Range(0.02, 0.198).plus(Range(0.05, 0.06))
    assert (total.low, total.high) == (pytest.approx(0.07), pytest.approx(0.258))


def test_scale_multiplies_both_ends_by_one_factor():
    scaled = Range(20.0, 198.0).scale(1 / 1000)
    assert (scaled.low, scaled.high) == (pytest.approx(0.02), pytest.approx(0.198))
