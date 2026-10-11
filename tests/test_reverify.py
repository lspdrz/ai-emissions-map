import shutil
from datetime import date

import pytest
import yaml

from build.reverify import ReverifyError, confirms, main, org_claim_files, reverify
from build.validate import load_sources

TODAY = date(2026, 12, 1)
ALP_URL = "https://alpinehost.example/docs/regions"
ALP_SHA = "4444444444444444444444444444444444444444444444444444444444444444"


@pytest.fixture
def root(tmp_path, fixtures_dir):
    copy = tmp_path / "corpus"
    shutil.copytree(fixtures_dir / "corpus", copy)
    return copy


def _page(url, sha, text, status=200, capture="auto", error=None):
    return {"url": url, "final_url": url, "capture": capture, "http_status": status, "content_sha256": sha,
            "content_type": "text/html", "text": text, "error": error}


def _fetcher(pages):
    """A stand-in for build.fetch_source.fetch: answers from `pages`, and anything else is unreachable."""
    def fetch(url, capture="auto"):
        if capture == "manual":
            return _page(url, None, "", status=None, capture="manual", error="a manual capture needs a person")
        return pages.get(url) or _page(url, None, "", status=None, error="ConnectionError")
    return fetch


def _load(root, path):
    return yaml.safe_load((root / "sources" / path).read_text())


def test_confirms_on_identical_bytes_or_quoted_text():
    entry = {"url": ALP_URL, "shows": 'Regions page: "test-70b is served exclusively from ALP-1"',
             "content_sha256": ALP_SHA}
    assert confirms(entry, _page(ALP_URL, ALP_SHA, "")) == (True, "unchanged")
    assert confirms(entry, _page(ALP_URL, "b" * 64, "… Test-70B is served   exclusively from ALP-1 …")) == \
        (True, "page changed; quoted text still present")
    assert confirms(entry, _page(ALP_URL, "b" * 64, "we moved to Frankfurt")) == \
        (False, "page changed; quoted text not found")
    assert confirms(entry, _page(ALP_URL, None, "", status=404)) == (False, "HTTP 404")
    assert confirms(entry, _page(ALP_URL, None, "", status=None, error="ConnectionError")) == \
        (False, "ConnectionError")


def test_no_quote_means_only_identical_bytes_confirm():
    entry = {"url": ALP_URL, "shows": "The regions page names ALP-1", "content_sha256": ALP_SHA}
    assert confirms(entry, _page(ALP_URL, "b" * 64, "The regions page names ALP-1")) == \
        (False, "page changed; shows quotes nothing to look for")


def test_confirmed_location_is_redated_and_digest_refreshed(root):
    before = (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text()
    pages = {ALP_URL: _page(ALP_URL, "c" * 64, "test-70b is served exclusively from ALP-1, our Zurich data centre.")}
    report = reverify(root, TODAY, fetcher=_fetcher(pages), write=True, only=["routes/alpinehost-test-70b.yaml"])
    assert report == [{"file": "routes/alpinehost-test-70b.yaml", "url": ALP_URL, "kind": "primary",
                       "confirmed": True, "detail": "page changed; quoted text still present"}]
    route = _load(root, "routes/alpinehost-test-70b.yaml")
    assert route["location"]["last_verified"] == "2026-12-01"
    ev = route["location"]["evidence"][0]
    assert (ev["accessed"], ev["http_status"], ev["content_sha256"]) == ("2026-12-01", 200, "c" * 64)
    after = (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text()
    assert len([1 for a, b in zip(before.splitlines(), after.splitlines()) if a != b]) == 3


def test_drift_leaves_the_claim_untouched(root):
    before = (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text()
    pages = {ALP_URL: _page(ALP_URL, "c" * 64, "We now serve from Frankfurt.")}
    report = reverify(root, TODAY, fetcher=_fetcher(pages), write=True, only=["routes/alpinehost-test-70b.yaml"])
    assert report[0]["confirmed"] is False
    assert (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text() == before


def test_dry_run_writes_nothing(root):
    before = (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text()
    pages = {ALP_URL: _page(ALP_URL, ALP_SHA, "")}
    report = reverify(root, TODAY, fetcher=_fetcher(pages), only=["routes/alpinehost-test-70b.yaml"])
    assert report[0]["confirmed"] is True
    assert (root / "sources" / "routes" / "alpinehost-test-70b.yaml").read_text() == before


def test_facility_location_is_reverified_too(root):
    url = "https://alpinehost.example/datacenters"
    pages = {url: _page(url, "2" * 64, "")}
    reverify(root, TODAY, fetcher=_fetcher(pages), write=True, only=["facilities/alp-1.yaml"])
    assert _load(root, "facilities/alp-1.yaml")["last_verified"] == "2026-12-01"


def test_manual_capture_is_reported_for_a_person(root):
    path = root / "sources" / "routes" / "multihost-test-70b.yaml"
    path.write_text(path.read_text().replace("    kind: primary\n", "    kind: primary\n    capture: manual\n"))
    report = reverify(root, TODAY, fetcher=_fetcher({}), write=True, only=["routes/multihost-test-70b.yaml"])
    assert report[0]["confirmed"] is False and "manual" in report[0]["detail"]
    assert _load(root, "routes/multihost-test-70b.yaml")["location"]["last_verified"] == "2026-09-20"


def test_unknown_locations_and_aggregators_are_skipped(root):
    report = reverify(root, TODAY, fetcher=_fetcher({}))
    files = {row["file"] for row in report}
    assert "routes/vaguehost-test-70b.yaml" not in files      # confidence unknown: nothing to keep fresh
    assert "routes/aggregator-test-70b.yaml" not in files     # no location of its own


def test_oldest_first_and_limit(root):
    path = root / "sources" / "routes" / "multihost-test-70b.yaml"
    path.write_text(path.read_text().replace("last_verified: '2026-09-20'", "last_verified: '2026-08-01'"))
    report = reverify(root, TODAY, fetcher=_fetcher({}), oldest=1)
    assert {row["file"] for row in report} == {"routes/multihost-test-70b.yaml"}


def test_windows_line_endings_are_kept(root):
    path = root / "sources" / "routes" / "alpinehost-test-70b.yaml"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    pages = {ALP_URL: _page(ALP_URL, ALP_SHA, "")}
    reverify(root, TODAY, fetcher=_fetcher(pages), write=True, only=["routes/alpinehost-test-70b.yaml"])
    raw = path.read_bytes()
    assert b"last_verified: '2026-12-01'\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


def test_failed_edit_leaves_the_file_untouched(root):
    # A duplicated key makes set_scalars' read-back check fail; the curated file must survive intact.
    path = root / "sources" / "facilities" / "alp-1.yaml"
    path.write_text(path.read_text() + "last_verified: '2026-09-21'\n")
    before = path.read_bytes()
    url = "https://alpinehost.example/datacenters"
    with pytest.raises(Exception):
        reverify(root, TODAY, fetcher=_fetcher({url: _page(url, "2" * 64, "")}), write=True,
                 only=["facilities/alp-1.yaml"])
    assert path.read_bytes() == before


def test_org_covers_its_routes_and_the_facilities_they_cite(root):
    assert org_claim_files(load_sources(root), "alpinehost") == [
        "routes/alpinehost-test-70b.yaml", "routes/alpinehost-test-8b.yaml", "facilities/alp-1.yaml"]


def test_org_run_checks_only_that_organization(root):
    only = org_claim_files(load_sources(root), "multihost")
    report = reverify(root, TODAY, fetcher=_fetcher({}), only=only)
    assert {row["file"] for row in report} == {"routes/multihost-test-70b.yaml"}


def test_unknown_organization_raises(root):
    with pytest.raises(ReverifyError, match="no organization 'nohost'"):
        org_claim_files(load_sources(root), "nohost")


def test_cli_names_an_unknown_organization(root, capsys):
    assert main(["--org", "nohost", "--root", str(root)]) == 1
    assert "ERROR: no organization 'nohost' in sources/organizations/" in capsys.readouterr().out
