"""Helpers that apply the methodology constants in build/config.py."""

from __future__ import annotations

import math

from build.config import CARBON_BAND_UPPER
from build.ranges import Range

_LETTERS = {4: "A", 3: "B", 2: "C", 1: "D", 0: "E"}


def band(value: float, uppers: tuple[float, ...] = CARBON_BAND_UPPER) -> int:
    """Carbon band for a value: n when below uppers[n-1], otherwise the top band."""
    for number, upper in enumerate(uppers, start=1):
        if value < upper:
            return number
    return len(uppers) + 1


def band_span(r: Range) -> tuple[int, int]:
    """(lowest band, highest band) covered by a range."""
    return band(r.low), band(r.high)


def score_to_letter(score: int) -> str:
    """Location disclosure score (0-4) to letter (E-A)."""
    return _LETTERS[score]


def average_level_score(scores: list[int]) -> int | None:
    """Mean of level scores rounded to the nearest score, ties rounding down."""
    if not scores:
        return None
    mean = sum(scores) / len(scores)
    return math.ceil(mean - 0.5)
