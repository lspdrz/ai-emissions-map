"""Model parameter counts: one record per model in sources/models/, most of them copied from EcoLogits.

Every route's model has a record. A record with `source: ecologits` copies its parameter counts from the
pinned EcoLogits package; `build.validate` checks it still matches the installed package, so upgrading
EcoLogits shows every changed model as a diff in sources/models/. A record with `source: curated` is for a
model EcoLogits lacks, or whose developer's model card contradicts it, and carries its own evidence.

Usage:
    uv run python -m build.models --add gemini-3.5-flash   # write a record from the installed EcoLogits
    uv run python -m build.models --sync                   # bring every EcoLogits record up to date
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources as resources
import json
import os
import re
from pathlib import Path

from build.ranges import Range

_MANAGED = ("ecologits", "architecture", "active_b", "total_b")   # the lines --sync owns in an EcoLogits record
_SYNC = "run `python -m build.models --sync`"


class ModelsError(Exception):
    pass


def packaged_ecologits_models() -> list[dict]:
    text = (resources.files("ecologits") / "data" / "models.json").read_text(encoding="utf-8")
    return json.loads(text)["models"]


def installed_ecologits_version() -> str:
    return importlib.metadata.version("ecologits")


def model_slug(ecologits_id: str) -> str:
    """The record slug for an EcoLogits id: its last path segment, lowercased, other characters as hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", ecologits_id.rsplit("/", 1)[-1].lower()).strip("-")


def ecologits_record(entry: dict, version: str) -> dict:
    """The fields an EcoLogits catalogue entry gives a model record, in record form."""
    arch, params = entry["architecture"]["type"], entry["architecture"]["parameters"]
    if isinstance(params, dict) and "active" in params:
        active, total = params["active"], params["total"]
    else:
        active = total = params
    return {"ecologits": {"id": entry["name"], "version": version}, "architecture": arch,
            "active_b": active, "total_b": total}


def _params(value) -> Range:
    if isinstance(value, dict):
        return Range(float(value["min"]), float(value["max"]))
    return Range.point(float(value))


def model_specs(models: dict | None) -> dict[str, dict]:
    """Model id -> {"active_b", "total_b": Range of billions of parameters, "source": "ecologits" | "curated"}.

    `models` is load_sources(...)["models"]. Parameters are always read from the records; for EcoLogits
    records, build.validate has checked they match the installed package.
    """
    return {name: {"active_b": _params(m["active_b"]), "total_b": _params(m["total_b"]), "source": m["source"]}
            for name, m in (models or {}).items()}


def _show(value) -> str:
    if isinstance(value, dict) and set(value) == {"min", "max"}:
        return f"{value['min']:g}–{value['max']:g}"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value)


def check_ecologits_records(models: dict, package: list[dict], version: str) -> list[str]:
    """One message per EcoLogits record that no longer matches the installed package."""
    by_id = {e["name"]: e for e in package}
    errors = []
    for name, m in sorted(models.items()):
        if m.get("source") != "ecologits":
            continue
        eco_id = m["ecologits"]["id"]
        if eco_id not in by_id:
            errors.append(f"models/{name}.yaml: {eco_id!r} is not in EcoLogits {version}")
            continue
        expected = ecologits_record(by_id[eco_id], version)
        changes = []
        if m["ecologits"]["version"] != version:
            changes.append(f"version {m['ecologits']['version']} → {version}")
        changes += [f"{key} {_show(m.get(key))} → {_show(expected[key])}"
                    for key in ("architecture", "active_b", "total_b") if m.get(key) != expected[key]]
        if changes:
            errors.append(f"models/{name}.yaml: out of date with EcoLogits {version} ({'; '.join(changes)}); {_SYNC}")
    return errors


def _flow(value) -> str:
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{k}: {_flow(v)}" for k, v in value.items()) + " }"
    if isinstance(value, str):
        return json.dumps(value)   # a double-quoted YAML string
    return f"{value:g}" if isinstance(value, float) else str(value)


def _managed_lines(record: dict) -> dict[str, str]:
    return {key: f"{key}: {_flow(record[key])}" for key in _MANAGED}


def add_record(models_dir: Path, ecologits_id: str, package: list[dict], version: str) -> Path:
    entry = next((e for e in package if e["name"] == ecologits_id), None)
    if entry is None:
        raise ModelsError(f"{ecologits_id!r} is not in EcoLogits {version}")
    slug = model_slug(ecologits_id)
    path = models_dir / f"{slug}.yaml"
    if path.exists():
        raise ModelsError(f"sources/models/{slug}.yaml already exists")
    models_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"name: {slug}", f"display_name: {ecologits_id}", "source: ecologits",
             *_managed_lines(ecologits_record(entry, version)).values()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def sync_record(path: Path, record: dict, package: list[dict], version: str) -> bool:
    """Rewrite the managed lines of one EcoLogits record from the package; False if it already matched."""
    entry = next((e for e in package if e["name"] == record["ecologits"]["id"]), None)
    if entry is None:
        raise ModelsError(f"sources/models/{path.name}: {record['ecologits']['id']!r} is not in EcoLogits {version}")
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    new = text
    for key, line in _managed_lines(ecologits_record(entry, version)).items():
        pattern = re.compile(rf"^{key}:[^\r\n]*$", re.M)
        if len(pattern.findall(new)) != 1:
            raise ModelsError(f"sources/models/{path.name}: expected one single-line {key!r}; edit it by hand")
        new = pattern.sub(lambda _: line, new)
    if new == text:
        return False
    temp = path.with_name(f".{path.name}.sync")
    with temp.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new)
    os.replace(temp, path)
    return True


def main(argv: list[str] | None = None, package: list[dict] | None = None, version: str | None = None) -> int:
    from build.validate import ROOT, load_sources

    parser = argparse.ArgumentParser(prog="python -m build.models", description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--add", nargs="+", metavar="ECOLOGITS_ID", help="write a record for each EcoLogits id")
    action.add_argument("--sync", action="store_true", help="bring every EcoLogits record up to date")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    package = packaged_ecologits_models() if package is None else package
    version = installed_ecologits_version() if version is None else version
    models_dir = args.root / "sources" / "models"
    try:
        if args.add:
            for eco_id in args.add:
                path = add_record(models_dir, eco_id, package, version)
                print(f"wrote sources/models/{path.name}")
        else:
            models = load_sources(args.root)["models"]
            changed = [name for name, m in sorted(models.items()) if m.get("source") == "ecologits"
                       and sync_record(models_dir / f"{name}.yaml", m, package, version)]
            for name in changed:
                print(f"updated sources/models/{name}.yaml")
            print(f"{len(changed)} record(s) updated to EcoLogits {version}")
    except ModelsError as e:
        print(f"ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
