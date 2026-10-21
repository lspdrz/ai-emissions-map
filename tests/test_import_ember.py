import json
from datetime import date

from build.import_ember import import_ember, intensity_rows

# Ember's three yearly releases, cut down to the columns import_ember reads. Each test writes its own.
GLOBAL_HEADER = "Area,ISO 3 code,Year,Area type,Electricity source,Emissions intensity (gCO2e/kWh)"
US_HEADER = "Area,ISO 3 code,State,State code,Year,Electricity source,Emissions intensity (gCO2e/kWh)"
CHINA_HEADER = "Area,ISO 3 code,Province,Province code,Year,Electricity source,Emissions intensity (gCO2e/kWh)"


def _write(path, header, rows):
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def test_rows_keep_the_total_generation_intensity_of_countries_and_subdivisions_for_the_year(tmp_path):
    global_csv = _write(
        tmp_path / "global.csv",
        GLOBAL_HEADER,
        [
            "Switzerland,CHE,2025,Country or economy,Total generation,39.278",
            "Switzerland,CHE,2025,Country or economy,Hydro,24.0",  # one source, not the total
            "Europe,,2025,Region,Total generation,250.0",  # a region, not a country
            "Switzerland,CHE,2024,Country or economy,Total generation,34.648",
        ],
    )
    us_csv = _write(
        tmp_path / "us.csv",
        US_HEADER,
        [
            "United States,USA,Virginia,VA,2025,Total generation,356.592",
            "United States,USA,Virginia,VA,2025,Coal,820.0",
        ],
    )
    china_csv = _write(tmp_path / "china.csv", CHINA_HEADER, ["China,CHN,Sichuan,SC,2025,Total generation,178.0"])
    rows, skipped = intensity_rows(global_csv, {"US": us_csv, "CN": china_csv}, 2025)
    assert rows == [
        {"geography": "CH", "name": "Switzerland", "year": "2025", "intensity": "39.278"},
        {"geography": "CN-SC", "name": "Sichuan", "year": "2025", "intensity": "178.0"},
        {"geography": "US-VA", "name": "Virginia", "year": "2025", "intensity": "356.592"},
    ]
    assert skipped == []


def test_a_geography_without_the_year_keeps_its_latest_earlier_year_never_a_later_one(tmp_path):
    global_csv = _write(
        tmp_path / "global.csv",
        GLOBAL_HEADER,
        [
            "Switzerland,CHE,2022,Country or economy,Total generation,30.0",
            "Switzerland,CHE,2023,Country or economy,Total generation,32.0",
            "Switzerland,CHE,2026,Country or economy,Total generation,41.0",
            "France,FRA,2026,Country or economy,Total generation,40.0",  # only a later year
        ],
    )
    assert intensity_rows(global_csv, {}, 2025) == (
        [{"geography": "CH", "name": "Switzerland", "year": "2023", "intensity": "32.0"}],
        [{"area": "France", "code": "FR", "reason": "no year 2025 or earlier"}],
    )


def test_a_country_without_an_alpha_2_code_is_skipped_with_its_reason(tmp_path):
    global_csv = _write(
        tmp_path / "global.csv", GLOBAL_HEADER, ["Kosovo,XKX,2025,Country or economy,Total generation,900.0"]
    )
    assert intensity_rows(global_csv, {}, 2025) == (
        [],
        [{"area": "Kosovo", "code": "XKX", "reason": "no ISO 3166-1 alpha-2 code"}],
    )


def test_a_subnational_releases_national_total_is_skipped_not_kept_as_a_subdivision(tmp_path):
    # Ember's subnational files carry a national total row (US, China); it is not an ISO 3166-2 subdivision.
    global_csv = _write(tmp_path / "global.csv", GLOBAL_HEADER, [])
    us_csv = _write(tmp_path / "us.csv", US_HEADER, ["United States,USA,US (total),US,2025,Total generation,384.4"])
    china_csv = _write(tmp_path / "china.csv", CHINA_HEADER, ["China,CHN,China (total),CN,2025,Total generation,560.0"])
    assert intensity_rows(global_csv, {"US": us_csv, "CN": china_csv}, 2025) == (
        [],
        [
            {"area": "China (total)", "code": "CN-CN", "reason": "not an ISO 3166-2 subdivision"},
            {"area": "US (total)", "code": "US-US", "reason": "not an ISO 3166-2 subdivision"},
        ],
    )


def _downloads(tmp_path):
    global_csv = _write(
        tmp_path / "global.csv", GLOBAL_HEADER, ["Switzerland,CHE,2025,Country or economy,Total generation,39.278"]
    )
    us_csv = _write(tmp_path / "us.csv", US_HEADER, [])
    china_csv = _write(tmp_path / "china.csv", CHINA_HEADER, [])
    return global_csv, us_csv, china_csv


def test_import_writes_the_table_and_its_provenance(tmp_path):
    run = import_ember(tmp_path, *_downloads(tmp_path), date(2026, 10, 21))
    snapshots = tmp_path / "sources" / "snapshots"
    assert run.errors == [] and len(run.written) == 2
    assert (
        snapshots / "grid_intensity.csv"
    ).read_text() == "geography,name,year,intensity\nCH,Switzerland,2025,39.278\n"
    provenance = json.loads((snapshots / "grid_intensity.provenance.json").read_text())
    assert (provenance["licence"], provenance["retrieved"], provenance["year"], provenance["rows"]) == (
        "CC-BY-4.0; attribute Ember (ember-energy.org)",
        "2026-10-21",
        2025,
        1,
    )
    assert [len(f["sha256"]) for f in provenance["files"]] == [64, 64, 64]


def test_a_second_import_of_the_same_files_writes_nothing(tmp_path):
    downloads = _downloads(tmp_path)
    import_ember(tmp_path, *downloads, date(2026, 10, 21))
    assert import_ember(tmp_path, *downloads, date(2026, 10, 21)).written == []


def test_a_missing_download_is_reported_and_nothing_is_written(tmp_path):
    global_csv, us_csv, _ = _downloads(tmp_path)
    run = import_ember(tmp_path, global_csv, us_csv, tmp_path / "missing.csv", date(2026, 10, 21))
    assert run.written == [] and run.errors[0].endswith(
        "no such file; download it from the URL in sources/snapshots/README.md"
    )
    assert not (tmp_path / "sources").exists()


def test_an_import_rewrites_every_grids_intensity_from_the_new_table(tmp_path):
    (tmp_path / "sources" / "grids").mkdir(parents=True)
    grid = tmp_path / "sources" / "grids" / "ch.yaml"
    grid.write_text("name: ch\ndisplay_name: Switzerland\ncountry: CH\n")
    run = import_ember(tmp_path, *_downloads(tmp_path), date(2026, 10, 21))
    assert run.errors == [] and "ch.yaml" in [p.name for p in run.written]
    assert "  g_per_kwh: 39.278\n  year: 2025\n  geography: CH\n  source: Ember\n" in grid.read_text()
