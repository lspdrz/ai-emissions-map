# Add a model

## Use this when
A route serves a model that has no record in `sources/models/` (`build.validate` reports
"model … has no sources/models/…"). Every model a route serves has a record, whether its numbers
come from EcoLogits or from the developer.

## Inputs you need
- The model's id in EcoLogits' catalogue, if it is there.
- Otherwise, or if the developer's own model card contradicts EcoLogits: the model card or paper,
  giving the architecture (dense or mixture of experts) and the parameter counts, active and
  total, in billions.

## Files this changes
1. `sources/models/<slug>.yaml`, new.

## Procedure
1. **Look the model up in the installed EcoLogits catalogue:**
   ```bash
   uv run python -c "from build.models import packaged_ecologits_models as m; print('\n'.join(sorted({x['name'] for x in m()})))" | grep -i <name>
   ```
2. **If EcoLogits has it** (the usual case), write the record from the package; never type the
   numbers by hand:
   ```bash
   uv run python -m build.models --add gemini-3.5-flash
   ```
   This writes `sources/models/gemini-3-5-flash.yaml` with `source: ecologits`, the EcoLogits id
   and version, and the parameter counts. Set `display_name` to the model's public name, and add
   `comments` if useful; leave the other lines to the tool. The route's `model` is the record's
   slug (`gemini-3-5-flash`).
3. **If EcoLogits lacks it, or the developer's model card contradicts it**, write a curated
   record. The slug is the developer's model name in lowercase kebab-case, with dots as hyphens
   (`Example-1.5-70B` → `example-1-5-70b`; see
   [`../reference/identity.md`](../reference/identity.md#models)). Capture the model card with
   `uv run python -m build.fetch_source <url>` and write `shows` quoting the parameter counts:
   ```yaml
   name: example-1-5-70b
   display_name: Example 1.5 70B
   source: curated
   architecture: dense        # dense | moe
   active_b: 70               # a number, or {min: …, max: …} when only a range is published
   total_b: 70
   evidence:
   - url: https://huggingface.co/example/Example-1.5-70B
     shows: 'Model card: "a 70B parameter dense decoder-only model"'
     accessed: "2026-10-12"
     http_status: 200
     content_sha256: <from fetch_source>
     kind: primary
     capture: auto
   ```
   For a dense model, `active_b` equals `total_b`. A developer's own card is `primary`; an
   estimate from anyone else is `corroborating`, and `comments` says whose estimate it is. Where
   the record contradicts EcoLogits, `comments` says so.

## Validation
```bash
uv run python -m build.validate
```
It must print `0 error(s)`, and the route that needed the model must no longer be reported.
Validation also checks every `source: ecologits` record against the installed EcoLogits.

## Expected PR contents
The model file, usually together with the route that serves it.

## Stop and escalate when
- The architecture or the active parameter count of a mixture-of-experts model is not published.
- The provider serves a quantized or otherwise modified version, and you cannot tell whether that
  changes the parameter counts.
- `build.validate` says an EcoLogits record is out of date: that is an EcoLogits upgrade (see
  `AGENTS.md`), not something to fix inside an unrelated PR.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../methodology.md`](../methodology.md)
