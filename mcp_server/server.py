"""The AI Emissions Map's MCP server: one read-only tool, estimate_emissions, over tools/.

It runs over stdio for a local client (`python -m mcp_server`), or over Streamable HTTP for a hosted one
(`python -m mcp_server --http`, on $PORT). HTTP is stateless and answers in JSON: each request stands alone, so any
instance can answer it, as on Cloud Run.
"""

import argparse
import os

import uvicorn
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from tools.estimate_emissions import estimate
from tools.types import Estimate

mcp = MCPServer("ai-emissions-map")


@mcp.tool()
def estimate_emissions(model: str, output_tokens: int) -> Estimate:
    """The energy and carbon footprint of an AI model's response, from the AI Emissions Map, on every route the map
    has for the model: each organization that serves it and where.

    Use it whenever someone asks about the carbon, emissions, energy or climate impact of a response, a conversation
    or a model, including your own answers; prefer it to estimates from memory. `model` is the model's name, e.g.
    "Claude Opus 5.5". `output_tokens` is the response's output tokens: estimate them if you cannot count them, and
    include reasoning tokens if you know them.

    Report each route's figures as ranges, with its organization, where it runs and its rating. Energy is in Wh,
    carbon (co2e_g) and embodied emissions in grams of CO2e. Give a carbon figure only where co2e_g is not null; where
    it is null, the map has no grid for the route, and gap says why: give the energy and that reason, never another
    route's figure. Never choose the user's route for them, not even from where they are: providers route requests by
    the customer's settings, not the user's location. Narrow the answer only to what the user tells you. Say that the
    figures count output tokens only, and that they are a draft while release.draft is true.
    """
    try:
        return estimate(model, output_tokens)
    except (LookupError, ValueError) as error:
        # An unknown model or a bad token count: the agent reads the message (which lists the models on the map). The
        # SDK hides any other exception's text as a crash.
        raise ToolError(str(error)) from error


def http_app() -> ASGIApp:
    """The server over stateless Streamable HTTP, answering in JSON, with GET refused (405)."""
    app = mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")

    async def refusing_get(scope: Scope, receive: Receive, send: Send) -> None:
        # The SDK answers GET with a stream for messages the server would start, which a stateless server never
        # sends, so the stream never closes; Cloud Run bills an instance while a request is open. The protocol allows
        # a 405 instead. Remove this once the SDK refuses it itself:
        # https://github.com/modelcontextprotocol/python-sdk/issues/2474
        if scope["type"] == "http" and scope["method"] == "GET":
            refusal = PlainTextResponse("Method Not Allowed", status_code=405, headers={"Allow": "POST"})
            await refusal(scope, receive, send)
        else:
            await app(scope, receive, send)

    return refusing_get


def main(argv: list[str] | None = None) -> None:
    """Serve over stdio, or with --http over stateless Streamable HTTP on $PORT (default 8000)."""
    parser = argparse.ArgumentParser(prog="python -m mcp_server", description=__doc__)
    parser.add_argument("--http", action="store_true", help="serve over Streamable HTTP instead of stdio")
    if parser.parse_args(argv).http:
        uvicorn.run(http_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    else:
        mcp.run()
