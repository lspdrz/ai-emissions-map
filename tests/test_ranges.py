import pytest

from aem.ranges import Range


def test_range_rejects_inverted_and_negative():
    with pytest.raises(ValueError):
        Range(2.0, 1.0)
    with pytest.raises(ValueError):
        Range(-1.0, 1.0)


def test_range_arithmetic():
    operational = Range(0.5, 0.6).times(Range(40.0, 330.0)).scale(1 / 1000)
    assert operational.low == pytest.approx(0.02)
    assert operational.high == pytest.approx(0.198)
    score = operational.plus(Range(0.05, 0.06))
    assert score.low == pytest.approx(0.07)
    assert score.high == pytest.approx(0.258)
    assert Range.point(3.0) == Range(3.0, 3.0)
    assert Range.union([Range(1, 2), Range(0.5, 1.5)]) == Range(0.5, 2)


def test_union_of_nothing_is_an_error():
    with pytest.raises(ValueError):
        Range.union([])


def test_sort_key_is_geometric_midpoint_and_handles_zero():
    assert Range(4.0, 16.0).sort_key() == pytest.approx(8.0)
    assert Range(0.0, 10.0).sort_key() == pytest.approx(5.0)
