"""Break a valid record, for tests that need invalid data: build it with a builder, then break it here.

Both return a deep copy as a plain dict, so the builder's record is untouched and the result is free
to be anything the files on disk could hold.
"""

import copy
from collections.abc import Mapping
from typing import Any


def changed(record: Mapping[str, Any], *path: str | int, to: Any) -> dict[str, Any]:
    """`record` with the value at `path` set to `to` (added if the last key is missing)."""
    broken = copy.deepcopy(dict(record))
    node: Any = broken
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = to
    return broken


def without(record: Mapping[str, Any], *path: str | int) -> dict[str, Any]:
    """`record` with the value at `path` removed."""
    broken = copy.deepcopy(dict(record))
    node: Any = broken
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return broken
