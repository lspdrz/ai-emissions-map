import json
from datetime import date

import yaml

import build.release as release_module
from build.release import inputs_sha, release
from tests.builders.corpus import make_corpus
from tests.builders.files import write_corpus, write_source
from tests.builders.grid import make_grid, make_grid_intensity
from tests.builders.location import make_location
from tests.builders.model import make_model
from tests.builders.organization import make_organization
from tests.builders.route import make_route


# Every test writes its records with the fields `python -m build score` stores, by hand: the release computes nothing.


def test_a_release_writes_the_data_file(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    assert release(tmp_path, date(2026, 10, 15)) == ([], [tmp_path / "web" / "data" / "data.json"])


def test_a_release_copies_each_routes_stored_fields(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    [route] = json.loads((tmp_path / "web" / "data" / "data.json").read_text())["routes"]
    assert (route["letter"], route["score"], route["band"]) == ("B", {"low": 0.065, "high": 0.078}, [2, 2])


def test_with_no_previous_data_file_the_release_date_is_the_run_date(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    assert json.loads((tmp_path / "web" / "data" / "data.json").read_text())["meta"]["release_date"] == "2026-10-15"


def test_a_release_records_the_hash_of_its_inputs(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    data = json.loads((tmp_path / "web" / "data" / "data.json").read_text())
    assert data["meta"]["inputs_sha"] == inputs_sha(tmp_path)


def test_a_route_without_stored_fields_says_to_run_score(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(name="acme-m-70b", org="acme", model="m-70b", location=make_location(candidates=["grid:ch"]))
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    assert release(tmp_path, date(2026, 10, 15)) == (
        [
            "routes/acme-m-70b.yaml: is missing the disclosure_rating field; run `python -m build score`",
            "routes/acme-m-70b.yaml: is missing the carbon_score field; run `python -m build score`",
        ],
        [],
    )
    assert not (tmp_path / "web" / "data" / "data.json").exists()


def test_invalid_sources_write_nothing(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    route = tmp_path / "sources" / "routes" / "acme-m-70b.yaml"
    route.write_text(route.read_text().split("carbon_score:")[0] + "carbon_score: 3\n")
    assert release(tmp_path, date(2026, 10, 15)) == (
        ["routes/acme-m-70b.yaml: carbon_score: Input should be a valid dictionary"],
        [],
    )
    assert not (tmp_path / "web" / "data" / "data.json").exists()


def test_a_rerun_on_unchanged_inputs_writes_nothing(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    assert release(tmp_path, date(2026, 10, 20)) == ([], [])


def test_a_change_the_site_does_not_show_keeps_the_release_date(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    route = tmp_path / "sources" / "routes" / "acme-m-70b.yaml"
    # A YAML comment: the file's bytes change, so the inputs hash moves, but the record it holds, and so everything
    # the site shows, stays the same.
    route.write_text("# a comment\n" + route.read_text())
    release(tmp_path, date(2026, 10, 20))
    assert json.loads((tmp_path / "web" / "data" / "data.json").read_text())["meta"]["release_date"] == "2026-10-15"


def test_a_change_the_site_does_not_show_updates_the_hash(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    route = tmp_path / "sources" / "routes" / "acme-m-70b.yaml"
    # A YAML comment: the file's bytes change, so the inputs hash moves, but the record it holds, and so everything
    # the site shows, stays the same.
    route.write_text("# a comment\n" + route.read_text())
    assert release(tmp_path, date(2026, 10, 20)) == ([], [tmp_path / "web" / "data" / "data.json"])
    data = json.loads((tmp_path / "web" / "data" / "data.json").read_text())
    assert data["meta"]["inputs_sha"] == inputs_sha(tmp_path)


def test_a_change_the_site_shows_moves_the_release_date(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    assert json.loads((tmp_path / "web" / "data" / "data.json").read_text())["meta"]["release_date"] == "2026-10-15"
    idle = make_organization(
        name="idle", disclosure_rating={"letter": None, "mean": None, "spread": {}, "summary": "Not rated (no routes)"}
    )
    write_source(tmp_path, "organizations/idle.yaml", yaml.safe_dump(dict(idle), sort_keys=False))
    release(tmp_path, date(2026, 10, 20))
    assert json.loads((tmp_path / "web" / "data" / "data.json").read_text())["meta"]["release_date"] == "2026-10-20"


def test_a_conflicted_data_file_is_rebuilt_with_the_run_date(tmp_path):
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    release(tmp_path, date(2026, 10, 15))
    data_file = tmp_path / "web" / "data" / "data.json"
    data_file.write_text("<<<<<<< HEAD\n" + data_file.read_text() + "=======\n{}\n>>>>>>> other\n")
    assert release(tmp_path, date(2026, 10, 20)) == ([], [data_file])
    assert json.loads(data_file.read_text())["meta"]["release_date"] == "2026-10-20"


def test_it_refuses_to_write_outside_the_contract(tmp_path, monkeypatch):
    real_build_data = release_module.build_data
    monkeypatch.setattr(
        "build.release.build_data", lambda *args: {**real_build_data(*args), "unknown_field": {"CH": 30}}
    )
    corpus = make_corpus(
        organizations=[
            make_organization(
                name="acme",
                disclosure_rating={"letter": "B", "mean": 2.0, "spread": {"B": 1}, "summary": "B (1 route at B)"},
            )
        ],
        grids=[make_grid(name="ch", country="CH", zone="CH", intensity=make_grid_intensity())],
        routes=[
            make_route(
                name="acme-m-70b",
                org="acme",
                model="m-70b",
                location=make_location(candidates=["grid:ch"]),
                disclosure_rating={"letter": "B", "gap": "The grid is disclosed, not the facility."},
                carbon_score={
                    "grids": ["ch"],
                    "energy_wh": {"low": 0.5, "high": 0.6},
                    "embodied_g": {"low": 0.05, "high": 0.06},
                    "intensity_g_per_kwh": {"low": 30.0, "high": 30.0},
                    "score_g": {"low": 0.065, "high": 0.078},
                    "band": [2, 2],
                },
            )
        ],
        models=[make_model(name="m-70b")],
    )
    write_corpus(tmp_path, corpus)
    assert release(tmp_path, date(2026, 10, 15)) == (
        ["the data file would leave its contract: top level: field 'unknown_field' is not in the contract"],
        [],
    )


# inputs_sha: the hash of everything a published value depends on, the records and build/'s code. Every test writes
# the files it hashes.


def test_the_hash_depends_on_the_files_not_on_where_the_repository_is(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    write_source(first, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    write_source(first, "grids/ch.yaml", "name: ch\n")
    write_source(second, "grids/ch.yaml", "name: ch\n")  # the same files, written in the other order
    write_source(second, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    assert inputs_sha(first) == inputs_sha(second)


def test_editing_a_record_moves_the_hash(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\norg: acme\n")
    assert inputs_sha(tmp_path) != before


def test_editing_builds_code_moves_the_hash(tmp_path):
    (tmp_path / "build" / "schemas").mkdir(parents=True)
    (tmp_path / "build" / "schemas" / "route.py").write_text("X = 1\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "build" / "schemas" / "route.py").write_text("X = 2\n")
    assert inputs_sha(tmp_path) != before


def test_adding_a_record_moves_the_hash(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "models/m-70b.yaml", "name: m-70b\n")
    assert inputs_sha(tmp_path) != before


def test_deleting_a_record_moves_the_hash(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    write_source(tmp_path, "models/m-70b.yaml", "name: m-70b\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "sources" / "models" / "m-70b.yaml").unlink()
    assert inputs_sha(tmp_path) != before


def test_renaming_a_record_moves_the_hash(tmp_path):
    write_source(tmp_path, "models/m-70b.yaml", "name: m-70b\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "sources" / "models" / "m-70b.yaml").rename(tmp_path / "sources" / "models" / "m-8b.yaml")
    assert inputs_sha(tmp_path) != before


def test_the_ecologits_version_moves_the_hash(tmp_path, monkeypatch):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    monkeypatch.setattr("build.release.version", lambda package: "0.11.2")
    before = inputs_sha(tmp_path)
    monkeypatch.setattr("build.release.version", lambda package: "99.0.0")
    assert inputs_sha(tmp_path) != before


def test_the_cloud_region_table_leaves_the_hash_alone(tmp_path):
    # The release reads the stored scores, not the table they were computed from.
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "snapshots/cloud_regions.csv", "vendor,region,zone\ncloudx,eu-de,DE\n")
    assert inputs_sha(tmp_path) == before


def test_a_file_in_a_records_folder_that_is_not_a_yaml_record_leaves_the_hash_alone(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "routes/acme-m-8b.yml", "name: acme-m-8b\n")  # never loaded, so never published
    assert inputs_sha(tmp_path) == before


def test_a_readme_in_sources_leaves_the_hash_alone(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "snapshots/README.md", "notes\n")
    assert inputs_sha(tmp_path) == before


def test_a_hidden_yaml_file_leaves_the_hash_alone(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    write_source(tmp_path, "routes/.acme-m-8b.yaml", "name: acme-m-8b\n")  # an editor's backup, say
    assert inputs_sha(tmp_path) == before


def test_a_file_outside_sources_and_build_leaves_the_hash_alone(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "notes.txt").write_text("draft\n")
    assert inputs_sha(tmp_path) == before


def test_compiled_python_leaves_the_hash_alone(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "score.py").write_text("X = 1\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "build" / "__pycache__").mkdir()
    (tmp_path / "build" / "__pycache__" / "score.cpython-312.pyc").write_bytes(b"\0")
    assert inputs_sha(tmp_path) == before


def test_line_endings_do_not_move_the_hash(tmp_path):
    # A Windows editor may save CRLF; the hash reads it as LF, so it matches CI.
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    before = inputs_sha(tmp_path)
    (tmp_path / "sources" / "routes" / "acme-m-70b.yaml").write_bytes(b"name: acme-m-70b\r\n")
    assert inputs_sha(tmp_path) == before
