from pathlib import Path

import pytest

from build.validate import load_sources

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def sources() -> dict:
    """The fixture corpus as load_sources returns it: plain dicts keyed by filename stem."""
    return load_sources(FIXTURES / "corpus")
