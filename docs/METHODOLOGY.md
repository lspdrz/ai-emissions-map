# Summary

We assess the routes through which organizations serve AI models. An **organization** is a company or institution that serves AI models itself, through an API or another service. A **model** is one specific version of an AI model, such as a particular release of an open-weight model. A **route** is one organization serving one model.

Each route receives a **carbon intensity**: the estimated emissions of generating 1,000 output tokens, calculated from the energy the model requires, the embodied emissions of the hardware it runs on, and the **grid intensity** where the route runs: the emissions of each kilowatt-hour of its electricity.

Each organization receives a **location disclosure rating** for how precisely it reveals where its routes' electricity comes from.

# Full methodology

The map rests on one observation: efficiency is not environmental cost. A model served efficiently from a high-emission grid can emit more than a less efficient model served from a low-emission grid.

It works at two levels. Each **route** receives a carbon intensity, calculated the same way for every route. Each **organization** receives a location disclosure rating, based on how precisely its own publications establish where its routes run.

## The carbon intensity

The calculation follows the [Software Carbon Intensity specification](https://greensoftware.foundation/standards/sci/) (SCI, ISO/IEC 21031:2024):

```
SCI = ((E × I) + M) per R
```

where E is the energy consumed, I is the grid intensity of the electricity, M is the embodied emissions of the hardware allocated to the work, and R is the functional unit (1,000 output tokens). The carbon intensity is the full SCI, in grams of CO₂-equivalent per 1,000 output tokens, always shown with its **operational part** (E × I) and its **embodied part** (M).

**Energy (E)** is the electricity needed to generate 1,000 output tokens. It is estimated with EcoLogits from three inputs:

- **The model's size**, its active and total parameter counts. These come from the developer's own publications (model card, published weights, technical report) wherever the developer releases them, and otherwise from EcoLogits' estimate, cited from its catalog. A size known only as a range is evaluated at both ends.
- **Generation speed**, which sets how long a request occupies the server. EcoLogits estimates it from the model's size; no measured speed or latency is used.
- **Power usage effectiveness (PUE)**, a data center's total energy divided by that of its computing equipment: about 1.1 in efficient large facilities, about 1.6 on average, and above 2 in older ones. PUE is a property of the building, so a route uses the published PUE of the buildings when available. The value must be measured over twelve months. A design figure, a best month, an average across a provider's facilities or an upper bound does not count. Where a candidate has no published PUE, the route uses a fallback range of 1.1–1.6, which spans efficient to average facilities.

Apart from PUE, providers' own hardware, serving configurations and published energy figures are not used, so that every carbon intensity comes from one consistent pipeline.

**Grid intensity (I)** is the emissions of the electricity a route draws from the grid it is connected to, in grams of CO₂e per kWh. A grid is the finest area that a facility can draw electricity from. If a facility runs on its own generation, then it is a grid of its own.

Every grid's intensity comes from one source, so that routes are compared on the same basis: [Ember](https://ember-energy.org/)'s yearly emissions intensity of electricity generation, for the grid's **country**, or for its **subdivision** where Ember publishes one: its state in the United States, its province in China. Ember publishes it openly (CC-BY-4.0) for over 200 countries, every US state and every Chinese province. It is a **life-cycle** value: Ember multiplies the electricity generated from each fuel by an IPCC emission factor that counts, in addition to what power plants emit while generating, their construction, fuel supply chains and upstream methane. It is an average of the electricity **generated** in the country or state, so imports and exports are not traced.

The value is for the release's year (2025 in this one) or, where a country or subdivision has none for that year, its most recent earlier year; a later year is never used. The values come from a committed snapshot of Ember's data, refreshed and recorded with their source, and each grid's file records the value it uses, its year and the area it is for, so every carbon intensity can be traced to the figure behind it.

Zones within one country, or one US state or Chinese province, share its value. A facility that runs on its own generation cannot be valued from a country's or subdivision's average, so a route on an on-site grid has no carbon intensity until the method can value it.

**Embodied emissions (M)** are the emissions of manufacturing the hardware that serves a request: the servers and the accelerators (GPUs) in them. EcoLogits estimates how many accelerators the model needs from its size, and gives each request a share of their manufacturing emissions:

- **by time:** the fraction of the hardware's assumed three-year lifetime that generating the request takes;
- **by batch:** that time is shared among the requests the server handles at once.

**Ranges.** Where a route's location is established only as several possible grids, I spans their intensities, and the carbon intensity is a range from the lowest energy, intensity and embodied emissions to the highest. A route whose location is not established has **no carbon intensity**: it is *not calculated*. Carbon intensities are never reduced to a point. Where routes must be ordered, the geometric midpoint is used as a sort key and is not displayed.

**Bands.** Each carbon intensity is placed on an absolute scale of five bands, in grams of CO₂e per 1,000 output tokens: 1 below 0.03, 2 from 0.03 to below 0.1, 3 from 0.1 to below 0.3, 4 from 0.3 to below 1, and 5 at 1 or above. The edges are about a factor of three apart because carbon intensities span three orders of magnitude. Because M is included, each model has a floor no route can fall below, however clean the grid. The scale is absolute, not relative to model size. A range within one band shows that band; a range that crosses bands shows the span.

### Where a route runs

A route's location is recorded as the grids it may draw from and, where the evidence names them, the buildings it runs in. A cloud region resolves to its grids through the provider's published region metadata, as normalized by the Green Software Foundation; a named building gives the grid it draws from, or its own on-site supply.

Locations are researched from the organization's own publications (hosting pages, documentation, subprocessor lists and data-processing agreements, announcements, region options), which are **primary** sources. Press, analysts and third-party datasets are **corroborating**: recorded for context, never sufficient alone, so a location known only from the press is undisclosed. Every source is recorded with the passage it shows and the date it was read, and stands until it is shown to have changed or disappeared.

An organization can make its locations directly readable by publishing a serving-locations file on its own domain, in a format the map documents: for each model, its default routing and each region a customer can choose, with every location requests may run in. The file is a primary source like any other.

Location belongs to the route, not the model. A route records the model **actually served**, which may differ from the name it is offered under; both are then shown. Only organizations that serve models themselves are assessed. A service that only forwards requests to other providers is not, since those requests are assessed at the providers that serve them.

## The location disclosure rating

Each route is rated on how precisely its primary evidence determines where its electricity comes from:

- **A:** it names the facility, the only level at which the building's actual supply can be checked.
- **B:** it determines one grid.
- **C:** more than one grid is possible, including a single zone subdivided into finer ones.
- **D:** the location is unknown, or known only from the press.

The rating is generated from the recorded location, never assigned by hand, and each route below A states what is missing.

An organization's rating is the average of its routes' ratings, with A counted as 3, B as 2, C as 1 and D as 0. Each route is weighted equally, and the result is rounded to the nearest rating, ties rounding down. It is always shown with its distribution: two routes at B and one at D average 1.33, shown as "C (2 routes at B, 1 route at D)". Where customers can choose among regions or jurisdictions, each choice is a separate route, and all of the routes count toward the organization's rating. Only routes for models within the map's scope are curated, so the rating describes those services, not an organization's whole catalog.

The rating measures disclosure, not emissions: an organization that discloses a facility on a coal-heavy grid is rated A, and its routes have high carbon intensities; one that discloses nothing is rated D, and its routes have none.

## Notes

### Training

Only serving is assessed. Training emissions are not spread over per-token figures: dividing a one-time impact by the tokens a model later serves makes it shrink toward zero with use, hiding a real and permanent impact behind a clean serving location. A model trained on a high-emission grid and served from a low-emission one therefore appears clean here.

### Corrections

Anyone, the organization included, may submit corrections or new location disclosures with evidence, which are reviewed like any other change. Where a publication contradicts itself, it is credited for what it plainly discloses, the contradiction is recorded, and the organization is asked to clarify; published figures are never silently corrected.

### Versions

Each release states its methodology version, its grid data (Ember, and the year) and its EcoLogits version. Every change in a carbon intensity or rating between releases comes from new evidence, new input data (a refreshed Ember snapshot or a new EcoLogits release) or a change of method. The band edges, the rating scale and the fallback PUE range are deliberate choices, reviewed when the evidence changes materially.

### Presentation

Every carbon intensity is labeled as a life-cycle estimate from EcoLogits and Ember, and shown as a numeric range with its band or band span and its operational and embodied parts. A route without one says *not calculated* and never shows a band. The disclosure rating uses letters and the carbon band a numbered color scale, so the two cannot be confused.

### Limitations

- The assessed set is a curated sample, not a census.
- Locations are established from public documents, not observed in providers' operations.
- The carbon intensity is an estimate built on two sources: EcoLogits' models for energy and embodied emissions, and Ember's data for grid intensity.
- EcoLogits assumes NVIDIA H100-class hardware and estimates generation speed from parameter counts, so real deployments may differ several-fold.
- A route whose buildings publish no PUE uses the fallback range, which reflects no particular building: efficient operators that publish nothing get no credit, and very inefficient facilities are underestimated. A published PUE is the building's average over a year, not that of the hardware serving the model.
- Providers' actual hardware, efficiency and energy figures are not reflected.
- Closed models' sizes are EcoLogits' estimates.
- Embodied emissions rest on life-cycle data for one class of server and a fixed three-year lifetime, and carry no uncertainty beyond that of the model's parameter counts.
- Grid intensity is an annual average: it reflects neither when requests are served nor marginal emissions.
- Grid intensity is per country, or per state in the United States and per province in China: regions within any other country share one value, and a state or province is not a grid (US grids are balancing authorities, which cross state lines; Chinese provinces trade power across regional grids).
- Grid intensity is production-based: a country that imports fossil-heavy electricity is credited with its own generation alone, and one that exports clean electricity is not credited for it.
- Grid intensity is life-cycle, so carbon intensities are higher than those using direct emission factors.
- Ember applies one emission factor per fuel everywhere: a coal plant counts the same whatever its efficiency or fuel quality.
- The latest full year of grid data may precede the release, and Ember revises recent years.
- Routes on facilities with their own generation have no carbon intensity.
- The carbon intensity excludes water, networking, storage, users' devices, input tokens and training.
