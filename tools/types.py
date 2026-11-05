"""The shapes tools/ reads from data/data.json and returns: never validated, since data.json is checked when
`python -m build release` writes it (build/generate_site_data.py's contract)."""

from typing import TypedDict

# data.json's entries: only the fields read here, named as build/generate_site_data.py writes them.


class Range(TypedDict):
    low: float
    high: float


class PublishedModel(TypedDict):
    slug: str
    display_name: str


class PublishedOrganization(TypedDict):
    slug: str
    display_name: str


class PublishedRoute(TypedDict):
    slug: str
    org: str
    model: str
    label: str
    default: bool
    letter: str
    gap: str | None
    served_as: str | None
    energy: Range
    embodied: Range
    grid_intensity: Range | None
    sci: Range | None


class Release(TypedDict):
    release_date: str
    methodology_version: str
    ecologits_version: str
    draft: bool


class FunctionalUnit(TypedDict):
    output_tokens: int


class PublishedMeta(Release):
    functional_unit: FunctionalUnit


class PublishedData(TypedDict):
    schema: str
    meta: PublishedMeta
    models: list[PublishedModel]
    organizations: list[PublishedOrganization]
    routes: list[PublishedRoute]


# What tools.estimate_emissions returns: data.json's fields under the names an agent reads (energy_wh, co2e_g, rating).


class RouteSummary(TypedDict):
    route: str
    organization: str
    where: str
    rating: str
    gap: str | None
    served_as: str | None
    energy_wh: Range
    embodied_g: Range | None
    co2e_g: Range | None


class Estimate(TypedDict):
    model: str
    output_tokens: int
    routes: list[RouteSummary]  # every route of the model, scaled to output_tokens
    release: Release
