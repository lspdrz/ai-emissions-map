from typing import Any

from pydantic import TypeAdapter

from build.schemas.route import CheckedRoute, Location, Route
from tests.builders.location import make_location

_ROUTE = TypeAdapter(CheckedRoute)


def make_route(
    name: str = "acme-m-70b",
    org: str = "acme",
    model: str = "m-70b",
    location: Location | None = None,
    **overrides: Any,
) -> Route:
    """A route: an organization serving a model from a location (make_location's default)."""
    return _ROUTE.validate_python(
        {
            "name": name,
            "org": org,
            "model": model,
            "location": make_location() if location is None else location,
        }
        | overrides
    )
