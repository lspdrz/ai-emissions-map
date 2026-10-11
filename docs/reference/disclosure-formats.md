# Disclosure formats

Two machine-readable files that organizations can publish on their own domain so that the AI Emissions Map
can read their disclosures directly. A file published on the organization's own domain is a **primary
source**; the map fetches it, hashes it, and re-verifies it before every release.

| Format | Status | What it changes |
|---|---|---|
| **Serving locations** (`serving-locations/v1`) | **v1**: template and schema published | Determines each route's location disclosure level (A–E) and the grid zones used in the carbon score |
| **Model energy** (`model-energy/v0-draft`) | **v2 preview**: not used in v1 | In v2, replaces the EcoLogits energy estimate for a model when a qualifying disclosure exists |

Both are designed to sit alongside existing work rather than compete with it: an organization's
[`carbon.txt`](https://www.thegreenwebfoundation.org/news/green-hosting-providers-can-use-carbon-txt/) (Green Web Foundation) can link to them, and the IETF
`sustainability-data` well-known URI draft is a natural location for the JSON. Suggested paths:
`/.well-known/ai-serving-locations.json` and `/.well-known/ai-model-energy.json`.

---

## 1. Serving locations (v1)

Where each model the organization serves actually runs, by default and when a customer pins a region.

### Example

```json
{
  "schema": "ai-emissions-map/serving-locations/v1",
  "organization": "Example AI",
  "published": "2026-10-01",
  "valid_until": "2027-03-31",
  "contact": "sustainability@example.ai",
  "services": [
    {
      "service": "Example AI API",
      "endpoint": "https://api.example.ai/v1",
      "models": [
        {
          "model": "swiss-ai/Apertus-v1.5-70B",
          "served_as": "apertus-70b",
          "default_routing": [
            {
              "facility": "Geneva 1",
              "operator": "Example AI",
              "ownership": "owned",
              "city": "Geneva",
              "country": "CH",
              "grid_zone": "CH",
              "share_of_traffic": 0.8
            },
            {
              "facility": "Zurich Colo 3",
              "operator": "ColoCorp AG",
              "ownership": "colocation",
              "city": "Zurich",
              "country": "CH",
              "grid_zone": "CH",
              "share_of_traffic": 0.2
            }
          ],
          "pinnable_regions": [
            { "region": "ch-geneva", "facility": "Geneva 1", "grid_zone": "CH" }
          ]
        }
      ]
    }
  ]
}
```

### Fields

| Field | Required | Meaning |
|---|---|---|
| `schema` | yes | Format identifier and version |
| `organization`, `contact` | yes | Who publishes the file and who answers questions about it |
| `published`, `valid_until` | yes | Date of publication and the date after which the file should be treated as stale |
| `services[].service`, `endpoint` | yes | The service and the API endpoint the routing applies to |
| `models[].model` | yes | The **exact model version actually served** (a Hugging Face repository id where one exists) |
| `models[].served_as` | if different | The name under which the model is offered (alias or label) |
| `default_routing[]` | yes | Where requests go when the customer does not pin a region. This is what the rating uses |
| `facility`, `operator`, `ownership` | for level A | The facility's name, who operates the building (which may differ from the provider, as in colocation), and `owned` / `colocation` / `hpc_center` / `gpu_cloud` |
| `city`, `country` | for levels A–C | Location at city level; a street address is not required |
| `grid_zone` | recommended | Electricity Maps zone code; removes any ambiguity in the carbon score |
| `region` | for level B | A cloud region or provider region, when facilities are not named |
| `share_of_traffic` | optional | Intended share of default traffic per location. Shown, not used to average in v1 |
| `pinnable_regions[]` | optional | Regions a customer can choose; each becomes an additional route |

### How it maps to the location disclosure rating

For each model's `default_routing`:

| What the file states | Route level |
|---|---|
| Every entry names a `facility` (with `operator` and `city`) | **A** |
| Every entry names at least a `region` | **B** |
| Every entry names at least a `country` (a single one) | **C** |
| Entries name several possible countries without regions or facilities | **D** |
| The model is not listed, or no file exists | **E** |

Where entries differ in precision, the route takes the level of the **least precise** entry.

### Notes

- **Facilities are identified by name and city, not street address.** This is enough for the grid zone and for the rating, and addresses the security concern that is the most common reason for withholding data-center locations.
- **One file per organization,** covering every service and model it wants rated. Models it omits are rated E.
- **Keeping it current:** the file is re-fetched before every quarterly release. An expired `valid_until` or a file that no longer loads makes its routes revert to the best other primary evidence available, or to E.

---

## 2. Model energy (v2 preview, not used in v1)

In v1, every model's energy comes from EcoLogits. In v2, the map will apply one conditional:

> **If a qualifying energy disclosure exists for the exact model version, use it. If not, derive energy from EcoLogits.**

The format below is what a model developer or provider would publish to qualify.

### Example

```json
{
  "schema": "ai-emissions-map/model-energy/v0-draft",
  "publisher": "Example AI",
  "published": "2026-10-01",
  "contact": "sustainability@example.ai",
  "measurements": [
    {
      "model": "swiss-ai/Apertus-v1.5-70B",
      "precision": "bf16",
      "service": "api",
      "it_energy_wh_per_1k_output_tokens": 0.48,
      "boundary": "server",
      "includes": ["gpu", "cpu", "memory", "networking_in_server", "idle_share"],
      "facility_pue": 1.08,
      "workload": {
        "input_tokens_per_request_mean": 850,
        "output_tokens_per_request_mean": 410,
        "batching": "continuous, production traffic",
        "period": { "start": "2026-07-01", "end": "2026-09-30" }
      },
      "hardware": { "accelerator": "NVIDIA H200", "accelerators_per_replica": 4 },
      "method": {
        "description_url": "https://example.ai/sustainability/energy-method",
        "tooling": "server power meters (BMC), aggregated per model",
        "independent_verification": null
      },
      "embodied_gco2e_per_1k_output_tokens": null
    }
  ]
}
```

### What makes a disclosure qualify (draft rules for v2)

| Requirement | Why |
|---|---|
| **Exact model version and precision** | Versions are distinct models; a quantized model is not the same as full precision |
| **Energy per 1,000 output tokens at the IT (server) level**, `boundary: server` | Comparable with EcoLogits, which models server energy. GPU-only measurements understate energy and do not qualify |
| **Facility overhead excluded from the figure, PUE reported separately** | Keeps v1's principle that only the grid differs by location: the map applies its own PUE (1.1–1.6 in v1; a facility's published PUE once facility-specific PUE lands, the major v2 aim) to every model, so a provider is neither rewarded nor penalized for its building in the energy term. `facility_pue` is recorded for a possible later use |
| **Workload description**: tokens per request, batching, measurement period | Energy per token depends heavily on traffic shape; a figure measured on an idle benchmark is not comparable with production |
| **A published method** | So readers can judge the figure; figures without a method do not qualify |
| **Measurement period within the last 24 months** | Serving stacks change quickly |

Embodied emissions are optional: if `embodied_gco2e_per_1k_output_tokens` is absent, M continues to come from EcoLogits.

### How v2 would use it

1. If a qualifying measurement exists for the route's exact model version (and service), E = `it_energy_wh_per_1k_output_tokens` × the map's fixed PUE.
2. Otherwise, E comes from EcoLogits exactly as in v1.
3. The route shows which source its energy came from ("measured by Example AI" or "estimated by EcoLogits"), and the calibration note compares the two wherever both exist.

Because energy remains a property of the model, a measurement published by a model's developer would apply to every route serving that exact version, unless a provider publishes its own measurement for its route. Whether provider-specific measurements should override the developer's figure is an open question for v2.
