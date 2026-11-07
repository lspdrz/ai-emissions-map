# Open WebUI plugins

Plugins that bring the [AI Emissions Map](https://ai-emissions-map.vercel.app) into [Open WebUI](https://openwebui.com).
Each is one file an admin imports into Open WebUI, and each talks to the map's hosted MCP server.

## Carbon estimate

[`carbon_estimate.py`](carbon_estimate.py) is a filter that shows each response's carbon footprint, from the map, on
the message itself:

- **the grams of CO₂e** on the message, which show everyday equivalents when clicked: an LED bulb, a phone charge and
  a petrol car;
- **a source** under the message with the details: where the route runs, its rating, its energy, and the release the
  figures come from.

It reads the model and the response's output tokens in Open WebUI, and sends the map's hosted MCP server the route (or
the model) and the token count, nothing else.

### Install

Only an admin can install a filter.

1. In Open WebUI, open **Admin Panel > Functions**, click **Import from URL**, and paste:

   ```
   https://github.com/lspdrz/ai-emissions-map/blob/main/open_webui_plugins/carbon_estimate.py
   ```

   Review the code and save.
2. Turn it on, and either make it **Global** (the ⋮ menu in the list of functions) or attach it to the models it
   should run on (**Workspace > Models**, edit the model, **Filters**). It runs on every reply of those models.
3. Under each model's **Capabilities** (**Workspace > Models**, edit the model), turn on **Usage**, so that Open WebUI
   asks the provider for the reply's token count.
4. Set the **routes** valve (the gear icon in the list of functions), as `model=route` pairs separated by commas:

   ```
   swiss-ai/apertus-v1.5-70b=public-ai-apertus-v1-5-70b, mistral-medium-3.5-128b=scaleway-mistral-medium-3-5-128b
   ```

   - The **model** is its ID in Open WebUI, exactly as the model's settings show it: the provider's name for it,
     not the map's. A workspace model also matches the route saved for its base model.
   - The **route** is its slug on the map, shown under each route on the AI Emissions Map site.

   A model without a saved route shows every route the map has for it, across the range of their figures.

### Update

Open WebUI does not update an imported function, and refuses to import it again under the same ID. To update it,
open it in **Admin Panel > Functions**, replace its code with the [latest version](carbon_estimate.py), and save; its
valves are kept. The `version` in the file's header says which one you have.

### Token counts

The filter uses the output tokens the provider reports. When a provider reports none, it estimates them from the
reply's text, at about 4 characters a token, and says so in the source. That estimate leaves out reasoning a provider
hides, so it can be well short for a reasoning model. Turn **estimate tokens from text** off to show only figures from
the provider's count.