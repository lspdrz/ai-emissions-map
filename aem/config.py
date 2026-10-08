"""Methodology constants. Every value here is a documented, tunable choice (spec §8-§9).

Only constants live here; functions that use them are in aem/utils.py.
"""

from __future__ import annotations

METHODOLOGY_VERSION = "0.1.0"

# Absolute carbon bands, gCO2e per 1k output tokens: band n when below CARBON_BAND_UPPER[n-1], else 5.
CARBON_BAND_UPPER: tuple[float, ...] = (0.03, 0.1, 0.3, 1.0)

# Data-center overhead (Power Usage Effectiveness), applied by EcoLogits as its final step:
# request energy = PUE x IT energy. v1 uses ONE range for every route, from efficient hyperscale
# (~1.1) to the industry average (~1.56, Uptime Institute), so scores are not biased optimistic
# and only the grid differs between providers.
#
# TODO(v2, MAJOR): use each facility's published PUE where one exists (e.g. Infomaniak 1.085,
# Google ~1.09), falling back to this range otherwise. PUE is a property of the building, like the
# grid zone, and varies from ~1.08 to 2.0+ in practice; a fixed range ignores real efficiency
# differences between operators.
PUE: tuple[float, float] = (1.1, 1.6)

# Functional unit: every route's score is express per this many output tokens.
OUTPUT_TOKENS = 1000

# Days before a release within which location evidence must have been re-verified to count.
VERIFICATION_WINDOW = 90

# Location disclosure score per precision level.
LOCATION_PRECISION_SCORE: dict[str, int] = {
    "facility": 4,
    "region": 3,
    "country": 2,
    "country_set": 1,
    "unknown": 0,
}
