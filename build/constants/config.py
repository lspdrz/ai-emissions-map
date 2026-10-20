"""
Methodology constants. Every value here is a documented, tunable choice; docs/METHODOLOGY.md states each.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

# The repository root: sources/, docs/ and web/ are found from here.
ROOT = Path(__file__).resolve().parents[2]

METHODOLOGY_VERSION = "0.1.0"

# Absolute carbon bands, gCO2e per 1k output tokens: band n when below CARBON_BAND_UPPER[n-1], else 5.
CARBON_BAND_UPPER: tuple[float, ...] = (0.03, 0.1, 0.3, 1.0)

# Points per location disclosure letter, for averaging an organization's routes: its letter is the nearest to the
# mean, ties rounding down. The letters are build.schemas.disclosure_rating.Letter, spelled out here because
# constants/ imports nothing from build/.
DISCLOSURE_POINTS: dict[Literal["A", "B", "C", "D"], int] = {"A": 3, "B": 2, "C": 1, "D": 0}

# Data-center overhead (Power Usage Effectiveness), applied by EcoLogits as its final step:
# request energy = PUE x IT energy. v1 uses ONE range for every route, from efficient hyperscale
# (~1.1) to the industry average (~1.56, Uptime Institute), so scores are not biased optimistic
# and only the grid differs between providers.
#
# TODO(v2, MAJOR, #10): use each facility's published PUE where one exists (e.g. Infomaniak 1.085,
# Google ~1.09), falling back to this range otherwise. PUE is a property of the building, like the
# grid zone, and varies from ~1.08 to 2.0+ in practice; a fixed range ignores real efficiency
# differences between operators.
PUE: tuple[float, float] = (1.1, 1.6)

# Functional unit: every route's score is express per this many output tokens.
OUTPUT_TOKENS = 1000

# The year of grid intensity every score uses: each grid's consumption-based direct value for it, or for its latest
# earlier year (docs/workflows/refresh-grids.md moves it forward).
GRID_YEAR = 2025

# A grid value more than this many years older than GRID_YEAR is flagged on the routes that use it. It does not change
# which value is used.
MAX_GRID_AGE = 2

# The site is noindex until the first public release (providers have not had their notice).
DRAFT = True
