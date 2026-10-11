import pytest

from build.grid import GridError, intensity_range, load_cloud_regions, load_grid, resolve_zones
from build.ranges import Range


@pytest.fixture
def grid(fixtures_dir):
    return load_grid(fixtures_dir / "grid.csv")


@pytest.fixture
def cloud(fixtures_dir):
    return load_cloud_regions(fixtures_dir / "cloud_regions.csv")


def _location(sources, route):
    return sources["routes"][route]["location"]


def test_load_grid_and_cloud(grid, cloud):
    assert grid["CH"] == {"direct": 30.0, "lifecycle": 45.0, "fallback": False, "source": "electricitymaps"}
    assert cloud[("cloudx", "eu-de")] == ["DE"]


def test_candidates_resolve_to_zones(sources, cloud):
    facilities = sources["facilities"]
    assert resolve_zones(_location(sources, "alpinehost-test-70b"), facilities, cloud) == ["CH"]
    assert resolve_zones(_location(sources, "multihost-test-70b"), facilities, cloud) == ["DE", "FR"]
    assert resolve_zones(_location(sources, "alpinehost-test-8b"), facilities, cloud) == ["CH"]


def test_unknown_location_cannot_be_resolved(sources, cloud):
    with pytest.raises(GridError, match="unknown"):
        resolve_zones(_location(sources, "vaguehost-test-70b"), sources["facilities"], cloud)


def test_intensity_ranges_by_basis(grid):
    assert intensity_range(["DE", "FR"], grid, "direct") == Range(40, 330)
    assert intensity_range(["DE", "FR"], grid, "lifecycle") == Range(60, 380)


def test_missing_zone_raises_named_error(grid):
    with pytest.raises(GridError, match="NL"):
        intensity_range(["DE", "NL"], grid, "direct")


def test_unrecognised_candidate(sources, cloud):
    location = {"confidence": "country", "candidates": ["planet:mars"], "evidence": []}
    with pytest.raises(GridError, match="unrecognised"):
        resolve_zones(location, sources["facilities"], cloud)


def test_region_spanning_two_zones_resolves_to_both(sources):
    location = {"confidence": "region", "candidates": ["cloud:azure:northeurope"], "evidence": []}
    cloud = {("azure", "northeurope"): ["FI", "IE"]}
    assert resolve_zones(location, sources["facilities"], cloud) == ["FI", "IE"]


def test_latest_grid_ignores_mock_files_unless_asked(tmp_path):
    from build.grid import latest_grid
    assert latest_grid(tmp_path) is None
    (tmp_path / "2025.MOCK.csv").write_text("")
    assert latest_grid(tmp_path) is None                     # a mock is never picked up silently
    assert latest_grid(tmp_path, allow_mock=True) == tmp_path / "2025.MOCK.csv"
    (tmp_path / "2023.csv").write_text("")
    (tmp_path / "2024.csv").write_text("")
    (tmp_path / "notes.csv").write_text("")
    assert latest_grid(tmp_path) == tmp_path / "2024.csv"
    assert latest_grid(tmp_path, allow_mock=True) == tmp_path / "2024.csv"   # real data wins over a mock
