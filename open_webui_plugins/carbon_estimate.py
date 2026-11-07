"""
title: Carbon Estimate
author: Luis Pedraza
author_url: https://github.com/lspdrz/ai-emissions-map
version: 0.2.0
license: MIT
description: Shows each response's energy and carbon footprint, from the AI Emissions Map, under the message.
"""

# The docstring above is Open WebUI's metadata for the function: its title names it in the admin panel.
# An Open WebUI filter: an admin imports this file (Admin Panel > Functions > Import from URL). After each response its outlet reads
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

# Equivalents, shown when the status line is clicked. The bulb and the phone compare the energy, which is the same on
# any grid; the car compares the carbon.
# A standard LED bulb, about 10 W: Hannah Ritchie, "Does that use a lot of energy?",
# https://hannahritchie.github.io/energy-use-comparisons/
LED_BULB_W = 10
# A phone's full charge, about 20 Wh with charging losses: the same page.
PHONE_CHARGE_WH = 20
# A petrol car, 142 g CO2e per km: ADEME's Impact CO2 (https://impactco2.fr), as the EcoLogits calculator uses it,
# https://github.com/mlco2/ecologits-calculator/blob/main/src/config/constants.py
PETROL_CAR_G_PER_KM = 142
# Units from the largest: a span is written in the largest unit its high end reaches.
DURATION_UNITS = ((3600, "h"), (60, "min"), (1, "s"))
DISTANCE_UNITS = ((1000, "km"), (1, "m"), (0.01, "cm"), (0.001, "mm"))

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


def _midpoint(value: dict[str, float]) -> float:
    return (value["low"] + value["high"]) / 2


def _span(low: float, high: float) -> str:
    return _number(low) if _number(low) == _number(high) else f"{_number(low)}–{_number(high)}"


def _in_units(low: float, high: float, units: tuple[tuple[float, str], ...]) -> str:
    factor, name = next(((factor, name) for factor, name in units if high >= factor), units[-1])
    return f"{_span(low / factor, high / factor)} {name}"


def _midpoints(values: list[dict[str, float]]) -> tuple[float, float] | None:
    """The lowest and highest midpoint of the ranges, or None without any."""
    midpoints = [_midpoint(value) for value in values]
    return (min(midpoints), max(midpoints)) if midpoints else None


def _equivalents(energy: tuple[float, float] | None, carbon: tuple[float, float] | None) -> list[str]:
    lines = []
    if energy:
        low, high = energy
        seconds = _in_units(low / LED_BULB_W * 3600, high / LED_BULB_W * 3600, DURATION_UNITS)
        lines.append(f"≈ {seconds} of a {LED_BULB_W} W LED bulb")
        lines.append(f"≈ {_span(low / PHONE_CHARGE_WH * 100, high / PHONE_CHARGE_WH * 100)} % of a phone charge")
    if carbon:
        low, high = carbon
        meters = _in_units(low / PETROL_CAR_G_PER_KM * 1000, high / PETROL_CAR_G_PER_KM * 1000, DISTANCE_UNITS)
        lines.append(f"≈ {meters} driven by a petrol car")
    return lines


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
        show_status: bool = Field(
            default=True,
            description="Show the grams of CO₂e as a line on the message, with everyday equivalents on a click.",
        )
        show_source: bool = Field(default=True, description="Show the details as a source under the message.")
        server_url: str = Field(default=SERVER_URL, description="The AI Emissions Map's MCP server.")

    def __init__(self) -> None:
        # No toggle: Open WebUI would run a toggle filter only in chats where a user switched its chip on.
        self.valves = self.Valves()

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
        try:
            if route:
                result = await self._call("estimate_route_emissions", {"route": route, "output_tokens": count})
                routes, lines = [result["route"]], self._route_lines(result)
            else:
                result = await self._call("estimate_emissions", {"model": base_id, "output_tokens": count})
                routes, lines = result["routes"], self._model_lines(result)
        except Exception as error:
            # A filter's errors are otherwise logged at debug level and dropped: say why there is no footprint.
            await self._status(__event_emitter__, f"Footprint unavailable: {error}")
            return body
        if self.valves.show_status:
            # Open WebUI shows the last status on the message, and the earlier ones when it is clicked: the equivalents
            # first, then the grams. Each is a midpoint, or across several routes the span of their midpoints.
            energy = _midpoints([r["energy_wh"] for r in routes])
            carbon = _midpoints([r["co2e_g"] for r in routes if r["co2e_g"] is not None])
            if carbon:
                grams = f"{_span(*carbon)} g CO₂e"
            else:
                grams = "No carbon figure for this route" if route else "No carbon figure for this model's routes"
            for status in _equivalents(energy, carbon) + [grams]:
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

    def _route_lines(self, result: dict[str, Any]) -> list[str]:
        route = result["route"]
        where = f"{route['organization']}, {route['where']} ({route['rating']})"
        return [f"{result['model']} on {where}: {self._details(route)}"]

    def _model_lines(self, result: dict[str, Any]) -> list[str]:
        routes = result["routes"]
        lines = [
            f"{result['model']} on every route the map has for it. No route is saved for this model in this "
            "filter's settings: an admin can save the one this chat uses, to show only its footprint."
        ]
        lines += [
            f"{route['organization']}, {route['where']} ({route['rating']}): {self._details(route)}" for route in routes
        ]
        return lines

    def _details(self, route: dict[str, Any]) -> str:
        energy = f"{_span(route['energy_wh']['low'], route['energy_wh']['high'])} Wh"
        if route["co2e_g"] is None:
            return f"{energy}, no carbon figure: {route['gap']}"
        carbon = f"{_span(route['co2e_g']['low'], route['co2e_g']['high'])} g CO₂e"
        return f"{carbon}, {energy}" + (f". {route['gap']}" if route["gap"] else "")

    def _notes(self, result: dict[str, Any], estimated: bool) -> list[str]:
        release = result["release"]
        notes = [
            "The figure on the message is the midpoint of the carbon range. Click it for everyday equivalents: a "
            f"{LED_BULB_W} W LED bulb and a {PHONE_CHARGE_WH} Wh phone charge for the energy, a petrol car at "
            f"{PETROL_CAR_G_PER_KM} g CO₂e per km (ADEME's Impact CO2) for the carbon.",
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
                    # One document: Open WebUI heads each document with its own "Content".
                    "document": ["\n\n".join(lines)],
                    "metadata": [{"source": MAP_URL, "name": "AI Emissions Map"}],
                },
            }
        )
