"""
title: Carbon Estimate
author: Luis Pedraza
author_url: https://github.com/lspdrz/ai-emissions-map
version: 0.1.0
license: MIT
description: Shows each response's energy and carbon footprint, from the AI Emissions Map, under the message.
"""

# The docstring above is Open WebUI's metadata for the function: its title names it in the admin panel and on the
# chat's toggle chip.
# An Open WebUI filter: an admin pastes this file in (Admin Panel > Functions). After each response its outlet reads
# the model and the response's output tokens and asks the map's hosted MCP server for the footprint: on the route the
# admin saved for the model, or else on every route of the model.

import asyncio
import json
import urllib.request
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

SERVER_URL = "https://ai-emissions-map-19055002993.europe-north2.run.app/mcp"
MAP_URL = "https://ai-emissions-map.vercel.app"
TIMEOUT_SECONDS = 10
# Without the provider's count, a reply's tokens are estimated from its text: about 4 characters a token in English.
CHARS_PER_TOKEN = 4
# Where providers report a reply's output tokens: OpenAI's Chat Completions, the Responses API and Anthropic, Ollama.
USAGE_FIELDS = ("completion_tokens", "output_tokens", "eval_count")

Emitter = Callable[[dict[str, Any]], Awaitable[None]]


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST a JSON-RPC request to the MCP server and read its JSON answer. The server is stateless, so a tools/call
    needs no initialize first."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


def _number(value: float) -> str:
    return f"{value:.0f}" if value >= 10 else f"{value:.2g}"


def _span(low: float, high: float) -> str:
    return _number(low) if _number(low) == _number(high) else f"{_number(low)}–{_number(high)}"


def _saved_routes(text: str) -> dict[str, str]:
    """The admin's saved routes, written as model=route pairs separated by commas."""
    pairs = (pair.split("=", 1) for pair in text.split(",") if "=" in pair)
    return {model.strip(): route.strip() for model, route in pairs}


class Filter:
    class Valves(BaseModel):
        routes: str = Field(
            default="",
            description="The route each model is served on, as model=route pairs separated by commas, e.g. "
            "mistral-medium-3.5-128b=scaleway-mistral-medium-3-5-128b. The model is its ID in Open WebUI, the route its "
            f"slug on the map ({MAP_URL}). A model without one shows every route the map has for it.",
        )
        estimate_tokens_from_text: bool = Field(
            default=True,
            description="When the provider reports no output tokens, estimate them from the reply's text.",
        )
        show_status: bool = Field(default=True, description="Show the footprint as a line on the message.")
        show_source: bool = Field(default=True, description="Show the details as a source under the message.")
        server_url: str = Field(default=SERVER_URL, description="The AI Emissions Map's MCP server.")

    def __init__(self) -> None:
        self.valves = self.Valves()
        # A chip in the chat: users can switch the footprint off for a chat.
        self.toggle = True

    async def outlet(
        self,
        body: dict[str, Any],
        __model__: dict[str, Any] | None = None,
        __event_emitter__: Emitter | None = None,
    ) -> dict[str, Any]:
        # An API caller has no chat to show it in.
        if __event_emitter__ is None:
            return body
        tokens = self._output_tokens(body["messages"][-1])
        if tokens is None:
            return body
        count, estimated = tokens
        model = __model__ or {}
        model_id = model.get("id") or body.get("model") or ""
        base_id = (model.get("info") or {}).get("base_model_id") or model_id
        saved = _saved_routes(self.valves.routes)
        route = saved.get(model_id) or saved.get(base_id)
        tokens_text = f"≈{count} output tokens (estimated from the text)" if estimated else f"{count} output tokens"
        try:
            if route:
                result = await self._call("estimate_route_emissions", {"route": route, "output_tokens": count})
                status, lines = self._route_footprint(result, tokens_text)
            else:
                result = await self._call("estimate_emissions", {"model": base_id, "output_tokens": count})
                status, lines = self._model_footprint(result, tokens_text)
        except Exception as error:
            # A filter's errors are otherwise logged at debug level and dropped: say why there is no footprint.
            await self._status(__event_emitter__, f"Footprint unavailable: {error}")
            return body
        if result["release"]["draft"]:
            status += " · draft"
        if self.valves.show_status:
            await self._status(__event_emitter__, status)
        if self.valves.show_source:
            await self._source(__event_emitter__, lines + self._notes(result, estimated))
        return body

    def _output_tokens(self, message: dict[str, Any]) -> tuple[int, bool] | None:
        """The reply's output tokens, and whether they are estimated: the provider's count, or else the text's."""
        usage = message.get("usage") or {}
        for field in USAGE_FIELDS:
            if isinstance(usage.get(field), int) and usage[field] > 0:
                return usage[field], False
        # The text includes any reasoning Open WebUI shows; reasoning the provider hides is not in it.
        count = round(len(message.get("content") or "") / CHARS_PER_TOKEN)
        if self.valves.estimate_tokens_from_text and count >= 1:
            return count, True
        return None

    async def _call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}}
        # urllib blocks: run it off Open WebUI's event loop.
        answer = await asyncio.to_thread(_post, self.valves.server_url, payload)
        if "error" in answer:
            raise RuntimeError(answer["error"]["message"])
        result = answer["result"]
        if result.get("isError"):
            # The tool's message, after the SDK's "Error executing tool <name>: ": its first sentence says what is
            # wrong; the rest lists the map's models or routes.
            text = result["content"][0]["text"].removeprefix(f"Error executing tool {tool}: ")
            raise LookupError(text.split(". ")[0].rstrip(".") + ".")
        return result["structuredContent"]

    def _route_footprint(self, result: dict[str, Any], tokens_text: str) -> tuple[str, list[str]]:
        route = result["route"]
        where = f"{route['organization']}, {route['where']} ({route['rating']})"
        status = f"{self._figures(route)} · {tokens_text} · {where}"
        return status, [f"{result['model']} on {where}: {self._details(route)}"]

    def _model_footprint(self, result: dict[str, Any], tokens_text: str) -> tuple[str, list[str]]:
        routes = result["routes"]
        carbon = [route["co2e_g"] for route in routes if route["co2e_g"] is not None]
        figures = []
        if carbon:
            figures.append(f"{_span(min(c['low'] for c in carbon), max(c['high'] for c in carbon))} g CO₂e")
        energy = [route["energy_wh"] for route in routes]
        figures.append(f"{_span(min(e['low'] for e in energy), max(e['high'] for e in energy))} Wh")
        status = f"{' · '.join(figures)} · {tokens_text} · {len(routes)} routes, none saved for this model"
        lines = [
            f"{result['model']} on every route the map has for it. No route is saved for this model in this "
            "filter's settings: an admin can save the one this chat uses, to show only its footprint."
        ]
        lines += [
            f"{route['organization']}, {route['where']} ({route['rating']}): {self._details(route)}" for route in routes
        ]
        return status, lines

    def _figures(self, route: dict[str, Any]) -> str:
        energy = f"{_span(route['energy_wh']['low'], route['energy_wh']['high'])} Wh"
        if route["co2e_g"] is None:
            return f"{energy} · no carbon figure"
        return f"{_span(route['co2e_g']['low'], route['co2e_g']['high'])} g CO₂e · {energy}"

    def _details(self, route: dict[str, Any]) -> str:
        energy = f"{_span(route['energy_wh']['low'], route['energy_wh']['high'])} Wh"
        if route["co2e_g"] is None:
            return f"{energy}, no carbon figure: {route['gap']}"
        carbon = f"{_span(route['co2e_g']['low'], route['co2e_g']['high'])} g CO₂e"
        return f"{carbon}, {energy}" + (f". {route['gap']}" if route["gap"] else "")

    def _notes(self, result: dict[str, Any], estimated: bool) -> list[str]:
        release = result["release"]
        notes = [
            f"The figures count {result['output_tokens']} output tokens only; input tokens are not counted.",
            f"Release {release['release_date']} (methodology {release['methodology_version']}, EcoLogits "
            f"{release['ecologits_version']})" + (", a draft." if release["draft"] else "."),
        ]
        if estimated:
            notes.insert(
                0,
                "The provider reported no token count, so the output tokens are estimated from the reply's text, at "
                f"about {CHARS_PER_TOKEN} characters a token; hidden reasoning is not counted.",
            )
        return notes

    async def _status(self, emit: Emitter, description: str) -> None:
        await emit({"type": "status", "data": {"description": description, "done": True, "hidden": False}})

    async def _source(self, emit: Emitter, lines: list[str]) -> None:
        await emit(
            {
                "type": "source",
                "data": {
                    "source": {"name": "AI Emissions Map", "url": MAP_URL},
                    "document": lines,
                    "metadata": [{"source": MAP_URL, "name": "AI Emissions Map"} for _ in lines],
                },
            }
        )
