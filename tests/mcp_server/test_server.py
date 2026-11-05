import asyncio

from mcp import Client
from mcp.types import CallToolResult, TextContent

from mcp_server import server
from tests.builders.data import make_data, make_data_meta, make_data_model, make_data_organization, make_data_route
from tools.estimate_emissions import estimate

# Each test builds the release it reads, every field stated, sets it by replacing published_data, and talks to the
# server through its own in-memory MCP client, as a chat app would.


# estimate_emissions: the energy and carbon of a response on every route of its model.


def _call_estimate_emissions_tool(model: str, output_tokens: int) -> CallToolResult:
    """Call estimate_emissions as a chat app would: through an in-memory MCP client."""

    async def call_tool():
        async with Client(server.mcp) as client:
            return await client.call_tool("estimate_emissions", {"model": model, "output_tokens": output_tokens})

    return asyncio.run(call_tool())


def test_estimate_emissions_is_offered_taking_a_model_and_its_output_tokens():
    async def list_tools():
        async with Client(server.mcp, raise_exceptions=True) as client:
            return (await client.list_tools()).tools

    tool = {tool.name: tool for tool in asyncio.run(list_tools())}["estimate_emissions"]
    assert set(tool.input_schema["properties"]) == {"model", "output_tokens"}
    assert set(tool.input_schema["required"]) == {"model", "output_tokens"}


def test_estimate_emissions_returns_the_estimate_as_structured_content(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Acme 1, Geneva",
                default=True,
                letter="A",
                gap=None,
                served_as=None,
                energy={"low": 0.6, "high": 0.8},
                embodied={"low": 0.05, "high": 0.05},
                grid_intensity={"low": 30.0, "high": 30.0},
                sci={"low": 0.068, "high": 0.074},
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)

    result = _call_estimate_emissions_tool("M 70B", 500)
    assert not result.is_error
    assert result.structured_content == estimate("M 70B", 500)


def test_estimate_emissions_on_a_route_without_a_grid_returns_null_grams(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[make_data_organization(slug="acme", display_name="Acme")],
        routes=[
            make_data_route(
                slug="acme-m-70b",
                org="acme",
                model="m-70b",
                label="Not disclosed",
                default=True,
                letter="D",
                gap="Location not disclosed by the provider.",
                served_as=None,
                energy={"low": 3.0, "high": 8.0},
                embodied={"low": 0.09, "high": 0.09},
                grid_intensity=None,
                sci=None,
            )
        ],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)

    result = _call_estimate_emissions_tool("M 70B", 500)
    assert result.structured_content is not None
    [route] = result.structured_content["routes"]
    assert route["co2e_g"] is None
    assert route["embodied_g"] is None
    assert route["energy_wh"] == {"low": 1.5, "high": 4.0}


def test_estimate_emissions_on_an_unknown_model_is_a_tool_error_naming_the_models(monkeypatch):
    data = make_data(
        schema="aem-data/4",
        meta=make_data_meta(
            release_date="2026-10-28",
            methodology_version="0.4.0",
            ecologits_version="0.11.2",
            draft=True,
            functional_unit_tokens=1000,
        ),
        models=[make_data_model(slug="m-70b", display_name="M 70B")],
        organizations=[],
        routes=[],
    )
    monkeypatch.setattr("tools.estimate_emissions.published_data", lambda: data)

    result = _call_estimate_emissions_tool("X 9", 500)
    assert result.is_error
    [content] = result.content
    assert isinstance(content, TextContent)
    assert "No model on the map matches 'X 9'. Models: M 70B." in content.text


# Starting the server: stdio by default, stateless HTTP on Cloud Run's $PORT with --http.


def test_main_without_arguments_runs_over_stdio(monkeypatch):
    calls = []
    monkeypatch.setattr(server.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    server.main([])
    assert calls == [((), {})]


def test_main_with_http_runs_stateless_json_on_the_port_given(monkeypatch):
    calls = []
    monkeypatch.setattr(server.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setenv("PORT", "9999")
    server.main(["--http"])
    assert calls == [
        (
            ("streamable-http",),
            {"host": "0.0.0.0", "port": 9999, "stateless_http": True, "json_response": True},
        )
    ]
