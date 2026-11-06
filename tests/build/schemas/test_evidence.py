from build.schemas.evidence import has_primary
from tests.builders.evidence import make_evidence


def test_has_primary_needs_one_primary_source():
    assert has_primary([make_evidence(kind="corroborating"), make_evidence(kind="primary")])
    assert not has_primary([make_evidence(kind="corroborating")])
    assert not has_primary([])
    assert not has_primary(None)
