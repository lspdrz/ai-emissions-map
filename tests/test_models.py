from build.models import model_ids, model_specs
from build.ranges import Range


def test_ecologits_moe_entry_is_converted():
    raw = [{"provider": "mistralai", "name": "mistral-large-2512",
            "architecture": {"type": "moe", "parameters": {"total": 675, "active": 41}}}]
    spec = model_specs(None, ecologits_models=raw)["mistral-large-2512"]
    assert spec == {"active_b": Range.point(41), "total_b": Range.point(675), "source": "ecologits"}


def test_ecologits_parameter_ranges_are_kept():
    raw = [{"provider": "openai", "name": "closed-x",
            "architecture": {"type": "dense", "parameters": {"min": 100, "max": 300}}}]
    spec = model_specs(None, ecologits_models=raw)["closed-x"]
    assert spec["active_b"] == Range(100, 300) == spec["total_b"]


def test_curated_models_win_over_ecologits(sources):
    raw = [{"provider": "x", "name": "test-70b", "architecture": {"type": "dense", "parameters": 1}}]
    specs = model_specs(sources["models"], ecologits_models=raw)
    assert specs["test-70b"] == {"active_b": Range.point(70), "total_b": Range.point(70), "source": "curated"}
    assert specs["test-8b"]["source"] == "curated"


def test_curated_parameter_range():
    curated = {"closed-y": {"name": "closed-y", "architecture": "moe", "active_b": {"min": 20, "max": 40},
                            "total_b": {"min": 200, "max": 400}}}
    spec = model_specs(curated, ecologits_models=[])["closed-y"]
    assert (spec["active_b"], spec["total_b"]) == (Range(20, 40), Range(200, 400))


def test_model_ids_need_no_valid_parameters():
    # Validation needs the ids before it has checked the files, so reading them must not touch parameters.
    raw = [{"provider": "x", "name": "eco-1", "architecture": {"type": "dense", "parameters": 1}}]
    assert model_ids({"broken": {"name": "broken"}}, ecologits_models=raw) == {"eco-1", "broken"}
