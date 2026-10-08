"""Non-negative closed intervals used for every estimate in the map."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Range:
    low: float
    high: float

    def __post_init__(self) -> None:
        if self.low < 0 or self.high < 0:
            raise ValueError(f"Range values must be non-negative, got {self.low}..{self.high}")
        if self.low > self.high:
            raise ValueError(f"Range low {self.low} exceeds high {self.high}")

    @classmethod
    def point(cls, value: float) -> Range:
        return cls(value, value)

    def times(self, other: Range) -> Range:
        """Interval product; valid because both ranges are non-negative."""
        return Range(self.low * other.low, self.high * other.high)

    def plus(self, other: Range) -> Range:
        """Interval sum."""
        return Range(self.low + other.low, self.high + other.high)

    def scale(self, factor: float) -> Range:
        return Range(self.low * factor, self.high * factor)

    @classmethod
    def union(cls, ranges: Iterable[Range]) -> Range:
        items = list(ranges)
        if not items:
            raise ValueError("Cannot take the union of no ranges")
        return cls(min(r.low for r in items), max(r.high for r in items))

    def sort_key(self) -> float:
        """Geometric midpoint, used only for ordering, never displayed as a value."""
        if self.low == 0:
            return self.high / 2
        return math.sqrt(self.low * self.high)

    def to_dict(self) -> dict[str, float]:
        return {"low": self.low, "high": self.high}
