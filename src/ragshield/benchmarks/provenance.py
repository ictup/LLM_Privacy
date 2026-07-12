"""Shared provenance checks for externally maintained benchmark files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_manifest_files(
    root: str | Path,
    manifest_path: str | Path,
) -> dict[str, Any]:
    dataset_root = Path(root)
    manifest = load_manifest(manifest_path)
    failures = []
    for relative_path, expected_hash in manifest.get("files", {}).items():
        path = dataset_root / relative_path
        if not path.is_file():
            failures.append(f"missing {relative_path}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            failures.append(
                f"hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )
    if failures:
        name = manifest.get("name", "benchmark")
        raise ValueError(f"{name} validation failed: " + "; ".join(failures))
    return manifest
