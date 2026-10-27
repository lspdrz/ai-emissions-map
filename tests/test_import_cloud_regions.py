import json
from datetime import date

from build.import_cloud_regions import import_cloud_regions, region_rows

# The Green Software Foundation's Cloud_Region_Metadata.csv, cut down to the columns import_cloud_regions reads. Each
# test writes its own; a row that stops before power-usage-effectiveness has none.
HEADER = "year,cloud-provider,cloud-region,em-zone-id,location,power-usage-effectiveness"
COMMIT = "8f99b3bc01ecb342905b80a485573fda9494a052"


def _write(path, rows):
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def test_each_region_keeps_its_zones_in_its_latest_year_with_one(tmp_path):
    metadata = _write(
        tmp_path / "metadata.csv",
        [
            "2024,Microsoft Azure,northeurope,,Ireland",  # no zone in the latest year
            "2023,Microsoft Azure,northeurope,IE,Ireland",
            "2023,Microsoft Azure,northeurope,FI,Finland",
            "2022,Microsoft Azure,northeurope,SE,Sweden",  # an earlier year
            "2024,Amazon Web Services,eu-central-1,DE,Europe (Frankfurt)",
        ],
    )
    assert region_rows(metadata) == (
        [
            {
                "vendor": "aws",
                "region": "eu-central-1",
                "zone": "DE",
                "year": "2024",
                "location": "Europe (Frankfurt)",
                "pue": "",
                "pue_year": "",
            },
            {
                "vendor": "azure",
                "region": "northeurope",
                "zone": "FI",
                "year": "2023",
                "location": "Finland",
                "pue": "",
                "pue_year": "",
            },
            {
                "vendor": "azure",
                "region": "northeurope",
                "zone": "IE",
                "year": "2023",
                "location": "Ireland",
                "pue": "",
                "pue_year": "",
            },
        ],
        [],
    )


def test_rows_are_sorted_by_the_providers_full_name(tmp_path):
    metadata = _write(
        tmp_path / "metadata.csv",
        ["2023,Microsoft Azure,westeurope,NL,Netherlands", "2024,Google Cloud,europe-west4,NL,Netherlands"],
    )
    assert [row["vendor"] for row in region_rows(metadata)[0]] == ["gcp", "azure"]


def test_each_region_keeps_its_pue_from_its_latest_year_with_one(tmp_path):
    metadata = _write(
        tmp_path / "metadata.csv",
        [
            "2024,Google Cloud,europe-west4,NL,Netherlands,",  # no PUE in the latest year
            "2023,Google Cloud,europe-west4,NL,Netherlands,1.08",
            "2022,Google Cloud,europe-west4,NL,Netherlands,1.09",  # an earlier year
        ],
    )
    [row] = region_rows(metadata)[0]
    assert (row["year"], row["pue"], row["pue_year"]) == ("2024", "1.08", "2023")


def test_a_region_with_no_pue_in_any_year_has_none(tmp_path):
    metadata = _write(tmp_path / "metadata.csv", ["2024,Google Cloud,europe-west3,DE,Germany,"])
    [row] = region_rows(metadata)[0]
    assert (row["pue"], row["pue_year"]) == ("", "")


def test_every_zone_of_a_region_has_the_regions_pue(tmp_path):
    metadata = _write(
        tmp_path / "metadata.csv",
        ["2023,Microsoft Azure,northeurope,IE,Ireland,1.19", "2023,Microsoft Azure,northeurope,FI,Finland,1.19"],
    )
    assert [(row["zone"], row["pue"]) for row in region_rows(metadata)[0]] == [("FI", "1.19"), ("IE", "1.19")]


def test_a_region_without_a_zone_and_another_provider_are_skipped_with_their_reasons(tmp_path):
    metadata = _write(
        tmp_path / "metadata.csv",
        ["2024,Amazon Web Services,ca-west-1,,Canada West (Calgary)", "2024,Oracle Cloud,eu-frankfurt-1,DE,Frankfurt"],
    )
    assert region_rows(metadata) == (
        [],
        [
            {"vendor": "Amazon Web Services", "region": "ca-west-1", "reason": "no em-zone-id in any year"},
            {"vendor": "Oracle Cloud", "region": "eu-frankfurt-1", "reason": "provider not kept"},
        ],
    )


def test_import_writes_the_table_its_provenance_and_a_copy_of_the_download(tmp_path):
    metadata = _write(tmp_path / "metadata.csv", ["2024,Amazon Web Services,eu-central-1,DE,Europe (Frankfurt)"])
    run = import_cloud_regions(tmp_path, metadata, COMMIT, date(2026, 10, 21))
    snapshots = tmp_path / "sources" / "snapshots"
    assert run.errors == [] and len(run.written) == 3
    assert (snapshots / "cloud_regions.csv").read_text() == (
        "vendor,region,zone,year,location,pue,pue_year\naws,eu-central-1,DE,2024,Europe (Frankfurt),,\n"
    )
    assert (snapshots / "files" / "gsf_files" / "Cloud_Region_Metadata.csv").read_bytes() == metadata.read_bytes()
    provenance = json.loads((snapshots / "cloud_regions.provenance.json").read_text())
    assert (provenance["commit"], provenance["url"], provenance["copy"], provenance["retrieved"]) == (
        COMMIT,
        f"https://raw.githubusercontent.com/Green-Software-Foundation/real-time-cloud/{COMMIT}/Cloud_Region_Metadata.csv",
        "sources/snapshots/files/gsf_files/Cloud_Region_Metadata.csv",
        "2026-10-21",
    )
    assert len(provenance["sha256"]) == 64


def test_a_second_import_of_the_same_file_writes_nothing(tmp_path):
    metadata = _write(tmp_path / "metadata.csv", ["2024,Amazon Web Services,eu-central-1,DE,Europe (Frankfurt)"])
    import_cloud_regions(tmp_path, metadata, COMMIT, date(2026, 10, 21))
    assert import_cloud_regions(tmp_path, metadata, COMMIT, date(2026, 10, 21)).written == []


def test_a_new_download_replaces_the_kept_copy(tmp_path):
    metadata = _write(tmp_path / "metadata.csv", ["2024,Amazon Web Services,eu-central-1,DE,Europe (Frankfurt)"])
    import_cloud_regions(tmp_path, metadata, COMMIT, date(2026, 10, 21))
    _write(metadata, ["2025,Amazon Web Services,eu-central-1,DE,Europe (Frankfurt)"])
    run = import_cloud_regions(tmp_path, metadata, "0" * 40, date(2026, 11, 4))
    kept = tmp_path / "sources" / "snapshots" / "files" / "gsf_files" / "Cloud_Region_Metadata.csv"
    assert kept in run.written and kept.read_bytes() == metadata.read_bytes()


def test_a_branch_instead_of_a_commit_is_refused_and_nothing_is_written(tmp_path):
    metadata = _write(tmp_path / "metadata.csv", [])
    run = import_cloud_regions(tmp_path, metadata, "main", date(2026, 10, 21))
    assert run.written == [] and run.errors == [
        "'main': not a commit; pin the file at a full 40-character commit hash, never a branch"
    ]
    assert not (tmp_path / "sources").exists()


def test_a_missing_download_is_reported_and_nothing_is_written(tmp_path):
    run = import_cloud_regions(tmp_path, tmp_path / "missing.csv", COMMIT, date(2026, 10, 21))
    assert run.written == [] and run.errors[0].endswith(
        "no such file; download it from the URL in sources/snapshots/README.md"
    )
    assert not (tmp_path / "sources").exists()
