from typing import Any, Literal

from pydantic import TypeAdapter

from build.schemas.evidence import Evidence

_EVIDENCE = TypeAdapter(Evidence)


def make_evidence(kind: Literal["primary", "corroborating"] = "primary", **overrides: Any) -> Evidence:
    """One evidence entry: a source that was read and quoted."""
    return _EVIDENCE.validate_python(
        {
            "url": "https://acme.example/regions",
            "shows": 'Regions page: "served from Acme 1"',
            "accessed": "2026-09-01",
            "kind": kind,
        }
        | overrides
    )
