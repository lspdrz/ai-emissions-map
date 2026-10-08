"""Model parameter counts: EcoLogits' catalogue, with curated sources/models/<id>.yaml taking precedence."""

from __future__ import annotations

import importlib.resources as resources
import json

from build.ranges import Range


def packaged_ecologits_models() -> list[dict]:
    text = (resources.files("ecologits") / "data" / "models.json").read_text(encoding="utf-8")
    return json.loads(text)["models"]


def _params(value) -> Range:
    if isinstance(value, dict):
        return Range(float(value["min"]), float(value["max"]))
    return Range.point(float(value))


def model_ids(curated: dict | None, ecologits_models: list[dict] | None = None) -> set[str]:
    """Every known model id. Reads names only, so it is safe to call before validate_sources has checked the files."""
    raw = packaged_ecologits_models() if ecologits_models is None else ecologits_models
    return {m["name"] for m in raw} | set(curated or {})


def model_specs(curated: dict | None, ecologits_models: list[dict] | None = None) -> dict[str, dict]:
    """Model id -> {"active_b", "total_b": Range of billions of parameters, "source": "ecologits" | "curated"}.

    `curated` is load_sources(...)["models"]: a model file wins over an EcoLogits entry with the same id, for models
    EcoLogits lacks (Apertus, Llama, Qwen) or where a model card gives a better figure.
    """
    raw = packaged_ecologits_models() if ecologits_models is None else ecologits_models
    specs: dict[str, dict] = {}
    for m in raw:
        if m["name"] in specs:
            continue  # first entry wins; names are unique in practice
        params = m["architecture"]["parameters"]
        if isinstance(params, dict) and "active" in params:
            active, total = _params(params["active"]), _params(params["total"])
        else:
            active = total = _params(params)
        specs[m["name"]] = {"active_b": active, "total_b": total, "source": "ecologits"}
    for name, m in (curated or {}).items():
        specs[name] = {"active_b": _params(m["active_b"]), "total_b": _params(m["total_b"]), "source": "curated"}
    return specs
