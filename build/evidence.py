"""Evidence verification window (spec §9)."""

from __future__ import annotations

from datetime import date, timedelta

from build.config import VERIFICATION_WINDOW


def verified(location: dict, release: date) -> bool:
    """The claim rests on primary evidence and was re-confirmed within VERIFICATION_WINDOW days of the release
    (inclusive). A date after the release is a typo or a rebuild of an old release, and does not count."""
    last_verified = date.fromisoformat(location["last_verified"])
    recent = release - timedelta(days=VERIFICATION_WINDOW) <= last_verified <= release
    return recent and any(e["kind"] == "primary" for e in location["evidence"])


def location_established(location: dict, release: date) -> bool:
    return location["confidence"] != "unknown" and verified(location, release)
