"""Gate: every route's stored carbon score is what `python -m build score` computes now.

Recomputes from the committed files (sources/, the cloud-region table, the installed EcoLogits)
and compares with each route's carbon_score: field; build/check_disclosure_ratings.py checks the disclosure
ratings and build/grid_emissions.py each grid's intensity. CI runs it: a pull request that changes facts, code, a grid
file or EcoLogits without rerunning score fails.

    uv run python -m build check-carbon-scores
"""

from __future__ import annotations

from pathlib import Path

from build.schemas.carbon_score import CarbonScore
from build.score import score
from build.types import ScoreRun

RUN = "run `python -m build score`"
# The keys of a route's carbon_score: field.
CARBON_KEYS = tuple(CarbonScore.__annotations__)


def check_carbon_scores(root: Path) -> ScoreRun:
    """python -m build check-carbon-scores: run score without writing, then one message per route whose stored carbon
    score is missing or differs from what score computes now, naming what moved. score's errors, if it has any. Writes
    nothing."""
    run = score(root, write=False)
    if run.errors:
        return ScoreRun(run.errors, [])
    messages = []
    for name in sorted(run.routes):
        stored, computed = run.data["routes"][name].get("carbon_score"), run.routes[name]["carbon_score"]
        if stored is None:
            messages.append(f"routes/{name}.yaml: is missing the carbon_score field; {RUN}")
            continue
        moved = [k for k in CARBON_KEYS if stored.get(k) != computed[k]]
        if moved:
            messages.append(f"routes/{name}.yaml: its carbon score is out of date ({', '.join(moved)}); {RUN}")
    return ScoreRun(messages, [])
