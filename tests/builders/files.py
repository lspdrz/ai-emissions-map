"""Write records to a temporary root's sources/, for the tests that read files from disk."""

from pathlib import Path

import yaml

from build.schemas.sources import Sources


def write_source(root: Path, path: str, text: str = "") -> None:
    file = root / "sources" / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)


def write_corpus(root: Path, corpus: Sources) -> None:
    for dirname in ("organizations", "grids", "routes", "models"):
        for name, record in corpus[dirname].items():
            write_source(root, f"{dirname}/{name}.yaml", yaml.safe_dump(dict(record), sort_keys=False))


def write_grid_intensities(root: Path, intensities: dict[str, dict[int, float]]) -> None:
    """Write sources/snapshots/grid_intensity.csv: each geography's Ember intensity per year, in gCO2e/kWh."""
    rows = [f"{geo},{geo},{year},{value}" for geo, by_year in intensities.items() for year, value in by_year.items()]
    write_source(root, "snapshots/grid_intensity.csv", "\n".join(["geography,name,year,intensity", *rows]) + "\n")
