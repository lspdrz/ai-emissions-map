import inspect

from build import config, utils
from build.ranges import Range


def test_config_holds_only_constants():
    functions = [name for name, obj in vars(config).items() if inspect.isfunction(obj)]
    assert functions == []
    assert config.METHODOLOGY_VERSION == "0.1.0"
    assert config.VERIFICATION_WINDOW == 90


def test_location_precision_scores():
    assert config.LOCATION_PRECISION_SCORE == {
        "facility": 4, "region": 3, "country": 2, "country_set": 1, "unknown": 0,
    }
    assert not hasattr(config, "LOCATION_PRECISION_ORDER")  # the scores define the ranking
    assert not hasattr(config, "LEVEL_SCORE")


def test_carbon_bands():
    assert utils.band(0.0024) == 1
    assert utils.band(0.03) == 2
    assert utils.band(0.198) == 3
    assert utils.band(0.99) == 4
    assert utils.band(3.1) == 5
    assert utils.band_span(Range(0.015, 0.018)) == (1, 1)
    assert utils.band_span(Range(0.07, 0.258)) == (2, 3)


def test_score_to_letter():
    assert [utils.score_to_letter(s) for s in (4, 3, 2, 1, 0)] == ["A", "B", "C", "D", "E"]


def test_average_level_score_rounds_ties_down():
    assert utils.average_level_score([3, 3, 0]) == 2   # 2.0
    assert utils.average_level_score([3, 2]) == 2      # 2.5 -> down
    assert utils.average_level_score([4, 3]) == 3      # 3.5 -> down
    assert utils.average_level_score([4, 4, 3]) == 4   # 3.67
    assert utils.average_level_score([0]) == 0
    assert utils.average_level_score([]) is None
