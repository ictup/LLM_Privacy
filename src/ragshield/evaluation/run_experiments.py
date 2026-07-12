"""Run baseline, ablation, and full-defense experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ragshield.evaluation.attack_runner import run_cases
from ragshield.utils.jsonl import read_jsonl, write_jsonl


EXPERIMENTS = [
    ("Baseline RAG", "baseline", "configs/baseline.yaml"),
    ("+ Context Separation", "context_boundary", "configs/context_boundary.yaml"),
    ("+ Retrieval Sanitizer", "retrieval_sanitizer", "configs/retrieval_sanitizer.yaml"),
    ("+ PII Redaction", "pii_redaction", "configs/pii_redaction.yaml"),
    ("+ Tool Gate", "tool_gate", "configs/tool_gate.yaml"),
    ("Full RAGShield", "ragshield_full", "configs/ragshield_full.yaml"),
]


def load_default_cases() -> list[dict]:
    paths = [
        "data/attacks/all.jsonl",
        "data/eval_sets/mixed_qa.jsonl",
        "data/eval_sets/benign_qa.jsonl",
    ]
    cases: list[dict] = []
    for path in paths:
        cases.extend(read_jsonl(path))
    return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="reports")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = load_default_cases()
    summaries = []

    for display_name, slug, config_path in EXPERIMENTS:
        rows, summary = run_cases(
            config_path=config_path,
            cases=cases,
            trace_output=str(output_dir / f"{slug}.trace.jsonl"),
        )
        result_path = output_dir / f"{slug}_results.jsonl"
        write_jsonl(result_path, rows)
        summary_with_name = {
            "system": display_name,
            "slug": slug,
            "config": config_path,
            **summary,
        }
        summaries.append(summary_with_name)
        print(
            f"{display_name}: ASR={summary['attack_success_rate']} "
            f"Leakage={summary['leakage_rate']} Benign={summary['benign_success_rate']}"
        )

    summary_path = output_dir / "experiment_summaries.json"
    summary_path.write_text(json.dumps(summaries, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote experiment summaries to {summary_path}.")


if __name__ == "__main__":
    main()
