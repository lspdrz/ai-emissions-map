# Add a model

## Use this when
A route serves a model that has no record in `sources/models/` (`build score` reports
"model … has no sources/models/…"). Every model a route serves has a record, with its counts from the
developer, or, where the developer has not released the architecture, from EcoLogits' estimate.

## Inputs you need
- The developer's own publications giving the architecture (dense or mixture of experts) and the parameter
  counts, active and total, in billions (step 1).
- Only if there are none: the model's entry in EcoLogits' catalogue (step 3).

## Files this changes
1. `sources/models/<slug>.yaml`, new.

## Procedure
1. **Research the counts from the developer, most authoritative first:**
   1. the developer's model card (on Hugging Face, or the developer's own site);
   2. the published weights: the parameter count Hugging Face reads from the safetensors files, and
      `config.json` for a mixture of experts' number of experts and how many are active per token;
   3. the developer's technical report or paper;
   4. the developer's announcement or documentation.

   Read each source yourself; never take a count from memory. Press, benchmarks and other people's
   estimates are corroborating only: they never stand in for the developer's figures. When the developer's
   sources disagree (the card says 70B, the weights hold 70.6B), record the figure the developer states and
   note the other in `comments`. EcoLogits' catalogue entry for the model (step 3) lists its `sources`, which
   often include the developer's card. If no developer source gives the counts, go to step 3.
2. **Write the record from the developer.** The slug is the developer's model name in lowercase kebab-case, with
   dots as hyphens (`Example-1.5-70B` → `example-1-5-70b`; see
   [`../reference/identity.md`](../reference/identity.md#models)); `display_name` is the model's public name, and
   the route's `model` is the record's slug. Quote the parameter counts in `shows` from the source that gives
   them, with today's date in `accessed`:
   ```yaml
   name: example-1-5-70b
   display_name: Example 1.5 70B
   architecture: dense        # dense | moe
   active_b: 70               # a number, or {min: …, max: …} when only a range is published
   total_b: 70
   evidence:
   - url: https://huggingface.co/example/Example-1.5-70B
     shows: 'Model card: "a 70B parameter dense decoder-only model"'
     accessed: "2026-10-12"
     kind: primary
   ```
   For a dense model, `active_b` equals `total_b`. An estimate from anyone else may be added as
   `corroborating` alongside the developer's figures, with `comments` saying whose estimate it is. Where the
   record contradicts EcoLogits, `comments` says so.
3. **Only if the developer gives no counts, use EcoLogits' estimate.** Open EcoLogits' catalogue at the
   installed version, `https://github.com/genai-impact/ecologits/blob/<version>/ecologits/data/models.json`, where
   `<version>` is the `ecologits==` pin in `pyproject.toml`, and find the model's entry: its `architecture`
   (`type` and `parameters`), `warnings` and `sources`. If its warnings include `model-arch-not-released`, the
   counts are EcoLogits' estimate: copy the architecture and counts exactly, cite the catalogue at the installed
   version as `corroborating`, quoting the entry and its warnings, and say in `comments` that the counts are its
   estimate:
   ```yaml
   name: example-flash-2-5
   display_name: Example Flash 2.5
   architecture: moe
   active_b: { min: 40, max: 120 }
   total_b: 400
   evidence:
   - url: https://github.com/genai-impact/ecologits/blob/0.11.2/ecologits/data/models.json
     shows: 'EcoLogits catalogue, "example-flash-2.5": architecture "moe", parameters "total": 400, "active": {"min": 40, "max": 120}; warnings "model-arch-not-released"'
     accessed: "2026-10-19"
     kind: corroborating
   comments: >-
     EcoLogits marks Example Flash 2.5's architecture as not released by Example Lab: these counts are its estimate.
   ```
   If the entry has no such warning, EcoLogits copied the counts from a developer source: find it among the
   entry's `sources` and go back to step 2. If EcoLogits lacks the model, stop (see "Stop and escalate when").

## Validation
```bash
uv run python -m build score
uv run python -m build release
```
`score` rewrites the carbon intensity of every route that serves the model; `release` rewrites `web/data/data.json`.
Both must end without `ERROR:` lines; commit everything they write. The route that needed the model must no longer be reported.
`score` also checks that every record has evidence; whether the evidence is good is for the pull request's
review.

## Expected PR contents
The model file, usually together with the route that serves it.

## Stop and escalate when
- Neither the developer nor EcoLogits gives the parameter counts: write no record, and ask the maintainer. Do
  not record any other estimate in their place.
- The architecture or the active parameter count of a mixture-of-experts model is not published.
- The provider serves a quantized or otherwise modified version, and you cannot tell whether that
  changes the parameter counts.
- A record cites an older EcoLogits catalogue than the installed one: that is an EcoLogits upgrade (see
  `AGENTS.md`), not something to fix inside an unrelated PR.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`METHODOLOGY.md`](../METHODOLOGY.md)
