from build.disclosure_rating import disclosure_rating, organization_rating
from tests.builders.evidence import make_evidence
from tests.builders.grid import make_grid
from tests.builders.location import make_location


# A route's rating: how precisely its location's primary evidence determines where its electricity comes from. A named
# facilities, B one grid, C several grids or a subdivided one, D nothing disclosed (or known only from the press),
# which is checked first.


def test_a_route_naming_its_facilities_is_a():
    location = make_location(candidates=["grid:ch"], facilities=["Acme 1, Geneva"])
    assert disclosure_rating(location, {"ch": make_grid()}) == {"letter": "A", "gap": None}


def test_a_route_naming_its_facilities_is_a_whatever_its_grids():
    location = make_location(candidates=["grid:ch", "grid:de"], facilities=["Acme 1, Geneva", "Acme 2, Frankfurt"])
    grids = {"ch": make_grid(), "de": make_grid(name="de", country="DE", zone="DE")}
    assert disclosure_rating(location, grids) == {"letter": "A", "gap": None}


def test_a_route_on_one_grid_is_b():
    location = make_location(candidates=["grid:ch"])
    assert disclosure_rating(location, {"ch": make_grid()}) == {
        "letter": "B",
        "gap": "The grid is disclosed, not the facility.",
    }


def test_a_route_on_one_subdivided_grid_is_c():
    location = make_location(candidates=["grid:se"])
    grids = {"se": make_grid(name="se", country="SE", zone="SE", subdivided=True)}
    assert disclosure_rating(location, grids) == {
        "letter": "C",
        "gap": "The grid is not determined: several are possible.",
    }


def test_a_route_on_several_grids_is_c_even_within_one_country():
    location = make_location(candidates=["grid:us-cal-ciso", "grid:us-tex-erco"])
    grids = {
        "us-cal-ciso": make_grid(name="us-cal-ciso", country="US", zone="US-CAL-CISO"),
        "us-tex-erco": make_grid(name="us-tex-erco", country="US", zone="US-TEX-ERCO"),
    }
    assert disclosure_rating(location, grids) == {
        "letter": "C",
        "gap": "The grid is not determined: several are possible.",
    }


def test_a_route_with_no_candidates_is_d():
    location = make_location(candidates=[], evidence=[make_evidence(kind="primary")])
    assert disclosure_rating(location, {}) == {"letter": "D", "gap": "Location not disclosed by the provider."}


def test_a_route_known_only_from_the_press_is_d():
    location = make_location(candidates=[], evidence=[make_evidence(kind="corroborating")])
    assert disclosure_rating(location, {}) == {"letter": "D", "gap": "Location not disclosed by the provider."}


# An organization's rating: the average of its routes' ratings, A counting 3, B 2, C 1 and D 0.


def test_org_without_routes_is_not_rated():
    assert organization_rating([]) == {"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"}


def test_an_organizations_rating_is_its_routes_average_letter():
    assert organization_rating(["A", "B", "B"]) == {
        "letter": "B",
        "mean": 2.333333,
        "spread": {"A": 1, "B": 2},
        "summary": "B (1 route at A, 2 routes at B)",
    }


def test_an_organizations_letter_is_its_routes_average_rounded_to_the_nearest_ties_down():
    assert organization_rating(["B", "B", "D"])["letter"] == "C"  # 1.33
    assert organization_rating(["B", "C"])["letter"] == "C"  # 1.5, down
    assert organization_rating(["A", "B"])["letter"] == "B"  # 2.5, down
    assert organization_rating(["A", "A", "B"])["letter"] == "A"  # 2.67
    assert organization_rating(["D"])["letter"] == "D"
