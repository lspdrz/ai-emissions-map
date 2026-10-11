"""Committed documentation stays consistent with the code and with itself.

Documents are read by people and agents who act on them, so a broken link, a rule stated with an old
number, or a workflow nobody can find is a defect like any other.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from build.config import CARBON_BAND_UPPER, PUE, VERIFICATION_WINDOW

REPO = Path(__file__).resolve().parents[1]
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def committed_markdown() -> list[Path]:
    """Every Markdown file that ships in the repository (never .notes/, .venv/ or test fixtures)."""
    files = list(REPO.glob("*.md"))
    for directory in ("docs", "skills", ".github", "sources"):
        if (REPO / directory).exists():
            files += (REPO / directory).rglob("*.md")
    return sorted(files)


def links(path: Path) -> list[str]:
    """Relative link targets in a Markdown file, anchors stripped; web, mail and same-page links skipped."""
    targets = []
    for target in _LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        targets.append(target.split("#", 1)[0])
    return targets


def test_relative_links_resolve():
    broken = [f"{p.relative_to(REPO)} -> {t}" for p in committed_markdown() for t in links(p)
              if not (p.parent / t).exists()]
    assert not broken, f"links to files that do not exist: {broken}"


def test_no_link_points_into_notes():
    # .notes/ is gitignored: a link into it resolves on the maintainer's machine and nowhere else.
    bad = [f"{p.relative_to(REPO)} -> {t}" for p in committed_markdown() for t in links(p) if ".notes" in t]
    assert not bad, f"links into the gitignored .notes/: {bad}"


def test_methodology_states_the_configured_constants():
    text = (REPO / "docs" / "methodology.md").read_text(encoding="utf-8")
    low, high = PUE
    assert f"{low:g}–{high:g}" in text, "methodology PUE range differs from build/config.py PUE"
    assert f"within {VERIFICATION_WINDOW} days" in text, "methodology window differs from VERIFICATION_WINDOW"
    e = [f"{u:g}" for u in CARBON_BAND_UPPER]
    bands = (f"1 below {e[0]}, 2 from {e[0]} to below {e[1]}, 3 from {e[1]} to below {e[2]}, "
             f"4 from {e[2]} to below {e[3]}, and 5 at {e[3]} or above")
    assert bands in text, "methodology band edges differ from CARBON_BAND_UPPER"


REFERENCE_DOCS = ("identity", "evidence-and-freshness", "location-disclosure", "disclosure-formats")


def test_reference_docs_exist():
    missing = [d for d in REFERENCE_DOCS if not (REPO / "docs" / "reference" / f"{d}.md").exists()]
    assert not missing, f"missing reference docs: {missing}"


def test_freshness_rule_states_the_configured_window():
    text = (REPO / "docs" / "reference" / "evidence-and-freshness.md").read_text(encoding="utf-8")
    assert f"within the {VERIFICATION_WINDOW} days" in text


FIRST_WORKFLOWS = ("add-organization", "add-facility", "add-model", "add-route", "refresh-organization")
WORKFLOW_SECTIONS = ("## Use this when", "## Inputs you need", "## Files this changes", "## Procedure",
                     "## Validation", "## Expected PR contents", "## Stop and escalate when",
                     "## Relevant reference material")


def workflow_files() -> list[Path]:
    return sorted((REPO / "docs" / "workflows").glob("*.md"))


def test_the_first_workflows_exist():
    assert {p.stem for p in workflow_files()} >= set(FIRST_WORKFLOWS)


def test_every_workflow_follows_the_template():
    for p in workflow_files():
        text = p.read_text(encoding="utf-8")
        positions = [text.find(h) for h in WORKFLOW_SECTIONS]
        missing = [h for h, pos in zip(WORKFLOW_SECTIONS, positions) if pos == -1]
        assert not missing, f"{p.name} lacks {missing}"
        assert positions == sorted(positions), f"{p.name}: template sections out of order"


def test_validation_sections_run_real_modules():
    for p in workflow_files():
        section = p.read_text(encoding="utf-8").split("## Validation", 1)[1].split("\n## ", 1)[0]
        assert "python -m build.validate" in section, f"{p.name}: Validation does not run build.validate"
        for module in re.findall(r"python -m build\.(\w+)", section):
            assert (REPO / "build" / f"{module}.py").exists(), f"{p.name}: no build/{module}.py"


def test_docs_readme_routes_every_workflow_and_reference_doc():
    readme = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
    missing = [p.name for p in workflow_files() if f"(workflows/{p.name})" not in readme]
    missing += [f"{d}.md" for d in REFERENCE_DOCS if f"(reference/{d}.md)" not in readme]
    assert "(methodology.md)" in readme, "docs/README.md does not route to the methodology"
    assert not missing, f"docs/README.md does not route to: {missing}"


def _registry() -> dict:
    return yaml.safe_load((REPO / "skills" / "registry.yaml").read_text(encoding="utf-8"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_registry_lists_every_skill_exactly_once():
    listed = [e["skill"] for e in _registry()["primary"]]
    on_disk = sorted(p.name for p in (REPO / "skills").iterdir() if p.is_dir())
    assert sorted(listed) == on_disk, f"registry {sorted(listed)} vs skills/ {on_disk}"
    assert len(listed) == len(set(listed)), "a skill is registered twice"


def test_primary_skills_map_one_to_one_to_workflows():
    claimed = [e["workflow"] for e in _registry()["primary"]]
    assert len(claimed) == len(set(claimed)), "two skills claim one workflow"
    workflows = sorted(str(p.relative_to(REPO)) for p in workflow_files())
    assert sorted(claimed) == workflows, "every workflow needs exactly one skill, and every skill one workflow"


def test_every_skill_names_itself_and_reads_its_workflow():
    for entry in _registry()["primary"]:
        path = REPO / "skills" / entry["skill"] / "SKILL.md"
        meta = _frontmatter(path)
        assert meta["name"] == entry["skill"], f"{path}: name is {meta['name']!r}"
        assert meta.get("description", "").startswith("Use when"), f"{path}: description must start 'Use when'"
        assert entry["workflow"] in path.read_text(encoding="utf-8"), f"{path} never points at {entry['workflow']}"


def test_skills_are_delivered_to_the_harness():
    for entry in _registry()["primary"]:
        link = REPO / ".claude" / "skills" / entry["skill"]
        assert link.is_symlink(), f"{link} is not a symlink"
        assert link.resolve() == (REPO / "skills" / entry["skill"]).resolve()


def test_docs_readme_names_every_skill():
    readme = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
    missing = [e["skill"] for e in _registry()["primary"] if f"`{e['skill']}`" not in readme]
    assert not missing, f"docs/README.md does not name: {missing}"


def test_agent_entry_points_exist():
    for name in ("CLAUDE.md", "AGENTS.md"):
        assert (REPO / name).exists(), f"{name} is missing"


def test_agents_md_names_every_build_module():
    text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    modules = sorted(p.stem for p in (REPO / "build").glob("*.py") if p.stem != "__init__")
    missing = [m for m in modules if f"`{m}`" not in text]
    assert not missing, f"AGENTS.md does not mention build modules: {missing}"
