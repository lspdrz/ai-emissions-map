from typing import Any

from pydantic import TypeAdapter

from build.schemas.model import Model, ParamRange
from tests.builders.evidence import make_evidence

_MODEL = TypeAdapter(Model)


def make_model(
    name: str = "m-70b", active_b: float | ParamRange = 70, total_b: float | ParamRange = 70, **overrides: Any
) -> Model:
    """A curated model record: parameter counts in billions, with the evidence for them."""
    return _MODEL.validate_python(
        {
            "name": name,
            "architecture": "dense",
            "active_b": active_b,
            "total_b": total_b,
            "evidence": [make_evidence()],
        }
        | overrides
    )
