"""Fetch a cited source and record what was fetched: status, a content hash, and the page's visible text.

Three capture modes, recorded on the evidence entry as `capture`:

- auto (default): a plain HTTP GET; the hash is over the response bytes.
- browser: headless Chromium for pages that only render with JavaScript (trust centres); the hash is
  over the rendered visible text, which is steadier than the HTML a script framework emits.
  Needs `uv sync --group browser && uv run playwright install chromium`.
- manual: a page a person saved because neither of the above could read it; the hash is over the file.

Re-verification (build.reverify) fetches again in the recorded mode, so both fetches are the same
operation. A dead or unreachable source is a finding to record, never an exception.

Usage:
    uv run python -m build.fetch_source https://example.com/regions [more urls]
    uv run python -m build.fetch_source --browser https://trust.example.com/subprocessors
    uv run python -m build.fetch_source --manual saved-page.html --url https://trust.example.com/subprocessors
"""

from __future__ import annotations

import argparse
import hashlib
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import requests
import yaml

USER_AGENT = "ai-emissions-map/0.1 (+https://github.com/lspdrz/ai-emissions-map)"
TIMEOUT_S = 30
SHOWS_PLACEHOLDER = "TODO: quote what the page says, in double quotes"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "template"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def visible_text(body: bytes) -> str:
    """The text a reader sees: tags, scripts and styles removed, whitespace collapsed."""
    parser = _TextExtractor()
    parser.feed(body.decode("utf-8", errors="replace"))
    return normalize(" ".join(parser.parts))


def _result(url: str, capture: str, **fields) -> dict:
    return {"url": url, "final_url": url, "capture": capture, "http_status": None, "content_sha256": None,
            "content_type": None, "text": "", "error": None, **fields}


def fetch_static(url: str, timeout: float = TIMEOUT_S) -> dict:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except requests.RequestException as err:
        return _result(url, "auto", error=f"{type(err).__name__}: {err}")
    body = response.content
    return _result(url, "auto", final_url=response.url, http_status=response.status_code,
                   content_sha256=hashlib.sha256(body).hexdigest(),
                   content_type=response.headers.get("Content-Type"), text=visible_text(body))


def fetch_browser(url: str, timeout_ms: int = 45_000) -> dict:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _result(url, "browser", error="playwright is not installed: uv sync --group browser && "
                                             "uv run playwright install chromium")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                text = normalize(page.inner_text("body"))
                final_url = page.url
            finally:
                browser.close()
    except PlaywrightError as err:
        return _result(url, "browser", error=f"{type(err).__name__}: {err}")
    return _result(url, "browser", final_url=final_url, http_status=response.status if response else None,
                   content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                   content_type="text/plain; rendered", text=text)


def capture_manual(path: Path, url: str) -> dict:
    body = path.read_bytes()
    return _result(url, "manual", content_sha256=hashlib.sha256(body).hexdigest(), text=visible_text(body))


def fetch(url: str, capture: str = "auto") -> dict:
    """Fetch in the given mode. Manual captures cannot be re-fetched by a machine."""
    if capture == "browser":
        return fetch_browser(url)
    if capture == "manual":
        return _result(url, "manual", error="a manual capture needs a person to save the page again")
    return fetch_static(url)


def evidence_entry(result: dict, accessed: date, kind: str = "primary") -> dict:
    """An evidence entry for sources/, in schema order. `shows` must still be written by a person."""
    entry = {"url": result["url"], "shows": SHOWS_PLACEHOLDER, "accessed": accessed.isoformat()}
    if result["http_status"] is not None:
        entry["http_status"] = result["http_status"]
    entry["content_sha256"] = result["content_sha256"]
    entry["kind"] = kind
    if result["capture"] != "auto":
        entry["capture"] = result["capture"]
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build.fetch_source", description=__doc__.splitlines()[0])
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--browser", action="store_true", help="render with headless Chromium")
    parser.add_argument("--manual", type=Path, help="a saved copy of the page (use with one --url)")
    parser.add_argument("--url", help="the address the --manual file was saved from")
    parser.add_argument("--kind", choices=["primary", "corroborating"], default="primary")
    parser.add_argument("--text", action="store_true", help="also print the visible text, to copy `shows` from")
    args = parser.parse_args(argv)
    if args.manual:
        if not args.url:
            parser.error("--manual needs --url")
        results = [capture_manual(args.manual, args.url)]
    elif args.urls:
        results = [fetch_browser(u) if args.browser else fetch_static(u) for u in args.urls]
    else:
        parser.error("give one or more urls, or --manual FILE --url URL")
    failed = 0
    for result in results:
        if result["error"] or result["content_sha256"] is None:
            failed += 1
            print(f"# {result['url']}: {result['error'] or 'no content'}")
            continue
        if result["http_status"] and result["http_status"] >= 400:
            print(f"# {result['url']}: HTTP {result['http_status']} (recorded, but this is not evidence)")
        print(yaml.safe_dump([evidence_entry(result, date.today(), args.kind)], sort_keys=False, allow_unicode=True,
                             width=100).rstrip())
        if args.text:
            print("# text:", result["text"][:2000])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
