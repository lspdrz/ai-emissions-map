"""Vercel deploys the website only when something under web/ changed since the last deployed commit."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "web" / "scripts" / "ignore-build.sh"
BUILD, SKIP = 1, 0


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.org")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "page.txt").write_text("v1")
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "x.yaml").write_text("v1")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "first")
    return tmp_path


def commit(repo, path, text):
    (repo / path).write_text(text)
    git(repo, "commit", "-q", "-am", f"change {path}")


def decide(repo, previous):
    env = {**os.environ, "VERCEL_GIT_PREVIOUS_SHA": previous}
    return subprocess.run(["sh", str(SCRIPT)], cwd=repo / "web", env=env).returncode


def test_first_deploy_builds(repo):
    assert decide(repo, "") == BUILD


def test_changes_outside_web_are_skipped(repo):
    previous = git(repo, "rev-parse", "HEAD")
    commit(repo, "sources/x.yaml", "v2")
    assert decide(repo, previous) == SKIP


def test_a_change_in_web_builds_even_under_later_commits(repo):
    previous = git(repo, "rev-parse", "HEAD")
    commit(repo, "web/page.txt", "v2")
    commit(repo, "sources/x.yaml", "v2")   # the last commit alone touches nothing in web/
    assert decide(repo, previous) == BUILD


def test_unknown_previous_commit_builds(repo):
    assert decide(repo, "0" * 40) == BUILD
