"""Frozen offline TAB evaluation and public aggregate report generation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from ragshield.benchmarks.tab import TABSpanMetrics, evaluate_tab_spans, load_tab
from ragshield.defenses.ner_privacy_guard import SpacyPrivacyGuard
from ragshield.defenses.privacy_guard import SensitiveFinding, detect_sensitive_data


PROTOCOL_VERSION = "tab-offline-external-v1"
DEFAULT_SPACY_MODEL = "en_core_web_sm"


def build_tab_summary(
    root: str | Path,
    manifest_path: str | Path,
    model_name: str = DEFAULT_SPACY_MODEL,
) -> dict:
    dataset = load_tab(root, manifest_path, splits=("test",), verify=True)
    guard = SpacyPrivacyGuard.from_model(model_name)
    detectors: dict[str, Callable[[str], Iterable[SensitiveFinding]]] = {
        "regex_rules": detect_sensitive_data,
        "spacy_ner": guard.detect_entities,
        "combined": guard.detect,
    }
    results: dict[str, dict] = {}
    for name, detector in detectors.items():
        metrics: TABSpanMetrics = evaluate_tab_spans(dataset, detector)
        results[name] = metrics.to_dict()
    return {
        "study": {
            "protocol_version": PROTOCOL_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "benchmark": dataset.manifest["name"],
            "benchmark_commit": dataset.manifest["commit"],
            "benchmark_venue": dataset.manifest["venue"],
            "benchmark_license": dataset.manifest["license"],
            "split": "test",
            "documents": len(dataset.documents),
            "quality_checked_documents": sum(row.quality_checked for row in dataset.documents),
            "spacy_model": model_name,
            "api_calls": 0,
            "estimated_api_cost_usd": 0.0,
        },
        "systems": results,
        "claim_boundary": {
            "supported": [
                "Offline span-detection performance on TAB's human annotations.",
                "Comparison of fixed regex, spaCy NER, and combined detectors.",
            ],
            "not_supported": [
                "Re-identification resistance or production privacy guarantees.",
                "LLM privacy behavior, because this study makes no LLM API calls.",
            ],
        },
    }


def write_tab_markdown(summary: dict, output: str | Path) -> None:
    study = summary["study"]
    systems = summary["systems"]
    lines = [
        "# RAGShield TAB Offline Privacy Evaluation",
        "",
        "## Study Identity",
        "",
        f"- Protocol: `{study['protocol_version']}`",
        f"- Benchmark commit: `{study['benchmark_commit']}`",
        f"- Split: `{study['split']}` ({study['documents']} quality-checked documents)",
        f"- NER model: `{study['spacy_model']}`",
        "- LLM API calls: 0",
        "",
        "## Results",
        "",
        "| System | Character F1 | Exact Mention F1 | Full Coverage Recall | "
        "Overlap Recall | False-positive Character Rate | Text Retention |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("regex_rules", "spacy_ner", "combined"):
        row = systems[name]
        lines.append(
            f"| {name} | {row['character_f1']:.3f} | "
            f"{row['exact_mention_f1']:.3f} | {row['full_coverage_recall']:.3f} | "
            f"{row['overlap_recall']:.3f} | {row['false_positive_character_rate']:.3f} | "
            f"{row['text_retention_rate']:.3f} |"
        )
    combined = systems["combined"]
    lines.extend(
        [
            "",
            "## Combined Detector by Entity Type",
            "",
            "| Entity Type | Full Coverage Recall |",
            "|---|---:|",
        ]
    )
    for entity_type, value in combined["full_coverage_recall_by_type"].items():
        lines.append(f"| {entity_type} | {value:.3f} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The regex-only detector targets structured secrets and therefore does not cover ordinary "
            "court-document names, locations, or organizations. NER broadens coverage but also "
            "redacts non-gold spans. This external evaluation measures that privacy-utility trade-off "
            "instead of treating all redaction as correct.",
            "",
            "## Claim Boundary",
            "",
            "This is an offline evaluation against TAB's human span annotations. It is not an LLM "
            "generation study and does not establish re-identification resistance or production privacy.",
        ]
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("dry-run", "report"), default="dry-run")
    parser.add_argument("--root", default="data/external/tab")
    parser.add_argument("--manifest", default="benchmarks/tab/manifest.json")
    parser.add_argument("--spacy-model", default=DEFAULT_SPACY_MODEL)
    parser.add_argument("--results-output", default="reports/tab_offline_results.json")
    parser.add_argument("--report-output", default="reports/tab_offline_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_tab(args.root, args.manifest, splits=("test",), verify=True)
    print(
        json.dumps(
            {
                "protocol": PROTOCOL_VERSION,
                "documents": len(dataset.documents),
                "spacy_model": args.spacy_model,
                "api_calls": 0,
            },
            indent=2,
        )
    )
    if args.phase == "dry-run":
        return
    summary = build_tab_summary(args.root, args.manifest, args.spacy_model)
    Path(args.results_output).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_tab_markdown(summary, args.report_output)


if __name__ == "__main__":
    main()
