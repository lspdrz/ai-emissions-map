# Add a model

## Use this when
A route serves a model that EcoLogits' catalogue does not contain (`build.validate` reports
"model … is not in EcoLogits or sources/models/"), or the developer's model card contradicts the
catalogue's parameter counts.

## Inputs you need
- The model card or paper from the developer, giving the architecture (dense or mixture of
  experts) and the parameter counts: active and total, in billions.

## Files this changes
1. `sources/models/<slug>.yaml`, new.

## Procedure
1. **Check the catalogue first:**
   ```bash
   uv run python -c "from build.models import packaged_ecologits_models as m; print('\n'.join(sorted({x['name'] for x in m()})))" | grep -i <name>
   ```
   If the model is there and its counts agree with the model card, use that id as the route's
   `model` and stop. If its counts are wrong and the id is not kebab-case (for example
   `owner/Name-1.5`), a curated file cannot shadow it: create the file under a new slug below and
   point the route's `model` at that slug.
2. **Pick the slug:** the developer's model name in lowercase kebab-case, with dots as hyphens
   (`Example-1.5-70B` → `example-1-5-70b`). A curated file can only shadow an EcoLogits id that is
   itself kebab-case (see [`../reference/identity.md`](../reference/identity.md#models)).
3. **Capture the model card** with `uv run python -m build.fetch_source <url>` and write `shows`
   quoting the parameter counts.
4. **Write the file:**
   ```yaml
   name: example-1-5-70b
   display_name: Example 1.5 70B
   architecture: dense        # dense | moe
   active_b: 70               # a number, or {min: …, max: …} when only a range is published
   total_b: 70
   evidence:
   - url: https://huggingface.co/example/Example-1.5-70B
     shows: 'Model card: "a 70B parameter dense decoder-only model"'
     accessed: "2026-10-11"
     http_status: 200
     content_sha256: <from fetch_source>
     kind: primary
     capture: auto
   ```
   For a dense model, `active_b` equals `total_b`. A developer's own card is `primary`; an
   estimate from anyone else is `corroborating`, and `comments` says whose estimate it is.

## Validation
```bash
uv run python -m build.validate
```
It must print `0 error(s)`, and the route that needed the model must no longer be reported.

## Expected PR contents
The model file, usually together with the route that serves it.

## Stop and escalate when
- The architecture or the active parameter count of a mixture-of-experts model is not published.
- The provider serves a quantized or otherwise modified version, and you cannot tell whether that
  changes the parameter counts.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../methodology.md`](../methodology.md)
