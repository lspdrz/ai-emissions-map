"""Gate: every stored disclosure letter and organization rating is what `python -m build score` computes now.

Recomputes from the committed files and compares with each route's and each organization's disclosure_rating:
field (build/check_carbon_scores.py checks the carbon scores). CI runs it.

    uv run python -m build check-disclosure-ratings
"""

from __future__ import annotations

from pathlib import Path

from build.schemas.disclosure_rating import DisclosureRating
from build.score import ScoreRun, score

RUN = "run `python -m build score`"
# The keys of a route's disclosure_rating: field.
DISCLOSURE_KEYS = tuple(DisclosureRating.__annotations__)


def check_disclosure_ratings(root: Path) -> ScoreRun:
    """python -m build check-disclosure-ratings: run score without writing, then one message per organization rating,
    then per route letter, that is missing or differs from what score computes now, naming what moved. score's errors,
    if it has any."""
    run = score(root, write=False)
    if run.errors:
        return ScoreRun(run.errors, [])
    data, routes, orgs = run.data, run.routes, run.orgs
    messages = []
    for name in sorted(orgs):
        stored = data["organizations"][name].get("disclosure_rating")
        if stored is None:
            messages.append(f"organizations/{name}.yaml: is missing the disclosure_rating field; {RUN}")
            continue
        moved = [k for k in orgs[name] if stored.get(k) != orgs[name][k]]
        if moved:
            messages.append(
                f"organizations/{name}.yaml: its disclosure rating is out of date ({', '.join(moved)}); {RUN}"
            )
    for name in sorted(routes):
        stored, computed = data["routes"][name].get("disclosure_rating"), routes[name]["disclosure_rating"]
        if stored is None:
            messages.append(f"routes/{name}.yaml: is missing the disclosure_rating field; {RUN}")
            continue
        moved = [k for k in DISCLOSURE_KEYS if stored.get(k) != computed[k]]
        if moved:
            messages.append(f"routes/{name}.yaml: its disclosure rating is out of date ({', '.join(moved)}); {RUN}")
    return ScoreRun(messages, [])
