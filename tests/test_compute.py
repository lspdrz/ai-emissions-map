import copy
from datetime import date

import pytest

from build.compute import ComputeError, compute_routes
from build.energy import FixedEnergyModel
from build.grid import load_cloud_regions, load_grid
from build.models import model_specs
from build.ranges import Range

RELEASE = date(2026, 10, 8)
ENERGY = FixedEnergyModel({
    "test-70b": (Range(0.5, 0.6), Range(0.05, 0.06)),
    "test-8b": (Range.point(0.08), Range.point(0.007)),
})


@pytest.fixture
def env(fixtures_dir):
    return load_grid(fixtures_dir / "grid.csv"), load_cloud_regions(fixtures_dir / "cloud_regions.csv")


def run(sources, env, release=RELEASE):
    models = model_specs(sources["models"], ecologits_models=[])
    return compute_routes(sources, models, *env, ENERGY, release)


def test_facility_route_is_scored(sources, env):
    r = run(sources, env)["alpinehost-test-70b"]
    assert (r["scored"], r["level"], r["zones"], r["org"]) == (True, "facility", ["CH"], "alpinehost")
    # operational = E x I: 0.5..0.6 Wh x 30 g/kWh
    assert r["operational_direct"].low == pytest.approx(0.015) and r["operational_direct"].high == pytest.approx(0.018)
    # score = operational + M (0.05..0.06 g)
    assert r["score_direct"].low == pytest.approx(0.065) and r["score_direct"].high == pytest.approx(0.078)
    assert r["score_lifecycle"].high == pytest.approx(0.087)  # 0.6 x 45 / 1000 + 0.06
    assert r["band"] == (2, 2)
    assert r["embodied_g"] == Range(0.05, 0.06)


def test_country_set_route_is_a_range(sources, env):
    r = run(sources, env)["multihost-test-70b"]
    assert r["level"] == "country_set" and r["zones"] == ["DE", "FR"]
    assert r["operational_direct"].low == pytest.approx(0.02) and r["operational_direct"].high == pytest.approx(0.198)
    assert r["score_direct"].low == pytest.approx(0.07) and r["score_direct"].high == pytest.approx(0.258)
    assert r["band"] == (2, 3)


def test_unknown_route_not_scored_but_energy_reported(sources, env):
    r = run(sources, env)["vaguehost-test-70b"]
    assert (r["scored"], r["level"], r["reason"]) == (False, "unknown", "location undisclosed")
    assert r["score_direct"] is None and r["operational_direct"] is None and r["band"] is None
    assert r["energy_wh"] == Range(0.5, 0.6) and r["embodied_g"] == Range(0.05, 0.06)


def test_aggregator_weakest_level_and_union(sources, env):
    r = run(sources, env)["aggregator-test-70b"]
    assert r["scored"] and r["level"] == "country_set"
    assert r["score_direct"].low == pytest.approx(0.065) and r["score_direct"].high == pytest.approx(0.258)
    assert r["operational_direct"].low == pytest.approx(0.015) and r["operational_direct"].high == pytest.approx(0.198)
    assert r["upstream_weights"] == [{"route": "alpinehost-test-70b", "weight": 1.0},
                                     {"route": "multihost-test-70b", "weight": 1.0}]


def test_aggregator_with_unscored_upstream(sources, env):
    d = copy.deepcopy(sources)
    d["routes"]["aggregator-test-70b"]["upstreams"].append({"route": "vaguehost-test-70b", "weight": 1})
    r = run(d, env)["aggregator-test-70b"]
    assert (r["scored"], r["level"], r["score_direct"]) == (False, "unknown", None)
    assert "upstream" in r["reason"]


def test_verification_boundary(sources, env):
    assert run(sources, env, date(2026, 12, 19))["alpinehost-test-70b"]["scored"]      # 90 days
    r = run(sources, env, date(2026, 12, 20))["alpinehost-test-70b"]                     # 91 days
    assert (r["scored"], r["level"]) == (False, "unknown")
    assert r["reason"] == "location evidence not verified within 90 days"


def test_label_mismatch_flagged(sources, env):
    d = copy.deepcopy(sources)
    d["routes"]["multihost-test-70b"]["served_as"] = "test-70b-v1.5"
    assert run(d, env)["multihost-test-70b"]["label_mismatch"] is True


def test_cycle_raises_compute_error(sources, env):
    d = copy.deepcopy(sources)
    alp = d["routes"]["alpinehost-test-70b"]
    del alp["location"]
    alp["upstreams"] = [{"route": "aggregator-test-70b", "weight": 1}]
    with pytest.raises(ComputeError, match="cycle"):
        run(d, env)
