import functools
import http.server
import threading
from pathlib import Path

import pytest

from build.validate import load_sources

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def sources() -> dict:
    """The fixture corpus as load_sources returns it: plain dicts keyed by filename stem."""
    return load_sources(FIXTURES / "corpus")


@pytest.fixture
def page_server():
    """Serves tests/fixtures/pages/ on a free local port; yields the base URL. Anything missing is a 404."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FIXTURES / "pages"))
    handler.log_message = lambda *args: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
