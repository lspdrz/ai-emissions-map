"""Repository plumbing: CI runs the gates, issue forms are well formed, the code license is in place."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
GITHUB = REPO / ".github"


def test_ci_installs_validates_and_tests_without_a_browser():
    workflow = yaml.safe_load((GITHUB / "workflows" / "validate.yml").read_text(encoding="utf-8"))
    runs = "\n".join(step.get("run", "") for step in workflow["jobs"]["validate"]["steps"])
    assert "uv sync --locked" in runs
    assert "uv run python -m build.validate" in runs
    assert 'uv run pytest -q -m "not browser"' in runs


def test_issue_forms_are_well_formed():
    forms = sorted(p for p in (GITHUB / "ISSUE_TEMPLATE").glob("*.yml") if p.name != "config.yml")
    assert {p.stem for p in forms} == {"report-an-error", "suggest-a-provider", "provider-response"}
    for p in forms:
        form = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert form.get("name") and form.get("description") and form.get("labels"), f"{p.name}: header"
        ids = [item["id"] for item in form["body"] if "id" in item]
        assert ids and len(ids) == len(set(ids)), f"{p.name}: body ids missing or repeated"


def test_code_license_is_mit():
    assert (REPO / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_contributor_files_exist():
    for name in ("CONTRIBUTING.md", "CHANGELOG.md", ".github/pull_request_template.md"):
        assert (REPO / name).exists(), f"{name} is missing"


def test_web_ci_lints_tests_builds_and_checks():
    workflow = yaml.safe_load((GITHUB / "workflows" / "web.yml").read_text(encoding="utf-8"))
    runs = "\n".join(step.get("run", "") for step in workflow["jobs"]["web"]["steps"])
    for command in ("npm ci", "npm run lint", "npm test", "npm run build", "npm run check"):
        assert command in runs, f"web.yml does not run {command}"


def test_vercel_skips_builds_outside_web():
    config = json.loads((REPO / "web" / "vercel.json").read_text(encoding="utf-8"))
    assert config["ignoreCommand"] == "sh scripts/ignore-build.sh"
