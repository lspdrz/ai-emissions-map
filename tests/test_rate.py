from datetime import date

import pytest

from build.compute import compute_routes
from build.energy import FixedEnergyModel
from build.grid import load_cloud_regions, load_grid
from build.models import model_specs
from build.ranges import Range
from build.rate import rate_orgs, rate_routes

ENERGY = FixedEnergyModel({
    "test-70b": (Range(0.5, 0.6), Range(0.05, 0.06)),
    "test-8b": (Range.point(0.08), Range.point(0.007)),
})


def _rate(sources, fixtures_dir, release=date(2026, 10, 8)):
    grid, cloud = load_grid(fixtures_dir / "grid.csv"), load_cloud_regions(fixtures_dir / "cloud_regions.csv")
    models = model_specs(sources["models"], ecologits_models=[])
    results = compute_routes(sources, models, grid, cloud, ENERGY, release)
    routes = rate_routes(sources, results)
    return routes, rate_orgs(sources, routes)


@pytest.fixture
def ratings(sources, fixtures_dir):
    return _rate(sources, fixtures_dir)


def test_route_letters_and_gaps(ratings):
    routes, _ = ratings
    assert {k: v["letter"] for k, v in routes.items()} == {
        "aggregator-test-70b": "D", "alpinehost-test-70b": "A", "alpinehost-test-8b": "C",
        "multihost-test-70b": "D", "vaguehost-test-70b": "E",
    }
    assert routes["alpinehost-test-70b"]["gap"] is None
    assert routes["multihost-test-70b"]["gap"] == "Location disclosed only as a set of possible countries."
    assert routes["vaguehost-test-70b"]["gap"] == "Reported in press, not disclosed by the provider."


def test_org_ratings_average(ratings):
    _, orgs = ratings
    assert {k: v["letter"] for k, v in orgs.items()} == {
        "aggregator": "D", "alpinehost": "B", "multihost": "D", "vaguehost": "E",
    }
    assert orgs["alpinehost"]["mean"] == pytest.approx(3.0)
    assert orgs["alpinehost"]["spread"] == {"A": 1, "C": 1}
    assert orgs["alpinehost"]["summary"] == "B (1 route at A, 1 route at C)"


def test_org_without_routes_is_not_rated(sources):
    sources["organizations"]["idle"] = sources["organizations"]["vaguehost"] | {"name": "idle", "routes": []}
    org = rate_orgs(sources, {})["idle"]
    assert (org["letter"], org["mean"], org["summary"]) == (None, None, "Not rated (no routes)")


def test_stale_route_is_not_called_undisclosed(sources, fixtures_dir):
    # 91 days after last_verified: the provider did disclose, the map just has not re-checked it.
    sources["routes"]["alpinehost-test-70b"]["location"]["evidence"].append(
        sources["routes"]["vaguehost-test-70b"]["location"]["evidence"][0])   # plus a press report
    routes, _ = _rate(sources, fixtures_dir, release=date(2026, 12, 20))
    assert routes["alpinehost-test-70b"]["letter"] == "E"
    assert routes["alpinehost-test-70b"]["gap"] == "Location evidence not re-verified within 90 days of the release."
    assert routes["aggregator-test-70b"]["gap"] == "An upstream route's location is undisclosed or unverified."
    assert routes["vaguehost-test-70b"]["gap"] == "Reported in press, not disclosed by the provider."


def test_pinned_routes_are_rated_but_not_averaged(sources, fixtures_dir):
    # A region a customer must choose is shown as its own route, but the organization is rated on
    # where its service runs by default; otherwise many pinnable regions would outweigh the default.
    sources["routes"]["alpinehost-test-8b"]["pinned"] = True
    routes, orgs = _rate(sources, fixtures_dir)
    assert routes["alpinehost-test-8b"]["letter"] == "C"
    org = orgs["alpinehost"]
    assert (org["letter"], org["mean"], org["spread"]) == ("A", 4.0, {"A": 1})
    assert (org["routes"], org["pinned_routes"]) == (["alpinehost-test-70b"], ["alpinehost-test-8b"])
    assert org["summary"] == "A (1 route at A; 1 pinned route not counted)"


def test_org_with_only_pinned_routes_is_not_rated(sources, fixtures_dir):
    sources["routes"]["vaguehost-test-70b"]["pinned"] = True
    _, orgs = _rate(sources, fixtures_dir)
    org = orgs["vaguehost"]
    assert (org["letter"], org["mean"], org["summary"]) == (None, None, "Not rated (no default routes)")
