# Serving-locations schema

[`serving-locations.v1.schema.json`](serving-locations.v1.schema.json) is the JSON Schema for the
**serving-locations file**: a small JSON file an organization that serves AI models can publish on its own domain to
say where each model actually runs. The AI Emissions Map reads it to rate how precisely the organization
discloses its serving locations, and to choose the electricity grids its carbon intensities use.

This page is for organizations that want to publish one. The schema describes every field, and
[`EXAMPLES.md`](EXAMPLES.md) has complete files for common setups.

## Why publish one

Every route on the map (one organization serving one model, by default or in a region a customer chooses) gets a
**location disclosure rating**, from A to D, and every organization a rating averaged from its routes' ratings. Without a
file, the rating is derived from independent research.

A serving-locations file on your own domain is a primary source: it states your locations directly, so your
routes get the best rating your real setup supports. It does not make a carbon-heavy grid look clean: the carbon
intensity still uses the grid your requests run on. What it does is make it precise. A route that could run in
any of twenty regions is calculated across all their grids; a route you place on one grid is calculated on that
grid alone.

## How the rating follows from the file

For each model, `routing` lists the ways a customer can have it served: the default (marked `"default": true`, and
always first), and each region or zone a customer can choose instead. Each entry becomes one route on the map,
and each route gets its own rating from its `locations`:

| What the route's `locations` state | Rating |
|---|---|
| Every location names a `facility`, with its `operator` and `city` | **A** |
| The facilities aren't disclosed, but the locations resolve to one grid | **B** |
| The facilities aren't disclosed, and the locations resolve to more than one grid | **C** |
| Nothing about the model or the organization's routes | **D** |

List every location a route's requests may run in, failover and overflow sites included: leaving one out makes the
route look more precise than it is. Facilities are identified by name and city; a street address is never asked
for. That is enough for the grid and the rating, and it answers the security concern that is the most common
reason for keeping data-center locations private.

Publish one file per organization, covering every service and model you want rated. A model the file leaves out is
rated from your other publications, as it would be without a file.

## Adding your facilities' PUE

A location that names its `facility` can also give its **PUE** (Power Usage Effectiveness): the building's total
energy divided by the energy of its computing equipment, measured over twelve months, with the last day of that
period:

```json
{ "facility": "Example Geneva 1", "operator": "Example AI", "city": "Geneva", "country": "CH", "grid_zone": "CH",
  "pue": { "value": 1.15, "period_end": "2025-12-31" } }
```

The map computes each route's energy with the PUE of the buildings it runs in when every location on the route has
one, and with a range of 1.09 to 1.54 otherwise. Give a value measured over a full year (a calendar year, or the
trailing twelve months), never a design target, a single month or an average across your facilities. The PUE
changes the carbon intensity, not the rating.

## Publishing it

1. **Write the file.** The smallest useful file names one service and one model, served by default from one facility:

   ```json
   {
     "schema": "ai-emissions-map/serving-locations/v1",
     "organization": "Example AI",
     "contact": "sustainability@example.com",
     "published": "2026-10-01",
     "services": [
       {
         "service": "Example API",
         "endpoint": "https://api.example.com/v1",
         "models": [
           {
             "model": "example-labs/Example-12B",
             "routing": [
               {
                 "name": "standard",
                 "default": true,
                 "locations": [
                   { "facility": "Example Geneva 1", "operator": "Example AI", "city": "Geneva", "country": "CH", "grid_zone": "CH" }
                 ]
               }
             ]
           }
         ]
       }
     ]
   }
   ```

   `model` is the exact version you serve, as its Hugging Face repository id where one exists. `grid_zone` is
   optional but recommended: an [Electricity Maps](https://app.electricitymaps.com/map) zone code removes any
   doubt about which grid a location draws from. List every model you want rated, in every service.
   [`EXAMPLES.md`](EXAMPLES.md) shows files with several facilities, cloud regions, no default, and a failover site.
2. **Check it against the schema** with any JSON Schema (draft 2020-12) validator, for example:

   ```bash
   uvx check-jsonschema --schemafile serving-locations.v1.schema.json ai-serving-locations.json
   ```

   A file that fails the schema is not used.
3. **Host it at `https://<your-domain>/.well-known/ai-serving-locations.json`**, the
   [well-known location](https://www.rfc-editor.org/rfc/rfc8615) where the map looks for it. If you publish a
   [`carbon.txt`](https://www.thegreenwebfoundation.org/news/green-hosting-providers-can-use-carbon-txt/), it can
   link to the file.
4. **Keep it current.** Update the file, and its `published` date, whenever your routing changes.

The map's curators read the file and record its locations as your routes, citing it as evidence.
