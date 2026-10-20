"""The release, python -m build release: validate sources/ and write web/data/data.json from it, with the hash
of its inputs. It computes nothing: the fields it publishes are written by `python -m build score`.

The hash (meta.inputs_sha) covers everything a published value depends on. The CI gate
`python -m build check-site-data` recomputes it: if sources/ or build/ changed since the last release, the hashes
differ and CI fails until the release is run again."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Any, NamedTuple, cast

from build.generate_site_data import build_data, check_contract
from build.load_sources import SOURCE_DIRS, load_sources
from build.schemas.sources import Sources
from build.validate import check_stored_scores, validate_sources

DATA_FILE = Path("web") / "data" / "data.json"
# What a release changes in data.json without changing what the site shows.
_STAMPS = ("release_date", "inputs_sha")


class Release(NamedTuple):
    errors: list[str]
    written: list[Path]


def _shown(data: dict[str, Any]) -> dict[str, Any]:
    return {**data, "meta": {k: v for k, v in data["meta"].items() if k not in _STAMPS}}


def _previous(out: Path) -> dict[str, Any] | None:
    """The committed data.json, or None if there is none or it cannot be read (a merge conflict in it, for example:
    rerunning the release is how that conflict is resolved)."""
    try:
        previous = json.loads(out.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return previous if isinstance(previous, dict) and "release_date" in previous.get("meta", {}) else None


def _write_data(root: Path, data: dict[str, Any], today: date) -> bool:
    """Write data.json, keeping the previous release date unless what the site shows changed. True if written."""
    out = root / DATA_FILE
    previous = _previous(out)
    same = previous is not None and _shown(previous) == _shown(data)
    data["meta"]["release_date"] = previous["meta"]["release_date"] if same and previous else today.isoformat()
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out.exists() and out.read_text(encoding="utf-8") == text:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return True


def _input_files(root: Path) -> list[Path]:
    """The files the release reads: the records (grid files included) and build/'s code."""
    files = [p for name in SOURCE_DIRS for p in (root / "sources" / name).glob("*.yaml")]
    files += (root / "build").rglob("*.py")
    return sorted(p for p in files if not p.name.startswith("."))


def inputs_sha(root: Path) -> str:
    """SHA-256 over the installed EcoLogits version and each input file's path and content."""
    h = hashlib.sha256()
    h.update(f"ecologits {version('ecologits')}\n".encode())
    for p in _input_files(root):
        h.update(p.relative_to(root).as_posix().encode() + b"\0")
        h.update(hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).digest())  # CRLF hashes as LF
    return h.hexdigest()


def release(root: Path, today: date) -> Release:
    data = load_sources(root)
    errors = validate_sources(data)
    if not errors:
        errors = check_stored_scores(data)
    if errors:
        return Release(errors, [])
    site = build_data(cast(Sources, data), today)
    site["meta"]["inputs_sha"] = inputs_sha(root)
    problems = check_contract(site)
    if problems:
        return Release(["the data file would leave its contract: " + "; ".join(problems)], [])
    written = [root / DATA_FILE] if _write_data(root, site, today) else []
    return Release([], written)
