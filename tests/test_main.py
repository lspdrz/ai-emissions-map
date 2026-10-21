from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from build.__main__ import main
from build.check_site_data import SiteDataCheck
from build.grid_emissions import GridRun
from build.import_ember import Import
from build.release import Release
from build.score import ScoreRun

# Each test replaces the command functions with fakes: what __main__ does is choose one, print its result and set the
# exit code.


def test_score_runs_score_on_the_root(monkeypatch):
    fake_score = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.__main__.score", fake_score)
    main(["score", "--root", "/repo"])
    fake_score.assert_called_once_with(Path("/repo"))


def test_release_runs_release_on_the_root_with_todays_date(monkeypatch):
    fake_release = Mock(return_value=Release([], []))
    monkeypatch.setattr("build.__main__.release", fake_release)
    monkeypatch.setattr("build.__main__.date", SimpleNamespace(today=lambda: date(2026, 10, 15)))
    main(["release", "--root", "/repo"])
    fake_release.assert_called_once_with(Path("/repo"), date(2026, 10, 15))


def test_check_carbon_scores_runs_its_gate_on_the_root(monkeypatch):
    fake_gate = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.__main__.check_carbon_scores", fake_gate)
    main(["check-carbon-scores", "--root", "/repo"])
    fake_gate.assert_called_once_with(Path("/repo"))


def test_check_disclosure_ratings_runs_its_gate_on_the_root(monkeypatch):
    fake_gate = Mock(return_value=ScoreRun([], []))
    monkeypatch.setattr("build.__main__.check_disclosure_ratings", fake_gate)
    main(["check-disclosure-ratings", "--root", "/repo"])
    fake_gate.assert_called_once_with(Path("/repo"))


def test_check_site_data_runs_its_gate_on_the_root(monkeypatch):
    fake_gate = Mock(return_value=SiteDataCheck([], []))
    monkeypatch.setattr("build.__main__.check_site_data", fake_gate)
    main(["check-site-data", "--root", "/repo"])
    fake_gate.assert_called_once_with(Path("/repo"))


@pytest.mark.parametrize(
    "command, target, result",
    [
        ("score", "build.__main__.score", ScoreRun),
        ("release", "build.__main__.release", Release),
        ("check-carbon-scores", "build.__main__.check_carbon_scores", ScoreRun),
        ("check-disclosure-ratings", "build.__main__.check_disclosure_ratings", ScoreRun),
        ("check-site-data", "build.__main__.check_site_data", SiteDataCheck),
    ],
)
def test_errors_are_printed_and_fail(monkeypatch, capsys, command, target, result):
    monkeypatch.setattr(target, lambda *args: result(["routes/x.yaml: broken", "grids/y.yaml: broken"], []))
    assert main([command, "--root", "/repo"]) == 1
    assert capsys.readouterr().out == "ERROR: routes/x.yaml: broken\nERROR: grids/y.yaml: broken\n2 error(s)\n"


def test_the_files_score_wrote_are_listed_relative_to_the_root(monkeypatch, capsys):
    written = [Path("/repo/sources/organizations/acme.yaml"), Path("/repo/sources/routes/acme-m-70b.yaml")]
    monkeypatch.setattr("build.__main__.score", lambda root: ScoreRun([], written))
    assert main(["score", "--root", "/repo"]) == 0
    assert capsys.readouterr().out == "wrote sources/organizations/acme.yaml\nwrote sources/routes/acme-m-70b.yaml\n"


@pytest.mark.parametrize(
    "command, target, result, done",
    [
        ("score", "build.__main__.score", ScoreRun, "nothing changed"),
        ("release", "build.__main__.release", Release, "nothing changed"),
        ("check-carbon-scores", "build.__main__.check_carbon_scores", ScoreRun, "0 error(s)"),
        ("check-disclosure-ratings", "build.__main__.check_disclosure_ratings", ScoreRun, "0 error(s)"),
        ("check-site-data", "build.__main__.check_site_data", SiteDataCheck, "0 error(s)"),
    ],
)
def test_a_command_with_nothing_to_report_says_so(monkeypatch, capsys, command, target, result, done):
    monkeypatch.setattr(target, lambda *args: result([], []))
    assert main([command, "--root", "/repo"]) == 0
    assert capsys.readouterr().out == done + "\n"


@pytest.mark.parametrize(
    "command, about",
    [
        ("score", "check sources/, write the disclosure_rating: and carbon_score: fields"),
        ("release", "validate sources/ and write web/data/data.json; computes nothing"),
        ("check-carbon-scores", "CI gate: every route's stored carbon score is what score would write now"),
        (
            "check-disclosure-ratings",
            "CI gate: every stored disclosure letter and rating is what score would write now",
        ),
        (
            "check-site-data",
            "CI gate: web/data/data.json is current with what it was built from and keeps to its contract",
        ),
    ],
)
def test_each_command_has_its_own_help(capsys, command, about):
    with pytest.raises(SystemExit):
        main([command, "--help"])
    out = capsys.readouterr().out
    assert out.splitlines()[0] == f"usage: python -m build {command} [-h]"
    assert about in " ".join(out.split())  # argparse may wrap the description


def test_import_ember_runs_on_the_root_with_its_three_downloads_and_todays_date(monkeypatch):
    fake_import = Mock(return_value=Import([], []))
    monkeypatch.setattr("build.__main__.import_ember", fake_import)
    monkeypatch.setattr("build.__main__.date", SimpleNamespace(today=lambda: date(2026, 10, 21)))
    argv = ["import-ember", "--root", "/repo", "--global-csv", "/g.csv", "--us-csv", "/u.csv", "--china-csv", "/c.csv"]
    assert main(argv) == 0
    fake_import.assert_called_once_with(
        Path("/repo"), Path("/g.csv"), Path("/u.csv"), Path("/c.csv"), date(2026, 10, 21)
    )


def test_import_ember_needs_all_three_downloads(capsys):
    with pytest.raises(SystemExit):
        main(["import-ember", "--global-csv", "/g.csv", "--us-csv", "/u.csv"])
    assert "--china-csv" in capsys.readouterr().err


def test_import_cloud_regions_runs_on_the_root_with_its_download_commit_and_todays_date(monkeypatch):
    fake_import = Mock(return_value=Import([], []))
    monkeypatch.setattr("build.__main__.import_cloud_regions", fake_import)
    monkeypatch.setattr("build.__main__.date", SimpleNamespace(today=lambda: date(2026, 10, 21)))
    assert main(["import-cloud-regions", "--root", "/repo", "--csv", "/m.csv", "--commit", "8f99b3bc"]) == 0
    fake_import.assert_called_once_with(Path("/repo"), Path("/m.csv"), "8f99b3bc", date(2026, 10, 21))


def test_import_cloud_regions_needs_the_commit(capsys):
    with pytest.raises(SystemExit):
        main(["import-cloud-regions", "--csv", "/m.csv"])
    assert "--commit" in capsys.readouterr().err


def test_grid_emissions_checks_by_default_and_writes_with_write(monkeypatch):
    fake = Mock(return_value=GridRun([], []))
    monkeypatch.setattr("build.__main__.grid_emissions", fake)
    assert main(["grid-emissions", "--root", "/repo"]) == 0
    assert main(["grid-emissions", "--root", "/repo", "--write", "ch", "de"]) == 0
    assert fake.call_args_list[0].args == (Path("/repo"), None) and fake.call_args_list[0].kwargs == {"write": False}
    assert fake.call_args_list[1].args == (Path("/repo"), ["ch", "de"]) and fake.call_args_list[1].kwargs == {
        "write": True
    }
