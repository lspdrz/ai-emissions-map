from build.load_sources import load_cloud_regions, load_grid_intensities, load_sources
from tests.builders.files import write_source

# Every test writes the files it reads into tmp_path: reading them from disk is what this module does.


# load_sources: every record in the four records folders, and anything there that is not a record.


def test_every_yaml_file_in_a_records_folder_is_a_record_keyed_by_its_filename_stem(tmp_path):
    write_source(tmp_path, "organizations/acme.yaml", "name: acme\ndisplay_name: Acme\n")
    write_source(tmp_path, "grids/ch.yaml", "name: ch\n")
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\norg: acme\n")
    write_source(tmp_path, "models/m-70b.yaml", "name: m-70b\n")
    assert load_sources(tmp_path) == {
        "organizations": {"acme": {"name": "acme", "display_name": "Acme"}},
        "grids": {"ch": {"name": "ch"}},
        "routes": {"acme-m-70b": {"name": "acme-m-70b", "org": "acme"}},
        "models": {"m-70b": {"name": "m-70b"}},
        "stray_files": [],
    }


def test_a_yml_file_is_not_a_record_but_a_stray_file(tmp_path):
    write_source(tmp_path, "routes/acme-m-8b.yml", "name: acme-m-8b\n")
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": ["routes/acme-m-8b.yml"],
    }


def test_a_subfolder_is_a_stray_file(tmp_path):
    (tmp_path / "sources" / "routes" / "old-layout").mkdir(parents=True)
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": ["routes/old-layout"],
    }


def test_a_subfolder_named_like_a_record_is_a_stray_file(tmp_path):
    (tmp_path / "sources" / "routes" / "acme-m-70b.yaml").mkdir(parents=True)
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": ["routes/acme-m-70b.yaml"],
    }


def test_stray_files_are_listed_in_order(tmp_path):
    write_source(tmp_path, "routes/zeta-m-70b.yml", "name: zeta-m-70b\n")
    write_source(tmp_path, "routes/acme-m-70b.yml", "name: acme-m-70b\n")
    assert load_sources(tmp_path)["stray_files"] == ["routes/acme-m-70b.yml", "routes/zeta-m-70b.yml"]


def test_a_dotfile_is_neither_a_record_nor_a_stray_file(tmp_path):
    write_source(tmp_path, "routes/.DS_Store", "x")
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": [],
    }


def test_a_hidden_yaml_file_is_neither_a_record_nor_a_stray_file(tmp_path):
    write_source(tmp_path, "routes/.acme-m-70b.yaml", "name: acme-m-70b\n")  # an editor's backup, say
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": [],
    }


def test_a_missing_records_folder_loads_as_empty(tmp_path):
    write_source(tmp_path, "routes/acme-m-70b.yaml", "name: acme-m-70b\n")
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {"acme-m-70b": {"name": "acme-m-70b"}},
        "models": {},
        "stray_files": [],
    }


def test_files_outside_the_records_folders_are_not_read(tmp_path):
    write_source(tmp_path, "snapshots/notes.yaml", "name: notes\n")
    assert load_sources(tmp_path) == {
        "organizations": {},
        "grids": {},
        "routes": {},
        "models": {},
        "stray_files": [],
    }


# load_cloud_regions: the cloud-region table, each (vendor, region) to its zones and its PUE.


def test_each_region_maps_to_its_zone(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    path.write_text("vendor,region,zone\ncloudx,eu-de,DE\ncloudx,eu-fr,FR\n")
    assert load_cloud_regions(path) == {
        ("cloudx", "eu-de"): {"zones": ["DE"], "pue": None},
        ("cloudx", "eu-fr"): {"zones": ["FR"], "pue": None},
    }


def test_a_region_on_several_rows_maps_to_each_of_their_zones(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    path.write_text("vendor,region,zone\nazure,northeurope,FI\nazure,northeurope,IE\n")
    assert load_cloud_regions(path) == {("azure", "northeurope"): {"zones": ["FI", "IE"], "pue": None}}


def test_a_regions_zones_are_sorted(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    rows = "".join(f"cloudx,eu,{zone}\n" for zone in ("SE", "PL", "NL", "IE", "FI", "DE"))  # six, so no order is luck
    path.write_text("vendor,region,zone\n" + rows)
    assert load_cloud_regions(path) == {("cloudx", "eu"): {"zones": ["DE", "FI", "IE", "NL", "PL", "SE"], "pue": None}}


def test_a_repeated_row_counts_once(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    path.write_text("vendor,region,zone\ncloudx,eu-de,DE\ncloudx,eu-de,DE\n")
    assert load_cloud_regions(path) == {("cloudx", "eu-de"): {"zones": ["DE"], "pue": None}}


def test_a_regions_pue_is_read_with_its_zones(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    path.write_text(
        "vendor,region,zone,year,location,pue,pue_year\n"
        "gcp,europe-west4,NL,2024,Netherlands,1.08,2024\n"
        "gcp,europe-west3,DE,2024,Germany,,\n"
    )
    assert load_cloud_regions(path) == {
        ("gcp", "europe-west3"): {"zones": ["DE"], "pue": None},
        ("gcp", "europe-west4"): {"zones": ["NL"], "pue": 1.08},
    }


def test_a_region_on_several_rows_has_one_pue(tmp_path):
    path = tmp_path / "cloud_regions.csv"
    path.write_text(
        "vendor,region,zone,year,location,pue,pue_year\n"
        "azure,northeurope,FI,2023,Finland,1.19,2023\n"
        "azure,northeurope,IE,2023,Ireland,1.19,2023\n"
    )
    assert load_cloud_regions(path) == {("azure", "northeurope"): {"zones": ["FI", "IE"], "pue": 1.19}}


# load_grid_intensities: Ember's table, each geography to its intensity per year.


def test_grid_intensities_are_read_per_geography_and_year(tmp_path):
    path = tmp_path / "grid_intensity.csv"
    path.write_text(
        "geography,name,year,intensity\nCH,Switzerland,2024,34.648\nCH,Switzerland,2025,39.278\nUS-VA,Virginia,2025,356.592\n"
    )
    assert load_grid_intensities(path) == {"CH": {2024: 34.648, 2025: 39.278}, "US-VA": {2025: 356.592}}
