# The MCP server's image (mcp_server/). Cloud Run builds and deploys it on every push to beta (set up in the console).

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /bin/uv

WORKDIR /app
# The image's own Python, compiled once at build time.
ENV UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Only the mcp dependency group
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --only-group mcp --no-install-project

COPY tools/ tools/
COPY mcp_server/ mcp_server/
COPY data/data.json data/data.json

ENV PATH="/app/.venv/bin:$PATH"
# Cloud Run sets $PORT; the server listens on it.
CMD ["python", "-m", "mcp_server", "--http"]
