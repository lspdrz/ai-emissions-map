"""
Carbon bands: which band a value falls in, given the band edges (CARBON_BAND_UPPER in build/constants/config.py
for a route's carbon intensity).
"""

from __future__ import annotations

from build.utils.range import Range


def band(value: float, uppers: tuple[float, ...]) -> int:
    """Carbon band for a value: n when below uppers[n-1], otherwise the top band."""
    for number, upper in enumerate(uppers, start=1):
        if value < upper:
            return number
    return len(uppers) + 1


def band_span(r: Range, uppers: tuple[float, ...]) -> tuple[int, int]:
    """(lowest band, highest band) covered by a range."""
    return band(r.low, uppers), band(r.high, uppers)
