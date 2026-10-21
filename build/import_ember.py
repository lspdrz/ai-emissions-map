"""python -m build import-ember: Ember's yearly electricity data -> sources/snapshots/grid_intensity.csv.

Reads Ember's three yearly releases, downloaded by hand from the URLs below (sources/snapshots/README.md), keeps the
emissions intensity of total generation of each country, US state and Chinese province for GRID_YEAR (or its latest
earlier year), and writes the table every score's grid intensity comes from, with a .provenance.json beside it. Ember's
data is CC-BY-4.0.

    uv run python -m build import-ember --global-csv <global.csv> --us-csv <us.csv> --china-csv <china.csv>
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import NamedTuple

import pycountry

from build.constants.config import GRID_YEAR
from build.grid_emissions import grid_emissions
from build.load_sources import GRID_INTENSITY_FILE

GLOBAL_URL = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"
_SUBNATIONAL = "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/generation/outputs/"
US_URL = _SUBNATIONAL + "release_us_subnational_generation_yearly.csv"
CHINA_URL = _SUBNATIONAL + "release_chn_subnational_generation_yearly.csv"
# Each subnational release: its country, and the columns holding a subdivision's code and name.
SUBNATIONAL = {"US": ("State code", "State"), "CN": ("Province code", "Province")}
TOTAL = "Total generation"  # Ember's row for all sources of a geography and year
INTENSITY = "Emissions intensity (gCO2e/kWh)"
COLUMNS = ("geography", "name", "year", "intensity")


class Import(NamedTuple):
    errors: list[str]
    written: list[Path]


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def intensity_rows(
    global_csv: Path, subnational_csvs: dict[str, Path], year: int
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """The table's rows (each geography's total-generation intensity for `year`, or for its latest earlier year,
    sorted) and the areas left out, each with its reason. A country is keyed by its ISO 3166-1 alpha-2 code; a
    subdivision (a US state, a Chinese province) by its ISO 3166-2 code, such as US-VA or CN-GD. `subnational_csvs` maps
    a country in SUBNATIONAL to its release."""
    rows: list[dict[str, str]] = []
    skipped: dict[str, dict[str, str]] = {}
    for r in _read(global_csv):
        if r["Area type"] != "Country or economy" or r["Electricity source"] != TOTAL or not r[INTENSITY]:
            continue
        country = pycountry.countries.get(alpha_3=r["ISO 3 code"]) if r["ISO 3 code"] else None
        if country is None:
            skipped[r["Area"]] = {"area": r["Area"], "code": r["ISO 3 code"], "reason": "no ISO 3166-1 alpha-2 code"}
            continue
        rows.append({"geography": country.alpha_2, "name": r["Area"], "year": r["Year"], "intensity": r[INTENSITY]})
    for country, path in subnational_csvs.items():
        code_column, name_column = SUBNATIONAL[country]
        for r in _read(path):
            if r["Electricity source"] != TOTAL or not r[INTENSITY]:
                continue
            code = f"{country}-{r[code_column]}"
            if pycountry.subdivisions.get(code=code) is None:  # a national total, or a code ISO does not list
                skipped[code] = {"area": r[name_column], "code": code, "reason": "not an ISO 3166-2 subdivision"}
                continue
            rows.append({"geography": code, "name": r[name_column], "year": r["Year"], "intensity": r[INTENSITY]})
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        if int(row["year"]) > year:
            continue  # a later year is never used
        kept = latest.get(row["geography"])
        if kept is None or int(row["year"]) > int(kept["year"]):
            latest[row["geography"]] = row
    for row in rows:
        if row["geography"] not in latest:
            skipped[row["geography"]] = {
                "area": row["name"],
                "code": row["geography"],
                "reason": f"no year {year} or earlier",
            }
    return sorted(latest.values(), key=lambda row: row["geography"]), sorted(skipped.values(), key=lambda s: s["code"])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_ember(root: Path, global_csv: Path, us_csv: Path, china_csv: Path, today: date) -> Import:
    """Write sources/snapshots/grid_intensity.csv and its .provenance.json from Ember's three downloads, then rewrite
    every grid's intensity: from it (python -m build grid-emissions --write); list the files whose content changed."""
    for path in (global_csv, us_csv, china_csv):
        if not path.is_file():
            return Import([f"{path}: no such file; download it from the URL in sources/snapshots/README.md"], [])
    rows, skipped = intensity_rows(global_csv, {"US": us_csv, "CN": china_csv}, GRID_YEAR)
    table = root / GRID_INTENSITY_FILE
    lines = [",".join(COLUMNS)] + [",".join(_csv_field(row[c]) for c in COLUMNS) for row in rows]
    provenance = {
        "source": "Ember, yearly electricity data: emissions intensity of total generation (gCO2e/kWh)",
        "licence": "CC-BY-4.0; attribute Ember (ember-energy.org)",
        "basis": "life-cycle (IPCC AR5 emission factors per fuel), of generation: imports are not traced",
        "files": [
            {"url": GLOBAL_URL, "sha256": _sha256(global_csv)},
            {"url": US_URL, "sha256": _sha256(us_csv)},
            {"url": CHINA_URL, "sha256": _sha256(china_csv)},
        ],
        "retrieved": today.isoformat(),
        "year": GRID_YEAR,
        "rows": len(rows),
        "skipped": skipped,
    }
    outputs = {
        table: "\n".join(lines) + "\n",
        table.with_suffix(".provenance.json"): json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
    }
    written = []
    for path, text in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written.append(path)
    grids = grid_emissions(root, write=True)
    return Import(grids.errors, written + grids.written)


def _csv_field(value: str) -> str:
    """A value quoted for CSV when it holds a comma or a quote (some area names do)."""
    return '"' + value.replace('"', '""') + '"' if "," in value or '"' in value else value
