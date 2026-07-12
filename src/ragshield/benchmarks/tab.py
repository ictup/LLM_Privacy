"""Validated TAB loader and transparent span-coverage metrics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from ragshield.benchmarks.provenance import load_manifest, validate_manifest_files


DEFAULT_ROOT = Path("data/external/tab")
DEFAULT_MANIFEST = Path("benchmarks/tab/manifest.json")
MASK_IDENTIFIERS = frozenset({"DIRECT", "QUASI"})


@dataclass(frozen=True)
class TABMention:
    start: int
    end: int
    entity_type: str
    identifier_type: str


@dataclass(frozen=True)
class TABDocument:
    doc_id: str
    text: str
    dataset_type: str
    quality_checked: bool
    mentions: tuple[TABMention, ...]

    @property
    def mentions_to_mask(self) -> tuple[TABMention, ...]:
        return tuple(
            mention for mention in self.mentions if mention.identifier_type in MASK_IDENTIFIERS
        )


@dataclass(frozen=True)
class TABDataset:
    root: Path
    manifest: dict[str, Any]
    documents: tuple[TABDocument, ...]


@dataclass(frozen=True)
class TABSpanMetrics:
    documents: int
    document_characters: int
    gold_mentions: int
    predicted_spans: int
    exact_matches: int
    fully_covered_mentions: int
    overlapping_mentions: int
    gold_characters: int
    predicted_characters: int
    intersecting_characters: int
    character_precision: float
    character_recall: float
    character_f1: float
    exact_mention_precision: float
    exact_mention_recall: float
    exact_mention_f1: float
    full_coverage_recall: float
    overlap_recall: float
    predicted_character_rate: float
    false_positive_character_rate: float
    text_retention_rate: float
    full_coverage_recall_by_type: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_tab(
    root: str | Path = DEFAULT_ROOT,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    splits: tuple[str, ...] = ("test",),
    verify: bool = True,
) -> TABDataset:
    dataset_root = Path(root)
    manifest = (
        validate_manifest_files(dataset_root, manifest_path)
        if verify
        else load_manifest(manifest_path)
    )
    documents = []
    for split in splits:
        if split not in {"train", "dev", "test"}:
            raise ValueError(f"Unsupported TAB split: {split}")
        rows = json.loads((dataset_root / f"echr_{split}.json").read_text(encoding="utf-8"))
        expected = manifest["expected_counts"][f"{split}_documents"]
        if len(rows) != expected:
            raise ValueError(f"TAB {split} expected {expected} documents, found {len(rows)}")
        for row in rows:
            mentions = set()
            for entity in row["annotations"].values():
                for mention in entity["entity_mentions"]:
                    mentions.add(
                        TABMention(
                            start=int(mention["start_offset"]),
                            end=int(mention["end_offset"]),
                            entity_type=str(mention["entity_type"]),
                            identifier_type=str(mention["identifier_type"]),
                        )
                    )
            documents.append(
                TABDocument(
                    doc_id=str(row["doc_id"]),
                    text=str(row["text"]),
                    dataset_type=str(row["dataset_type"]),
                    quality_checked=bool(row["quality_checked"]),
                    mentions=tuple(
                        sorted(
                            mentions,
                            key=lambda value: (
                                value.start,
                                value.end,
                                value.entity_type,
                                value.identifier_type,
                            ),
                        )
                    ),
                )
            )
    if splits == ("test",):
        quality_checked = sum(document.quality_checked for document in documents)
        expected_checked = manifest["expected_counts"]["quality_checked_test_documents"]
        if quality_checked != expected_checked:
            raise ValueError(
                f"TAB expected {expected_checked} quality-checked test documents, "
                f"found {quality_checked}"
            )
    return TABDataset(dataset_root, manifest, tuple(documents))


def _merge_spans(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    rows = sorted({(start, end) for start, end in spans if end > start})
    merged: list[tuple[int, int]] = []
    for start, end in rows:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
    return merged


def _span_length(spans: Iterable[tuple[int, int]]) -> int:
    return sum(end - start for start, end in spans)


def _intersection_length(
    left: list[tuple[int, int]],
    right: list[tuple[int, int]],
) -> int:
    left_index = right_index = total = 0
    while left_index < len(left) and right_index < len(right):
        left_start, left_end = left[left_index]
        right_start, right_end = right[right_index]
        total += max(0, min(left_end, right_end) - max(left_start, right_start))
        if left_end <= right_end:
            left_index += 1
        else:
            right_index += 1
    return total


def evaluate_tab_spans(
    dataset: TABDataset,
    detector: Callable[[str], Iterable[Any]],
) -> TABSpanMetrics:
    gold_mentions = predicted_spans = exact_matches = 0
    fully_covered = overlapping = 0
    document_characters = 0
    gold_characters = predicted_characters = intersecting_characters = 0
    type_totals: dict[str, int] = {}
    type_covered: dict[str, int] = {}

    for document in dataset.documents:
        document_characters += len(document.text)
        gold = document.mentions_to_mask
        predictions = [
            (int(finding.start), int(finding.end))
            for finding in detector(document.text)
            if 0 <= int(finding.start) < int(finding.end) <= len(document.text)
        ]
        gold_spans = [(mention.start, mention.end) for mention in gold]
        gold_set = set(gold_spans)
        prediction_set = set(predictions)
        gold_mentions += len(gold)
        predicted_spans += len(prediction_set)
        exact_matches += len(gold_set & prediction_set)

        for mention in gold:
            type_totals[mention.entity_type] = type_totals.get(mention.entity_type, 0) + 1
            is_covered = any(
                predicted_start <= mention.start and predicted_end >= mention.end
                for predicted_start, predicted_end in prediction_set
            )
            has_overlap = any(
                predicted_start < mention.end and predicted_end > mention.start
                for predicted_start, predicted_end in prediction_set
            )
            if is_covered:
                fully_covered += 1
                type_covered[mention.entity_type] = type_covered.get(mention.entity_type, 0) + 1
            if has_overlap:
                overlapping += 1

        merged_gold = _merge_spans(gold_spans)
        merged_predictions = _merge_spans(prediction_set)
        gold_characters += _span_length(merged_gold)
        predicted_characters += _span_length(merged_predictions)
        intersecting_characters += _intersection_length(merged_gold, merged_predictions)

    character_precision = (
        intersecting_characters / predicted_characters if predicted_characters else 0.0
    )
    character_recall = intersecting_characters / gold_characters if gold_characters else 0.0
    character_f1 = (
        2 * character_precision * character_recall / (character_precision + character_recall)
        if character_precision + character_recall
        else 0.0
    )
    exact_precision = exact_matches / predicted_spans if predicted_spans else 0.0
    exact_recall = exact_matches / gold_mentions if gold_mentions else 0.0
    exact_f1 = (
        2 * exact_precision * exact_recall / (exact_precision + exact_recall)
        if exact_precision + exact_recall
        else 0.0
    )
    return TABSpanMetrics(
        documents=len(dataset.documents),
        document_characters=document_characters,
        gold_mentions=gold_mentions,
        predicted_spans=predicted_spans,
        exact_matches=exact_matches,
        fully_covered_mentions=fully_covered,
        overlapping_mentions=overlapping,
        gold_characters=gold_characters,
        predicted_characters=predicted_characters,
        intersecting_characters=intersecting_characters,
        character_precision=round(character_precision, 6),
        character_recall=round(character_recall, 6),
        character_f1=round(character_f1, 6),
        exact_mention_precision=round(exact_precision, 6),
        exact_mention_recall=round(exact_recall, 6),
        exact_mention_f1=round(exact_f1, 6),
        full_coverage_recall=round(fully_covered / gold_mentions, 6) if gold_mentions else 0.0,
        overlap_recall=round(overlapping / gold_mentions, 6) if gold_mentions else 0.0,
        predicted_character_rate=(
            round(predicted_characters / document_characters, 6) if document_characters else 0.0
        ),
        false_positive_character_rate=(
            round((predicted_characters - intersecting_characters) / document_characters, 6)
            if document_characters
            else 0.0
        ),
        text_retention_rate=(
            round(1 - predicted_characters / document_characters, 6)
            if document_characters
            else 0.0
        ),
        full_coverage_recall_by_type={
            entity_type: round(type_covered.get(entity_type, 0) / total, 6)
            for entity_type, total in sorted(type_totals.items())
        },
    )
