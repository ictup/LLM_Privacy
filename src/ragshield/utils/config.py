"""Minimal YAML-like config loader for the repository's simple config files."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if value.startswith("[") and value.endswith("]"):
        return ast.literal_eval(value)
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_config(path: str | Path) -> dict[str, Any]:
    """Load the limited YAML subset used in configs/*.yaml.

    The project intentionally avoids a runtime dependency on PyYAML so the
    prototype can run in a clean Python environment.
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, separator, value = raw_line.strip().partition(":")
        if not separator:
            raise ValueError(f"Invalid config line: {raw_line!r}")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return root
