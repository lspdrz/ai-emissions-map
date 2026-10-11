import hashlib
import importlib.util
from datetime import date

import pytest

from build.fetch_source import capture_manual, evidence_entry, fetch_browser, fetch_static, visible_text


def _chromium_available() -> bool:
    if importlib.util.find_spec("playwright") is None:
        return False
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


needs_browser = pytest.mark.skipif(not _chromium_available(), reason="playwright + chromium not installed")


def test_static_fetch_hashes_the_bytes(page_server, fixtures_dir):
    result = fetch_static(f"{page_server}/regions.html")
    body = (fixtures_dir / "pages" / "regions.html").read_bytes()
    assert result["http_status"] == 200
    assert result["content_sha256"] == hashlib.sha256(body).hexdigest()
    assert result["capture"] == "auto" and result["error"] is None
    assert "test-70b is served exclusively from ALP-1" in result["text"]


def test_dead_page_is_a_finding_not_a_crash(page_server):
    result = fetch_static(f"{page_server}/gone.html")
    assert result["http_status"] == 404


def test_unreachable_host_is_a_finding_not_a_crash():
    result = fetch_static("http://127.0.0.1:9/nothing-listens-here")
    assert result["http_status"] is None and result["content_sha256"] is None
    assert result["error"]


def test_visible_text_drops_scripts_styles_and_extra_whitespace():
    html = b"<html><head><style>.x{}</style><script>var a = 1;</script></head><body><p>One\n  two</p><p>three</p></body></html>"
    assert visible_text(html) == "One two three"


def test_manual_capture_hashes_the_saved_file(tmp_path):
    saved = tmp_path / "trust-centre.html"
    saved.write_bytes(b"<html><body>Frankfurt or Paris regions</body></html>")
    result = capture_manual(saved, "https://trust.example.com/subprocessors")
    assert result["capture"] == "manual" and result["http_status"] is None
    assert result["content_sha256"] == hashlib.sha256(saved.read_bytes()).hexdigest()
    assert result["text"] == "Frankfurt or Paris regions"


def test_evidence_entry_is_ready_to_paste_except_shows(page_server):
    entry = evidence_entry(fetch_static(f"{page_server}/regions.html"), accessed=date(2026, 10, 8))
    assert list(entry) == ["url", "shows", "accessed", "http_status", "content_sha256", "kind"]
    assert entry["shows"] == "TODO: quote what the page says, in double quotes"
    assert (entry["accessed"], entry["kind"]) == ("2026-10-08", "primary")


def test_evidence_entry_records_non_default_capture(tmp_path):
    saved = tmp_path / "page.html"
    saved.write_text("<p>x</p>")
    entry = evidence_entry(capture_manual(saved, "https://example.com"), accessed=date(2026, 10, 8))
    assert entry["capture"] == "manual" and "http_status" not in entry


@pytest.mark.browser
@needs_browser
def test_browser_fetch_sees_text_written_by_javascript(page_server):
    static = fetch_static(f"{page_server}/trust-centre.html")
    assert "Frankfurt or Paris" not in static["text"]          # a plain fetch only sees "Loading…"
    result = fetch_browser(f"{page_server}/trust-centre.html")
    assert result["http_status"] == 200 and result["capture"] == "browser"
    assert "Frankfurt or Paris regions" in result["text"]
    # Hashed over the rendered visible text, so two renders of the same page agree.
    assert fetch_browser(f"{page_server}/trust-centre.html")["content_sha256"] == result["content_sha256"]
