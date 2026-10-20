from pathlib import Path

from build.constants import config

# Every methodology constant, pinned: changing one is a change of method, so it changes this file too.


def test_the_root_is_the_repository():
    assert config.ROOT == Path(__file__).resolve().parents[2]


def test_the_methodology_version():
    assert config.METHODOLOGY_VERSION == "0.1.0"


def test_the_carbon_band_edges():
    assert config.CARBON_BAND_UPPER == (0.03, 0.1, 0.3, 1.0)


def test_the_disclosure_points():
    assert config.DISCLOSURE_POINTS == {"A": 3, "B": 2, "C": 1, "D": 0}


def test_the_pue_range():
    assert config.PUE == (1.1, 1.6)


def test_the_functional_unit_is_1000_output_tokens():
    assert config.OUTPUT_TOKENS == 1000


def test_the_scoring_year():
    assert config.GRID_YEAR == 2025


def test_the_maximum_grid_age():
    assert config.MAX_GRID_AGE == 2


def test_the_site_is_a_draft():
    assert config.DRAFT is True
