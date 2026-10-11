<!--
Canonical methodology copy for the AI Emissions Map.

This file is HAND-AUTHORED and is the single source of truth for the methodology prose shown on
the site. It is NOT generated. The site renderer reads it at build time, substitutes the
{placeholders} below with values computed from the release, converts the Markdown to HTML, and
publishes it. The document has exactly two top-level "## " sections, in order: the first (Summary)
feeds the site header, the second (the body) feeds the Methodology page. Keep it to these two.

Placeholders (filled from the release at build time):
  {release_date} {methodology_version} {ecologits_version} {grid_year}
  {n_orgs} {n_routes} {n_models} {n_scored} {n_unscored} {n_rated_a_or_b}

Write prose in the academic register of a methods section: precise, defined, measured, and
forthright about limitations. No marketing cadence. The rulings log (docs/rulings/log.yaml)
records why each rule was chosen; this file states the rules.
-->

## Summary

We assess {n_routes} routes by which {n_orgs} organizations serve {n_models} AI models. Each route, a provider serving a model from a location, receives a **carbon score**: the estimated emissions of generating 1,000 output tokens, calculated from the energy the model requires and the embodied emissions of the hardware it runs on (EcoLogits), and the carbon intensity of the electricity where the route runs (Electricity Maps). Each organization receives a **location disclosure rating** (A–E) for how precisely it reveals where its routes run. Every score is an estimate and is shown as a range; routes whose location is undisclosed are not scored.

## Full methodology

The map rests on one observation: efficiency is not environmental cost. A model served efficiently from a high-emission grid can emit more than a less efficient model served from a low-emission one. Grid carbon intensity varies by more than an order of magnitude between locations, while differences in serving efficiency are typically a factor of two to five. Where a model runs is therefore the decisive variable, and the one that providers are not required to disclose.

The framework has two levels of analysis:

- **Each route** receives a carbon score, calculated in the same way for every route from two public sources. Nothing in the score is set by curators.
- **Each organization** receives a location disclosure rating, derived from how precisely its routes' locations are established by its own publications. This is the part of the map that rests on research.

### The carbon score

The calculation follows the Software Carbon Intensity specification (SCI, ISO/IEC 21031:2024):

```
SCI = ((E × I) + M) per R
```

where E is the energy consumed, I the carbon intensity of the electricity, M the embodied emissions of the hardware allocated to the work, and R the functional unit. We set **R = 1,000 output tokens**. The carbon score is the **full SCI**, in grams of CO₂-equivalent per thousand output tokens, and is always presented with its two parts: the **operational part**, E × I, and the **embodied part**, M.

**Embodied emissions (M)** are the emissions of manufacturing the servers and accelerators, allocated to the work by EcoLogits in proportion to the time a request occupies the hardware over an assumed three-year lifetime. Like energy, M is treated as a property of the model: the same model has the same M on every route. M therefore raises every route serving a model by the same amount, and the differences between those routes come entirely from the operational part. On low-carbon grids M is frequently the larger part. Including it gives the honest total, and narrows the apparent advantage of a clean grid: for one model, the ratio between a route on a 30 gCO₂e/kWh grid and one on a 330 gCO₂e/kWh grid falls from about eleven to about three and a half. The breakdown is shown so that the effect of location remains visible.

**Energy (E)** is a property of the model alone. It is estimated with EcoLogits {ecologits_version} from the served model's active and total parameter counts, using EcoLogits' own estimate of generation speed and a single range of power usage effectiveness (PUE), 1.1–1.6, for every route. PUE is the ratio of a data center's total energy use to the energy used by its computing equipment; EcoLogits applies it as the final step of its calculation, so it scales energy proportionally. It varies widely in practice, from about 1.1 in efficient large facilities to about 1.6 on average and above 2 in older ones. Applying the efficient-facility value to every route would bias every score downward, so the range spans efficient to average facilities, and the resulting uncertainty is carried in the score's range. The same model therefore has the same energy estimate on every route. Where a closed model's size is known only as a range, both ends are evaluated. Models absent from EcoLogits' catalogue are added with their published parameter counts and architecture. Providers' own hardware, serving configurations, and published energy figures are not used in this version, so that every score is produced by one consistent pipeline.

**Grid intensity (I)** is a property of the route's location. It is the annual average carbon intensity of the electricity **consumed** in the route's grid zone, from Electricity Maps' historical datasets for {grid_year}. Consumption-based intensity follows electricity across interconnectors, so a zone that imports from a fossil-heavy neighbor is not credited with its own clean generation alone; for Switzerland, published production-based and consumption-based figures differ by roughly a factor of three. The score uses **direct (operational) emission factors**, the basis of the GHG Protocol's Scope 2 location-based method used in corporate filings. A second score using **life-cycle factors** (adding power-plant construction, fuel supply chains and upstream methane) is shown alongside. Life-cycle grid factors concern power plants, not servers, and do not overlap with M. Each route uses the finest grid zone its location evidence supports, falling back to a country total; where Electricity Maps has no data for a zone, a fallback source is used and flagged.

**Ranges.** Where a route's location is established only as a set of candidates (several countries, for example), I spans the candidates' intensities and the score is reported as a range, from the lowest energy, intensity and embodied emissions to the highest. Where nothing about the location is established, the route is **not scored**. Scores are never reduced to a point; where routes must be ordered, the geometric midpoint is used as a sort key and is not displayed.

**Bands.** Each score is also placed on an absolute scale of five bands, in grams of CO₂e per thousand output tokens: 1 below 0.03, 2 from 0.03 to below 0.1, 3 from 0.1 to below 0.3, 4 from 0.3 to below 1, and 5 at 1 or above. The band edges are about a factor of three apart because scores span three orders of magnitude, from a small model on a low-carbon grid to a large model on a coal-heavy one. Because M is included, each model has a floor below which none of its routes can fall, however clean the grid. The scale is absolute rather than relative to model size: a route serving a larger model emits more per token, and model choice is a genuine lever. The comparison that isolates location, the same model on different grids, appears on each model's page, where every route serves the same model. A score range that falls within one band shows that band; one that crosses bands shows the span.

### Where a route runs

A route's location is recorded at one of five levels: **facility** (a named data center), **region** (a cloud region or equivalent), **country**, **country set** (several possible countries, typically from a subprocessor list), or **unknown**. Each candidate location resolves to a grid zone: a facility through its recorded zone, a cloud region through the provider's published region metadata as normalized by the Green Software Foundation.

Locations are researched from the organization's own publications: hosting pages, documentation, subprocessor lists and data-processing agreements, announcements, and region options. These are **primary** sources. Press coverage, analyst reports and third-party datasets are **corroborating** sources: recorded for context, never sufficient on their own. A location known only from the press is treated as undisclosed. Every source is captured, hashed and dated, and counts only if it was verified as still published and still showing the quoted passage within 90 days of the release date.

Organizations can make their locations directly readable by publishing a serving-locations file on their own domain, in the format the map documents: for each service and exact model version, where default traffic is served (facility, operator, city, country, and grid zone) and which regions a customer can choose. Such a file is a primary source, is re-verified before every release, and maps directly onto the rating described below.

Location belongs to the route, not the model: a developer's statement about where it serves a model establishes nothing about where another provider serves the same weights. Facilities are recorded once and shared by every provider that uses them, with the operator of a building recorded separately from its tenants. A route records the model **actually served**, which may differ from the name under which it is offered; where they differ, both are shown.

Some providers route requests to other providers. For such **aggregator routes**, the published routing weights are recorded as evidence. The route takes the location level of its least-disclosed upstream, is scored only if every upstream is scored, and reports the union of the upstream ranges. Weights are displayed but not used to average, because they describe intended routing rather than measured traffic.

### The location disclosure rating

Each route receives a location disclosure level from its primary evidence: **A** for a facility, **B** for a region, **C** for a country, **D** for a country set, and **E** for an unknown location or one known only from the press. Each route below A states what is missing.

Each organization's rating is the average of its routes' levels, with A counted as 4, B as 3, C as 2, D as 1 and E as 0, each route weighted equally and the result rounded to the nearest letter, ties rounding down. The distribution is always shown with it: an organization with two routes at B and one at E averages 2.0 and is rated C, displayed as "C (2 routes at B, 1 at E)". Only routes for models within the map's scope are curated, so the rating describes those services rather than an organization's entire catalogue. In release {release_date}, {n_rated_a_or_b} of {n_orgs} organizations are rated A or B, and {n_unscored} of {n_routes} routes are not scored for lack of a disclosed location.

The rating measures disclosure, not cleanliness. An organization that discloses a facility on a coal-heavy grid is rated A, and its routes receive high carbon scores; one that discloses nothing is rated E, and its routes are not scored at all.

### Training

This version assesses serving only. Training emissions are not amortized into per-token figures: dividing a one-time impact by the tokens a model later serves makes it shrink toward zero with use, which would hide a real and permanent impact behind a clean serving location. A model trained on a high-emission grid and served from a low-emission one will therefore appear clean here. Each organization's page states that training is not assessed.

### Notice, the right of reply, and errors

Before an organization is first published it is notified, with its draft entry, the evidence and the method, and given 30 days to respond. Thereafter it may submit corrections with evidence, new location disclosures, or a response statement of up to 300 words, published next to the contested item whether or not the data change. Outcomes are recorded as rulings. Where a publication appears internally inconsistent, it is credited for what it plainly discloses, the anomaly is shown, and the organization is asked to clarify; published figures are never silently corrected.

### Versioning and change

Each release states its methodology version ({methodology_version}), grid data year, EcoLogits version and dataset version. Every change in a score or rating between releases is attributed to new evidence, new input data (for example a new grid year or EcoLogits release), or a change of methodology. The band edges, the rating scale and the fixed PUE are deliberate, documented choices, reviewed when the evidence base changes materially. Releases may include a calibration note comparing EcoLogits' energy estimates with independent laboratory measurements for models both cover; it informs readers about the estimate's accuracy and does not change scores.

### Choices made in the presentation

Every carbon score is labeled as an estimate from EcoLogits and Electricity Maps, with its fixed assumptions one step away. Scores are shown as numeric ranges, with their band or band span. A route that is not scored is shown as *not scored*, in words, never as a band. Each score is drawn as a stacked range of its operational and embodied parts, so a reader comparing routes for the same model can see that only the operational part differs. The location rating uses letters and the carbon band uses a numbered color scale, so the two cannot be confused. Map markers are sized by location confidence, so a vague location looks vague.

### Limitations

Several constraints bound the present results and are stated plainly. The assessed set is a curated sample of organizations and of the routes serving in-scope models, not a census. Locations are asserted by curators from public documents, not observed in providers' operations. The carbon score is an estimate built from two models: EcoLogits' energy model assumes NVIDIA H100-class hardware and estimates generation speed from parameter counts, so real deployments may differ by several times, and the fixed PUE range of 1.1–1.6 reflects no particular building, so operators with efficient facilities receive no credit for them and very inefficient facilities are underestimated; providers' actual hardware, efficiency and published energy figures are not reflected. Closed-model sizes are estimates. Embodied emissions rest on life-cycle data for one class of server and a fixed three-year lifetime, and are not given an uncertainty range; newer accelerators, longer service lives or higher utilization would change them. Grid intensity is an annual average and does not reflect when requests are served, nor marginal emissions, and the most recent full year of grid data may precede the release. The score excludes water, networking, storage, users' devices, input-token processing and training. Only text models are assessed. Finally, the band edges and rating scale are editorial choices, not laws of nature.
