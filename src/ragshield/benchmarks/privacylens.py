"""Validated adapter for the peer-reviewed PrivacyLens dataset."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ragshield.benchmarks.provenance import load_manifest, validate_manifest_files


DEFAULT_ROOT = Path("data/external/privacylens")
DEFAULT_MANIFEST = Path("benchmarks/privacylens/manifest.json")


@dataclass(frozen=True)
class PrivacyLensCase:
    case_id: str
    source: str
    data_type: str
    data_subject: str
    data_sender: str
    data_recipient: str
    transmission_principle: str
    vignette: str
    user_instruction: str
    toolkits: tuple[str, ...]
    executable_trajectory: str
    final_action: str
    sensitive_info_items: tuple[str, ...]


@dataclass(frozen=True)
class PrivacyLensDataset:
    root: Path
    manifest: dict[str, Any]
    cases: tuple[PrivacyLensCase, ...]

    @property
    def sensitive_item_count(self) -> int:
        return sum(len(case.sensitive_info_items) for case in self.cases)


def load_privacylens(
    root: str | Path = DEFAULT_ROOT,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    verify: bool = True,
) -> PrivacyLensDataset:
    dataset_root = Path(root)
    manifest = (
        validate_manifest_files(dataset_root, manifest_path)
        if verify
        else load_manifest(manifest_path)
    )
    raw_rows = json.loads((dataset_root / "data/main_data.json").read_text(encoding="utf-8"))
    cases = []
    for row in raw_rows:
        seed = row["seed"]
        trajectory = row["trajectory"]
        cases.append(
            PrivacyLensCase(
                case_id=str(row["name"]),
                source=str(seed["source"]),
                data_type=str(seed["data_type"]),
                data_subject=str(seed["data_subject"]),
                data_sender=str(seed["data_sender"]),
                data_recipient=str(seed["data_recipient"]),
                transmission_principle=str(seed["transmission_principle"]),
                vignette=str(row["vignette"]["story"]),
                user_instruction=str(trajectory["user_instruction"]),
                toolkits=tuple(str(value) for value in trajectory["toolkits"]),
                executable_trajectory=str(trajectory["executable_trajectory"]),
                final_action=str(trajectory["final_action"]),
                sensitive_info_items=tuple(
                    str(value) for value in trajectory["sensitive_info_items"]
                ),
            )
        )

    expected = manifest["expected_counts"]
    if len(cases) != expected["cases"]:
        raise ValueError(f"PrivacyLens expected {expected['cases']} cases, found {len(cases)}")
    dataset = PrivacyLensDataset(dataset_root, manifest, tuple(cases))
    if dataset.sensitive_item_count != expected["sensitive_items"]:
        raise ValueError(
            "PrivacyLens expected "
            f"{expected['sensitive_items']} sensitive items, "
            f"found {dataset.sensitive_item_count}"
        )
    return dataset
