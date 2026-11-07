import asyncio
from typing import Any

from open_webui_plugins.carbon_estimate import Filter

# Each test builds the chat body, model and estimate the filter reads, replaces _post (the filter's one HTTP call to
# the MCP server) with a fake that records what it was sent, and collects the events the filter emits.


def _route_estimate(*, co2e_g: dict[str, float] | None, gap: str | None, draft: bool) -> dict[str, Any]:
    return {
        "model": "M 70B",
        "output_tokens": 850,
        "route": {
            "route": "acme-m-70b",
            "organization": "Acme",
            "where": "Acme 1, Geneva",
            "rating": "A" if gap is None else "D",
            "gap": gap,
            "served_as": None,
            "energy_wh": {"low": 0.78, "high": 0.78},
            "embodied_g": None if co2e_g is None else {"low": 0.07, "high": 0.07},
            "co2e_g": co2e_g,
        },
        "release": {
            "release_date": "2026-10-28",
            "methodology_version": "0.4.0",
            "ecologits_version": "0.11.2",
            "draft": draft,
        },
    }


def _model_estimate() -> dict[str, Any]:
    return {
        "model": "M 70B",
        "output_tokens": 850,
        "routes": [
            {
                "route": "acme-m-70b",
                "organization": "Acme",
                "where": "Acme 1, Geneva",
                "rating": "A",
                "gap": None,
                "served_as": None,
                "energy_wh": {"low": 0.5, "high": 0.6},
                "embodied_g": {"low": 0.01, "high": 0.01},
                "co2e_g": {"low": 0.02, "high": 0.03},
            },
            {
                "route": "globex-m-70b",
                "organization": "Globex",
                "where": "Not disclosed",
                "rating": "D",
                "gap": "Location not disclosed by the provider.",
                "served_as": None,
                "energy_wh": {"low": 0.4, "high": 0.9},
                "embodied_g": None,
                "co2e_g": None,
            },
            {
                "route": "initech-m-70b",
                "organization": "Initech",
                "where": "Initech 2, Warsaw",
                "rating": "B",
                "gap": None,
                "served_as": None,
                "energy_wh": {"low": 0.7, "high": 0.8},
                "embodied_g": {"low": 0.01, "high": 0.01},
                "co2e_g": {"low": 0.4, "high": 0.5},
            },
        ],
        "release": {
            "release_date": "2026-10-28",
            "methodology_version": "0.4.0",
            "ecologits_version": "0.11.2",
            "draft": False,
        },
    }


def _tool_result(content: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "result": {"content": [], "structuredContent": content, "isError": False}}


def _tool_error(message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": message}], "isError": True}}


def _run_outlet(
    flt: Filter, body: dict[str, Any], model: dict[str, Any], with_emitter: bool = True
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    async def emit(event: dict[str, Any]) -> None:
        events.append(event)

    async def run() -> dict[str, Any]:
        return await flt.outlet(body, __model__=model, __event_emitter__=emit if with_emitter else None)

    assert asyncio.run(run()) is body
    return events


def _fake_server(monkeypatch, response: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sent: list[tuple[str, dict[str, Any]]] = []

    def post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
        sent.append((url, payload))
        return response

    monkeypatch.setattr("open_webui_plugins.carbon_estimate._post", post)
    return sent


def _status(events: list[dict[str, Any]]) -> str:
    [status] = [event for event in events if event["type"] == "status"]
    assert status["data"]["done"] is True
    return status["data"]["description"]


def _source(events: list[dict[str, Any]]) -> str:
    [source] = [event for event in events if event["type"] == "source"]
    return "\n".join(source["data"]["document"])


def test_a_model_with_a_saved_route_gets_that_route(monkeypatch):
    sent = _fake_server(
        monkeypatch, _tool_result(_route_estimate(co2e_g={"low": 0.1, "high": 0.1}, gap=None, draft=True))
    )
    flt = Filter()
    flt.valves.routes = "other-model=globex-m-70b, acme/m-70b=acme-m-70b"
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    events = _run_outlet(flt, body, {"id": "acme/m-70b", "info": {}})
    [(url, payload)] = sent
    assert url == flt.valves.server_url
    assert payload["method"] == "tools/call"
    assert payload["params"] == {
        "name": "estimate_route_emissions",
        "arguments": {"route": "acme-m-70b", "output_tokens": 850},
    }
    assert _status(events) == "0.1 g CO₂e · 0.78 Wh · 850 output tokens · Acme, Acme 1, Geneva (A) · draft"


def test_a_workspace_model_finds_the_route_saved_for_its_base_model(monkeypatch):
    sent = _fake_server(
        monkeypatch, _tool_result(_route_estimate(co2e_g={"low": 0.1, "high": 0.1}, gap=None, draft=True))
    )
    flt = Filter()
    flt.valves.routes = "acme/m-70b=acme-m-70b"
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    _run_outlet(flt, body, {"id": "my-helper", "info": {"base_model_id": "acme/m-70b"}})
    [(_, payload)] = sent
    assert payload["params"]["arguments"]["route"] == "acme-m-70b"


def test_a_model_without_a_saved_route_gets_every_route_of_the_model(monkeypatch):
    sent = _fake_server(monkeypatch, _tool_result(_model_estimate()))
    flt = Filter()
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    events = _run_outlet(flt, body, {"id": "my-helper", "info": {"base_model_id": "acme/m-70b"}})
    [(_, payload)] = sent
    assert payload["params"] == {
        "name": "estimate_emissions",
        "arguments": {"model": "acme/m-70b", "output_tokens": 850},
    }
    assert _status(events) == "0.02–0.5 g CO₂e · 0.4–0.9 Wh · 850 output tokens · 3 routes, none saved for this model"
    source = _source(events)
    assert "No route is saved for this model" in source
    assert "Globex, Not disclosed (D): 0.4–0.9 Wh, no carbon figure: Location not disclosed by the provider." in source


def test_the_output_tokens_are_read_from_each_providers_usage_field(monkeypatch):
    for usage in ({"completion_tokens": 850}, {"output_tokens": 850}, {"eval_count": 850}):
        sent = _fake_server(monkeypatch, _tool_result(_model_estimate()))
        body = {"messages": [{"role": "assistant", "content": "Hello", "usage": usage}]}
        _run_outlet(Filter(), body, {"id": "acme/m-70b", "info": {}})
        [(_, payload)] = sent
        assert payload["params"]["arguments"]["output_tokens"] == 850


def test_without_usage_the_tokens_are_estimated_from_the_text_and_said_to_be(monkeypatch):
    sent = _fake_server(monkeypatch, _tool_result(_model_estimate()))
    body = {"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "x" * 400}]}
    events = _run_outlet(Filter(), body, {"id": "acme/m-70b", "info": {}})
    [(_, payload)] = sent
    assert payload["params"]["arguments"]["output_tokens"] == 100
    assert "≈100 output tokens (estimated from the text)" in _status(events)
    assert "hidden reasoning is not counted" in _source(events)


def test_without_usage_and_with_estimating_off_nothing_is_shown(monkeypatch):
    sent = _fake_server(monkeypatch, _tool_result(_model_estimate()))
    flt = Filter()
    flt.valves.estimate_tokens_from_text = False
    body = {"messages": [{"role": "assistant", "content": "x" * 400}]}
    assert _run_outlet(flt, body, {"id": "acme/m-70b", "info": {}}) == []
    assert sent == []


def test_a_route_without_a_grid_shows_its_energy_and_why_there_is_no_carbon_figure(monkeypatch):
    gap = "Location not disclosed by the provider."
    _fake_server(monkeypatch, _tool_result(_route_estimate(co2e_g=None, gap=gap, draft=False)))
    flt = Filter()
    flt.valves.routes = "acme/m-70b=acme-m-70b"
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    events = _run_outlet(flt, body, {"id": "acme/m-70b", "info": {}})
    assert _status(events) == "0.78 Wh · no carbon figure · 850 output tokens · Acme, Acme 1, Geneva (D)"
    assert gap in _source(events)


def test_the_source_names_the_release(monkeypatch):
    _fake_server(monkeypatch, _tool_result(_route_estimate(co2e_g={"low": 0.1, "high": 0.1}, gap=None, draft=True)))
    flt = Filter()
    flt.valves.routes = "acme/m-70b=acme-m-70b"
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    source = _source(_run_outlet(flt, body, {"id": "acme/m-70b", "info": {}}))
    assert "Release 2026-10-28 (methodology 0.4.0, EcoLogits 0.11.2), a draft." in source
    assert "output tokens only" in source


def test_status_and_source_can_each_be_turned_off(monkeypatch):
    _fake_server(monkeypatch, _tool_result(_model_estimate()))
    flt = Filter()
    flt.valves.show_status = False
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    assert [event["type"] for event in _run_outlet(flt, body, {"id": "acme/m-70b", "info": {}})] == ["source"]
    flt = Filter()
    flt.valves.show_source = False
    assert [event["type"] for event in _run_outlet(flt, body, {"id": "acme/m-70b", "info": {}})] == ["status"]


def test_a_tool_error_is_shown_as_its_first_sentence(monkeypatch):
    _fake_server(
        monkeypatch,
        _tool_error(
            "Error executing tool estimate_emissions: No model on the map matches 'x-1'. Models: M 70B, N Flash."
        ),
    )
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    events = _run_outlet(Filter(), body, {"id": "x-1", "info": {}})
    assert [event["type"] for event in events] == ["status"]
    assert _status(events) == "Footprint unavailable: No model on the map matches 'x-1'."


def test_a_failed_request_is_shown_not_raised(monkeypatch):
    def post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise OSError("timed out")

    monkeypatch.setattr("open_webui_plugins.carbon_estimate._post", post)
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    assert _status(_run_outlet(Filter(), body, {"id": "acme/m-70b", "info": {}})) == "Footprint unavailable: timed out"


def test_an_api_caller_without_an_emitter_gets_nothing_and_no_request(monkeypatch):
    sent = _fake_server(monkeypatch, _tool_result(_model_estimate()))
    body = {"messages": [{"role": "assistant", "content": "Hello", "usage": {"completion_tokens": 850}}]}
    assert _run_outlet(Filter(), body, {"id": "acme/m-70b", "info": {}}, with_emitter=False) == []
    assert sent == []


def test_the_filter_is_a_toggle():
    assert Filter().toggle is True
