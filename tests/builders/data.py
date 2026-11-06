"""Builders for data/data.json's entries, as tools/ reads them. Every field is a required argument, with no
defaults, so a test states each value its result depends on."""

from tools.types import PublishedData, PublishedMeta, PublishedModel, PublishedOrganization, PublishedRoute, Range


def make_data_model(*, slug: str, display_name: str) -> PublishedModel:
    return {"slug": slug, "display_name": display_name}


def make_data_organization(*, slug: str, display_name: str) -> PublishedOrganization:
    return {"slug": slug, "display_name": display_name}


def make_data_route(
    *,
    slug: str,
    org: str,
    model: str,
    label: str,
    default: bool,
    letter: str,
    gap: str | None,
    served_as: str | None,
    energy: Range,
    embodied: Range,
    grid_intensity: Range | None,
    sci: Range | None,
) -> PublishedRoute:
    return {
        "slug": slug,
        "org": org,
        "model": model,
        "label": label,
        "default": default,
        "letter": letter,
        "gap": gap,
        "served_as": served_as,
        "energy": energy,
        "embodied": embodied,
        "grid_intensity": grid_intensity,
        "sci": sci,
    }


def make_data_meta(
    *, release_date: str, methodology_version: str, ecologits_version: str, draft: bool, functional_unit_tokens: int
) -> PublishedMeta:
    return {
        "release_date": release_date,
        "methodology_version": methodology_version,
        "ecologits_version": ecologits_version,
        "draft": draft,
        "functional_unit": {"output_tokens": functional_unit_tokens},
    }


def make_data(
    *,
    schema: str,
    meta: PublishedMeta,
    models: list[PublishedModel],
    organizations: list[PublishedOrganization],
    routes: list[PublishedRoute],
) -> PublishedData:
    return {"schema": schema, "meta": meta, "models": models, "organizations": organizations, "routes": routes}
