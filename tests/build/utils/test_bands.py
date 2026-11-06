from build.utils.bands import band, band_span
from build.utils.range import Range

# Every test gives its own band edges: band 1 below 0.03, 2 below 0.1, 3 below 0.3, 4 below 1, and 5 at 1 or above.


def test_a_value_below_the_first_edge_is_band_1():
    assert band(0.0024, uppers=(0.03, 0.1, 0.3, 1.0)) == 1


def test_a_value_between_two_edges_is_the_band_below_the_upper_one():
    assert band(0.198, uppers=(0.03, 0.1, 0.3, 1.0)) == 3


def test_a_value_on_an_edge_is_the_band_above_it():
    assert band(0.03, uppers=(0.03, 0.1, 0.3, 1.0)) == 2


def test_a_value_on_the_last_edge_is_the_top_band():
    assert band(1.0, uppers=(0.03, 0.1, 0.3, 1.0)) == 5


def test_a_value_above_the_last_edge_is_the_top_band():
    assert band(3.1, uppers=(0.03, 0.1, 0.3, 1.0)) == 5


def test_a_range_within_one_band_spans_that_band():
    assert band_span(Range(0.015, 0.018), uppers=(0.03, 0.1, 0.3, 1.0)) == (1, 1)


def test_a_range_across_bands_spans_its_lowest_and_highest_band():
    assert band_span(Range(0.07, 0.258), uppers=(0.03, 0.1, 0.3, 1.0)) == (2, 3)
