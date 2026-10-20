from typing import Any, Literal

from pydantic import TypeAdapter

from build.schemas.organization import Organization

_ORGANIZATION = TypeAdapter(Organization)


def make_organization(
    name: str = "acme",
    type: Literal["model_lab", "inference_host", "cloud", "public_compute"] = "inference_host",
    **overrides: Any,
) -> Organization:
    """An organization."""
    return _ORGANIZATION.validate_python(
        {
            "name": name,
            "display_name": name.title(),
            "type": type,
            "homepage": f"https://{name}.example",
            "ids": {},
        }
        | overrides
    )
