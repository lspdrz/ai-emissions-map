# Serving-locations examples

Complete, valid serving-locations files for common setups, each with the routes and ratings the AI Emissions
Map would give it. Organizations, models, facilities and regions are all called "Example", and domains use
`example.com`, which is reserved for documentation; the countries, cities and
[Electricity Maps](https://app.electricitymaps.com/map) zone codes are real, because the map needs a real zone
to find a grid. The [README](README.md) explains the format; the
[schema](serving-locations.v1.schema.json) is the rule each example passes.

1. [One facility](#1-one-facility)
2. [Several facilities, and a choice of one](#2-several-facilities-and-a-choice-of-one)
3. [Cloud regions, without naming facilities](#3-cloud-regions-without-naming-facilities)
4. [No default: the customer always chooses](#4-no-default-the-customer-always-chooses)
5. [A failover site](#5-a-failover-site)

## 1. One facility

A small provider serves one model from the data center it runs itself. One route, the default, in one named
facility, with the facility's PUE over the last calendar year.

```json
{
  "schema": "ai-emissions-map/serving-locations/v1",
  "organization": "Example AI",
  "contact": "hello@example.com",
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
                {
                  "facility": "Example Lausanne 1",
                  "operator": "Example AI",
                  "ownership": "owned",
                  "city": "Lausanne",
                  "country": "CH",
                  "grid_zone": "CH",
                  "pue": { "value": 1.15, "period_end": "2025-12-31" }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

| Route (`name`) | Rating | Why |
|---|---|---|
| `standard` (default) | **A** | The one location names its facility, operator and city |

Its energy is computed with the facility's PUE, 1.15, since its one location has one.

## 2. Several facilities, and a choice of one

Requests are spread across two facilities by default, one owned and one rented in a colocation center. A
customer who wants requests kept in Geneva can call a separate endpoint. Two models share the same routing.

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
          "model": "example-labs/Example-70B",
          "served_as": "example-70b",
          "routing": [
            {
              "name": "standard",
              "default": true,
              "locations": [
                { "facility": "Example Geneva 1", "operator": "Example AI", "ownership": "owned", "city": "Geneva", "country": "CH", "grid_zone": "CH", "share_of_traffic": 0.7 },
                { "facility": "Example Colo Basel", "operator": "Example Colocation", "ownership": "colocation", "city": "Basel", "country": "CH", "grid_zone": "CH", "share_of_traffic": 0.3 }
              ]
            },
            {
              "name": "geneva",
              "endpoint": "https://geneva.api.example.com/v1",
              "locations": [
                { "facility": "Example Geneva 1", "operator": "Example AI", "city": "Geneva", "country": "CH", "grid_zone": "CH" }
              ]
            }
          ]
        },
        {
          "model": "example-labs/Example-12B",
          "routing": [
            {
              "name": "standard",
              "default": true,
              "locations": [
                { "facility": "Example Geneva 1", "operator": "Example AI", "city": "Geneva", "country": "CH", "grid_zone": "CH" },
                { "facility": "Example Colo Basel", "operator": "Example Colocation", "city": "Basel", "country": "CH", "grid_zone": "CH" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

| Route (`name`) | Rating | Why |
|---|---|---|
| Example-70B `standard` (default) | **A** | Both locations name their facility, operator and city |
| Example-70B `geneva` | **A** | Its one location names its facility |
| Example-12B `standard` (default) | **A** | Both locations name their facility |

`share_of_traffic` is shown on the map but not used to weight the carbon intensity.

## 3. Cloud regions, without naming facilities

A larger provider names its regions but not the buildings in them. By default a request may run in any of its
regions; customers can instead choose the EU, the US, or a single region.

```json
{
  "schema": "ai-emissions-map/serving-locations/v1",
  "organization": "Example AI",
  "contact": "climate@example.com",
  "published": "2026-10-01",
  "services": [
    {
      "service": "Example API",
      "endpoint": "https://models.example.com/v1",
      "models": [
        {
          "model": "example-labs/Example-Pro",
          "routing": [
            {
              "name": "global",
              "default": true,
              "locations": [
                { "region": "example-frankfurt", "city": "Frankfurt", "country": "DE", "grid_zone": "DE" },
                { "region": "example-amsterdam", "city": "Amsterdam", "country": "NL", "grid_zone": "NL" },
                { "region": "example-oregon", "country": "US", "grid_zone": "US-NW-BPAT" },
                { "region": "example-virginia", "country": "US", "grid_zone": "US-MIDA-PJM" }
              ]
            },
            {
              "name": "eu",
              "endpoint": "https://eu.models.example.com/v1",
              "locations": [
                { "region": "example-frankfurt", "city": "Frankfurt", "country": "DE", "grid_zone": "DE" },
                { "region": "example-amsterdam", "city": "Amsterdam", "country": "NL", "grid_zone": "NL" }
              ]
            },
            {
              "name": "us",
              "endpoint": "https://us.models.example.com/v1",
              "locations": [
                { "region": "example-oregon", "country": "US", "grid_zone": "US-NW-BPAT" },
                { "region": "example-virginia", "country": "US", "grid_zone": "US-MIDA-PJM" }
              ]
            },
            {
              "name": "example-frankfurt",
              "endpoint": "https://frankfurt.models.example.com/v1",
              "locations": [
                { "region": "example-frankfurt", "city": "Frankfurt", "country": "DE", "grid_zone": "DE" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

| Route (`name`) | Rating | Why |
|---|---|---|
| `global` (default) | **C** | Four possible grids |
| `eu` | **C** | Two possible grids, Germany's and the Netherlands' |
| `us` | **C** | Two possible grids |
| `example-frankfurt` | **B** | One grid |

Naming the facility behind each region would raise every route to A.

## 4. No default: the customer always chooses

A provider has no default location: every customer must pick a region when they set up a deployment. No entry is
marked `default`.

```json
{
  "schema": "ai-emissions-map/serving-locations/v1",
  "organization": "Example AI",
  "contact": "ops@example.com",
  "published": "2026-10-01",
  "services": [
    {
      "service": "Example API",
      "endpoint": "https://deploy.example.com/v1",
      "models": [
        {
          "model": "example-labs/Example-70B",
          "routing": [
            {
              "name": "oslo",
              "locations": [
                { "facility": "Example Oslo 1", "operator": "Example AI", "city": "Oslo", "country": "NO", "grid_zone": "NO-NO1" }
              ]
            },
            {
              "name": "stockholm",
              "locations": [
                { "region": "example-stockholm", "city": "Stockholm", "country": "SE", "grid_zone": "SE-SE3" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

| Route (`name`) | Rating | Why |
|---|---|---|
| `oslo` | **A** | Names its facility |
| `stockholm` | **B** | One grid, no facility named |

At most one entry may be the default, and only the first: a file marking a later entry, or two entries, fails the
schema.

## 5. A failover site

A provider serves from one facility, but sends requests to a second one in another country when the first is down
or full. The customer does not choose this, so the failover site belongs in the default route's `locations`, even
though it carries little traffic.

```json
{
  "schema": "ai-emissions-map/serving-locations/v1",
  "organization": "Example AI",
  "contact": "hello@example.com",
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
                { "facility": "Example Lausanne 1", "operator": "Example AI", "city": "Lausanne", "country": "CH", "grid_zone": "CH", "share_of_traffic": 0.98 },
                { "facility": "Example Lyon 1", "operator": "Example AI", "city": "Lyon", "country": "FR", "grid_zone": "FR", "share_of_traffic": 0.02 }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

| Route (`name`) | Rating | Why |
|---|---|---|
| `standard` (default) | **A** | Both locations name their facility |

The rating stays A, but the carbon intensity is now a range across the Swiss and French grids, because a request may
run on either. Leaving the Lyon site out would make the route look more precise than it is.
