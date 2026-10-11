import pytest

from build.yamledit import YamlEditError, set_scalars

DOC = """\
# A route. Comments and layout must survive an edit.
name: acme-m-70b
model: m-70b
location:
  confidence: facility
  candidates: ["facility:acme-1"]
  last_verified: '2026-09-20'   # re-dated by build.reverify
  evidence:
  - url: https://acme.example/regions
    shows: 'Regions page: "m-70b runs in Acme 1"'
    accessed: '2026-09-01'
    http_status: 200
    content_sha256: "4444444444444444444444444444444444444444444444444444444444444444"
    kind: primary
  - { url: https://acme.example/dpa, shows: 'DPA: "Geneva"', accessed: '2026-09-01', http_status: 200, content_sha256: "5555555555555555555555555555555555555555555555555555555555555555", kind: primary }
"""


def test_only_the_named_values_change():
    new = set_scalars(DOC, {
        ("location", "last_verified"): "2026-10-08",
        ("location", "evidence", 0, "content_sha256"): "a" * 64,
        ("location", "evidence", 0, "http_status"): 301,
    })
    changed = [(a, b) for a, b in zip(DOC.splitlines(), new.splitlines()) if a != b]
    assert changed == [
        ("  last_verified: '2026-09-20'   # re-dated by build.reverify",
         "  last_verified: '2026-10-08'   # re-dated by build.reverify"),
        ("    http_status: 200", "    http_status: 301"),
        ('    content_sha256: "4444444444444444444444444444444444444444444444444444444444444444"',
         f"    content_sha256: '{'a' * 64}'"),
    ]


def test_flow_mapping_values_are_edited_in_place():
    new = set_scalars(DOC, {("location", "evidence", 1, "accessed"): "2026-10-08"})
    assert "accessed: '2026-10-08', http_status: 200" in new
    assert new.count("\n") == DOC.count("\n")


def test_quotes_inside_strings_survive():
    new = set_scalars(DOC, {("location", "evidence", 0, "shows"): "Page: \"it's in Geneva\""})
    import yaml
    assert yaml.safe_load(new)["location"]["evidence"][0]["shows"] == "Page: \"it's in Geneva\""


def test_missing_path_is_an_error():
    with pytest.raises(YamlEditError, match="location.evidence.5"):
        set_scalars(DOC, {("location", "evidence", 5, "accessed"): "2026-10-08"})


def test_only_scalars_can_be_set():
    with pytest.raises(YamlEditError, match="not a scalar"):
        set_scalars(DOC, {("location", "candidates"): "zone:CH"})


def test_non_ascii_text_before_the_value_does_not_shift_the_edit():
    doc = "display_name: Zürich DC — gCO₂ ✓\nlast_verified: '2026-09-20'\n"
    assert set_scalars(doc, {("last_verified",): "2026-10-08"}) == \
        "display_name: Zürich DC — gCO₂ ✓\nlast_verified: '2026-10-08'\n"
