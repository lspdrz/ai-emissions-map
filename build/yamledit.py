"""Change scalar values in a YAML file without re-serializing it.

Corpus files are hand-formatted, and a load-modify-dump round trip rewraps strings, drops comments and
buries the one change that was meant (os-ai-map's rule: never load-modify-dump a file in sources/).
This module asks PyYAML's composer where each target value sits, replaces exactly those characters,
and then re-reads the result to prove that nothing but the named values changed.
"""

from __future__ import annotations

import copy

import yaml

Path = tuple[str | int, ...]


class YamlEditError(Exception):
    pass


def _render(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"   # single-quoted: no escapes except a doubled quote
    raise YamlEditError(f"cannot write a {type(value).__name__}")


def _node_at(root: yaml.Node, path: Path) -> yaml.Node:
    node = root
    for depth, key in enumerate(path):
        where = ".".join(str(p) for p in path[: depth + 1])
        if isinstance(key, int) and isinstance(node, yaml.SequenceNode) and key < len(node.value):
            node = node.value[key]
        elif isinstance(key, str) and isinstance(node, yaml.MappingNode):
            matches = [v for k, v in node.value if k.value == key]
            if not matches:
                raise YamlEditError(f"{where}: no such key")
            node = matches[0]
        else:
            raise YamlEditError(f"{where}: no such item")
    return node


def _apply(data: object, path: Path, value: object) -> None:
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


def set_scalars(text: str, updates: dict[Path, object]) -> str:
    """Return `text` with each path's scalar set to its value; everything else byte-for-byte unchanged."""
    root = yaml.compose(text)
    spans = []
    for path, value in updates.items():
        node = _node_at(root, path)
        if not isinstance(node, yaml.ScalarNode):
            raise YamlEditError(f"{'.'.join(str(p) for p in path)}: not a scalar")
        spans.append((node.start_mark.index, node.end_mark.index, _render(value)))
    new = text
    for start, end, rendered in sorted(spans, reverse=True):   # back to front, so earlier offsets hold
        new = new[:start] + rendered + new[end:]
    expected = copy.deepcopy(yaml.safe_load(text))
    for path, value in updates.items():
        _apply(expected, path, value)
    if yaml.safe_load(new) != expected:
        raise YamlEditError("the edited document does not read back as intended")
    return new
