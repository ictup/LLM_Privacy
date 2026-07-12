"""Fetch the pinned SafeRAG repository without redistributing its dataset."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


DEFAULT_MANIFEST = Path("benchmarks/saferag/manifest.json")
DEFAULT_OUTPUT = Path("data/external/saferag")


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def fetch(manifest_path: Path, output: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_commit = manifest["commit"]
    safe_directory = f"safe.directory={output.resolve().as_posix()}"
    if output.exists():
        actual_commit = run(["git", "-c", safe_directory, "rev-parse", "HEAD"], cwd=output)
        if actual_commit != expected_commit:
            raise SystemExit(
                f"SafeRAG exists at {output} but has commit {actual_commit}; "
                f"expected {expected_commit}. Remove or relocate it manually before retrying."
            )
        print(f"SafeRAG already present at pinned commit {expected_commit}.")
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", manifest["repository"], str(output)])
    run(["git", "-c", safe_directory, "checkout", expected_commit], cwd=output)
    actual_commit = run(["git", "-c", safe_directory, "rev-parse", "HEAD"], cwd=output)
    if actual_commit != expected_commit:
        raise SystemExit(f"Checkout verification failed: {actual_commit}")
    print(f"Fetched SafeRAG {expected_commit} into {output}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    fetch(args.manifest, args.output)
