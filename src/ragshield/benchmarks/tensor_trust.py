"""Validated adapters and label-based metrics for Tensor Trust v1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from ragshield.benchmarks.provenance import load_manifest, validate_manifest_files


DEFAULT_ROOT = Path("data/external/tensor-trust")
DEFAULT_MANIFEST = Path("benchmarks/tensor_trust/manifest.json")


@dataclass(frozen=True)
class TensorTrustRobustnessCase:
    task: str
    sample_id: str
    pre_prompt: str
    attack: str
    post_prompt: str
    access_code: str

    @property
    def attack_prompt(self) -> str:
        return f"{self.pre_prompt}{self.attack}{self.post_prompt}"

    @property
    def utility_prompt(self) -> str:
        return f"{self.pre_prompt}{self.access_code}{self.post_prompt}"


@dataclass(frozen=True)
class ExtractionDetectionCase:
    sample_id: str
    access_code: str
    llm_output: str
    is_prompt_extraction: bool


@dataclass(frozen=True)
class TensorTrustDataset:
    root: Path
    manifest: dict[str, Any]
    extraction_cases: tuple[TensorTrustRobustnessCase, ...]
    hijacking_cases: tuple[TensorTrustRobustnessCase, ...]
    detection_cases: tuple[ExtractionDetectionCase, ...]


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    total: int
    positives: int
    negatives: int
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    accuracy: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _load_robustness_cases(
    path: Path,
    task: str,
) -> tuple[TensorTrustRobustnessCase, ...]:
    return tuple(
        TensorTrustRobustnessCase(
            task=task,
            sample_id=str(row["sample_id"]),
            pre_prompt=str(row["pre_prompt"]),
            attack=str(row["attack"]),
            post_prompt=str(row["post_prompt"]),
            access_code=str(row["access_code"]),
        )
        for row in _read_jsonl(path)
    )


def load_tensor_trust(
    root: str | Path = DEFAULT_ROOT,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    verify: bool = True,
) -> TensorTrustDataset:
    dataset_root = Path(root)
    manifest = (
        validate_manifest_files(dataset_root, manifest_path)
        if verify
        else load_manifest(manifest_path)
    )
    extraction = _load_robustness_cases(
        dataset_root
        / "benchmarks/extraction-robustness/v1/extraction_robustness_dataset.jsonl",
        "extraction",
    )
    hijacking = _load_robustness_cases(
        dataset_root / "benchmarks/hijacking-robustness/v1/hijacking_robustness_dataset.jsonl",
        "hijacking",
    )
    detection = tuple(
        ExtractionDetectionCase(
            sample_id=str(row["sample_id"]),
            access_code=str(row["access_code"]),
            llm_output=str(row["llm_output"]),
            is_prompt_extraction=bool(row["is_prompt_extraction"]),
        )
        for row in _read_jsonl(
            dataset_root / "detecting-extractions/v1/prompt_extraction_detection.jsonl"
        )
    )
    expected = manifest["expected_counts"]
    actual = {
        "extraction_robustness": len(extraction),
        "hijacking_robustness": len(hijacking),
        "extraction_detection": len(detection),
    }
    if actual != expected:
        raise ValueError(f"Tensor Trust count mismatch: expected {expected}, got {actual}")
    return TensorTrustDataset(dataset_root, manifest, extraction, hijacking, detection)


def verbatim_extraction_detector(case: ExtractionDetectionCase) -> bool:
    return case.access_code in case.llm_output


def score_extraction_detector(
    cases: tuple[ExtractionDetectionCase, ...],
    detector: Callable[[ExtractionDetectionCase], bool],
) -> BinaryClassificationMetrics:
    true_positive = false_positive = true_negative = false_negative = 0
    for case in cases:
        prediction = bool(detector(case))
        if prediction and case.is_prompt_extraction:
            true_positive += 1
        elif prediction:
            false_positive += 1
        elif case.is_prompt_extraction:
            false_negative += 1
        else:
            true_negative += 1

    positives = true_positive + false_negative
    negatives = true_negative + false_positive
    precision = true_positive / (true_positive + false_positive) if true_positive else 0.0
    recall = true_positive / positives if positives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    total = positives + negatives
    accuracy = (true_positive + true_negative) / total if total else 0.0
    return BinaryClassificationMetrics(
        total=total,
        positives=positives,
        negatives=negatives,
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
        precision=round(precision, 6),
        recall=round(recall, 6),
        f1=round(f1, 6),
        accuracy=round(accuracy, 6),
    )
