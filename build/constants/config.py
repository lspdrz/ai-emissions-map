"""
Methodology constants. Every value here is a documented, tunable choice; docs/METHODOLOGY.md states each.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

# The repository root: sources/, docs/ and web/ are found from here.
ROOT = Path(__file__).resolve().parents[2]

METHODOLOGY_VERSION = "0.4.0"

# Absolute carbon bands, gCO2e per 1k output tokens: band n when below CARBON_BAND_UPPER[n-1], else 5.
CARBON_BAND_UPPER: tuple[float, ...] = (0.03, 0.1, 0.3, 1.0)

# Points per location disclosure letter, for averaging an organization's routes: its letter is the nearest to the
# mean, ties rounding down. The letters are build.schemas.disclosure_rating.Letter, spelled out here because
# constants/ imports nothing from build/.
DISCLOSURE_POINTS: dict[Literal["A", "B", "C", "D"], int] = {"A": 3, "B": 2, "C": 1, "D": 0}

# Data-center overhead (Power Usage Effectiveness), applied by EcoLogits as its final step:
# request energy = PUE x IT energy. A route uses its candidates' published PUE when every candidate has one
# (build/score.py, route_pue); otherwise this range, from efficient hyperscale (Google's fleet: 1.09 in 2025,
# https://www.datacenters.google/efficiency) to the industry average (a weighted average of 1.54 in 2025, Uptime
# Institute Global Data Center Survey 2025, p. 7, n=681), so a route without a published PUE is not biased optimistic.
FALLBACK_PUE: tuple[float, float] = (1.09, 1.54)

# Functional unit: every route's carbon intensity is expressed per this many output tokens.
OUTPUT_TOKENS = 1000

# The year of grid data every carbon intensity uses: each grid's Ember value for this year, or for its latest earlier year
# (sources/snapshots/grid_intensity.csv; sources/snapshots/README.md says how to refresh it).
GRID_YEAR = 2025

# The site is noindex until the first public release (providers have not had their notice).
DRAFT = True
