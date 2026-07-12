"""Validated adapter for the official SafeRAG dataset and knowledge bases."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ragshield.schemas import Document


TASKS = ("SA", "ICC", "SN", "WDoS")
DEFAULT_ROOT = Path("data/external/saferag")
DEFAULT_MANIFEST = Path("benchmarks/saferag/manifest.json")


@dataclass(frozen=True)
class SafeRAGCase:
    task: str
    case_id: int
    question: str
    golden_contexts: tuple[str, ...]
    attack_contexts: tuple[str, ...]
    attack_keywords: tuple[str, ...]
    numbered_options: tuple[str, ...]
    correct_options: tuple[str, ...]
    incorrect_options: tuple[str, ...]


@dataclass(frozen=True)
class SafeRAGDataset:
    root: Path
    manifest: dict[str, Any]
    cases: dict[str, list[SafeRAGCase]]
    knowledge_bases: dict[str, list[str]]

    @property
    def case_count(self) -> int:
        return sum(len(rows) for rows in self.cases.values())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(os.environ.get("SAFERAG_ROOT", DEFAULT_ROOT))


def validate_files(root: Path, manifest: dict[str, Any]) -> None:
    failures = []
    for relative, expected_hash in manifest["files"].items():
        path = root / relative
        if not path.is_file():
            failures.append(f"missing {relative}")
            continue
        actual_hash = _sha256(path)
        if actual_hash != expected_hash:
            failures.append(f"hash mismatch for {relative}: {actual_hash}")
    if failures:
        raise ValueError("SafeRAG validation failed: " + "; ".join(failures))


def load_saferag(
    root: str | Path | None = None,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    verify: bool = True,
) -> SafeRAGDataset:
    dataset_root = resolve_root(root)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if verify:
        validate_files(dataset_root, manifest)

    raw = json.loads((dataset_root / "nctd_datasets/nctd.json").read_text(encoding="utf-8"))
    cases: dict[str, list[SafeRAGCase]] = {}
    knowledge_bases: dict[str, list[str]] = {}
    for task in TASKS:
        task_rows = []
        for row in raw[task]:
            task_rows.append(
                SafeRAGCase(
                    task=task,
                    case_id=int(row["id"]),
                    question=row["questions"],
                    golden_contexts=tuple(row["enhanced_contexts"]),
                    attack_contexts=tuple(row[f"enhanced_{task}_contexts"]),
                    attack_keywords=tuple(row.get("attack_kws", [])),
                    numbered_options=tuple(row["numbered_options"]),
                    correct_options=tuple(row["ground_truth_correct_options"]),
                    incorrect_options=tuple(row["ground_truth_incorrect_options"]),
                )
            )
        cases[task] = task_rows
        knowledge_bases[task] = [
            line.strip()
            for line in (dataset_root / f"knowledge_base/{task}/db.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
    return SafeRAGDataset(dataset_root, manifest, cases, knowledge_bases)


def build_task_documents(dataset: SafeRAGDataset, task: str) -> list[Document]:
    if task not in TASKS:
        raise ValueError(f"Unsupported SafeRAG task: {task}")
    documents = [
        Document(
            doc_id=f"saferag_{task.lower()}_clean_{index:04d}",
            tenant="saferag",
            sensitivity="public",
            contains_pii=False,
            contains_prompt_injection=False,
            trusted_source=True,
            domain=f"saferag_{task.lower()}",
            title=f"SafeRAG {task} clean context {index}",
            text=text,
            metadata={"benchmark": "SafeRAG", "task": task, "partition": "clean"},
        )
        for index, text in enumerate(dataset.knowledge_bases[task])
    ]
    seen = set()
    for case in dataset.cases[task]:
        for context_index, text in enumerate(case.attack_contexts):
            if text in seen:
                continue
            seen.add(text)
            documents.append(
                Document(
                    doc_id=(
                        f"saferag_{task.lower()}_attack_"
                        f"{case.case_id:04d}_{context_index:02d}"
                    ),
                    tenant="saferag",
                    sensitivity="public",
                    contains_pii=False,
                    contains_prompt_injection=False,
                    trusted_source=False,
                    domain=f"saferag_{task.lower()}",
                    title=f"SafeRAG {task} injected context {case.case_id}",
                    text=text,
                    metadata={
                        "benchmark": "SafeRAG",
                        "task": task,
                        "partition": "attack",
                        "case_id": case.case_id,
                    },
                )
            )
    return documents
