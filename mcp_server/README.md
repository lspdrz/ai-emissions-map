# MCP server

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets any AI agent look up the energy and
carbon footprint of a response from the AI Emissions Map. It works with any MCP client or agent framework that can
connect to a remote server over Streamable HTTP. It is read-only: it serves the published release,
[`data/data.json`](../data/data.json).

## Connect an agent

The server is hosted, so there is nothing to install:

| | |
|---|---|
| **Name** | `ai-emissions-map` |
| **URL** | `https://ai-emissions-map-19055002993.europe-north2.run.app/mcp` |
| **Transport** | Streamable HTTP, stateless, JSON responses |
| **Authentication** | none |

How you register a server depends on the client, so follow its documentation for adding a remote MCP server and give
it the URL above. Many clients read a JSON file listing servers; the names of its fields, especially the one for a
remote server's URL, differ between them.

### Check the connection

The server answers plain JSON-RPC over `POST`, so you can test it with `curl` and no client (a `GET` returns 405):

```bash
curl -s -X POST https://ai-emissions-map-19055002993.europe-north2.run.app/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

It lists the two tools below with their arguments. To call one, send a `tools/call` request:

```bash
curl -s -X POST https://ai-emissions-map-19055002993.europe-north2.run.app/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"estimate_route_emissions","arguments":{"route":"deepseek-deepseek-v4-pro-0813","output_tokens":1000}}}'
```

## Tools

| Tool | Arguments | Returns |
|---|---|---|
| `estimate_emissions` | `model` (the model's name, such as `Mistral Medium 3.5`), `output_tokens` | The footprint of the response on **every route** the map has for the model: each organization that serves it and where, with its rating. It never picks one. |
| `estimate_route_emissions` | `route` (a route's slug, such as `scaleway-mistral-medium-3-5-128b`), `output_tokens` | The footprint on **one route**, for a caller who knows which route serves it. |

Both return ranges: energy in Wh, and carbon (`co2e_g`) and embodied emissions in grams of CO2e. A route with no
grid has its energy and a null `co2e_g`, with `gap` saying why. The figures count output tokens only, and the
release's `draft` flag says whether the data is still a draft. An unknown model or route returns an error that lists
the ones on the map.

## Using it from an agent

Each tool's description to the agent carries the rules for reporting the figures, so an agent that reads tool
descriptions needs nothing more. In short:

- **Call it when asked about the carbon, energy or climate impact** of a response, a conversation or a model, instead
  of estimating from memory.
- **Pass the response's output tokens.** If the agent cannot count them, it should estimate them, reasoning tokens
  included when known.
- **Use `estimate_emissions` unless the user has named the route** that serves them, in which case use
  `estimate_route_emissions`. The agent must never guess a route or choose one from the user's location: providers
  route requests by the customer's settings.
- **Report ranges, with each route's organization, where it runs and its rating.** Give a carbon figure only where
  `co2e_g` is not null; where it is null, give the energy and the `gap`, never another route's figure.
- **Say that the figures count output tokens only,** and that they are a draft while `release.draft` is true.