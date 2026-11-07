# Open WebUI plugins

Plugins that bring the [AI Emissions Map](https://ai-emissions-map.vercel.app) into [Open WebUI](https://openwebui.com).
Each is one file an admin pastes in, and each talks to the map's hosted MCP server.

## Carbon estimate

[`carbon_estimate.py`](carbon_estimate.py) is a filter that shows each response's energy and carbon footprint, from the
map, on the message itself.

It reads the model and the response's output tokens in Open WebUI and asks the map's hosted MCP server for the
footprint by sending the route and the token count.

### Install

Only an admin can install a filter.

1. In Open WebUI, open **Admin Panel > Functions**, add a new function, and paste in
   [`carbon_estimate.py`](carbon_estimate.py).
2. Turn it on, and attach it to the models it should run on (each model's settings, under **Filters**), or make it
   global.
3. Set the **routes** valve, as `model=route`
pairs separated by commas:

```
mistral-medium-3.5-128b=scaleway-mistral-medium-3-5-128b, gpt-oss-120b=scaleway-gpt-oss-120b
```

- The **model** is its ID in Open WebUI (in the model's settings). A workspace model also matches the route saved
  for its base model.
- The **route** is its slug on the map: the organization and the model, as listed on the AI Emissions Map site.

A model without a saved route shows every route the map has for it, with the range across them.

### Token counts

The filter uses the output tokens the provider reports. When a provider reports none, it estimates them from the
reply's text, at about 4 characters a token, and says so on the message. That estimate leaves out reasoning a
provider hides, so it can be well short for a reasoning model. Turn **estimate tokens from text** off to show only
figures from the provider's count.
