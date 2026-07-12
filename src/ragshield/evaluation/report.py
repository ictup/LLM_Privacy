"""Generate Markdown and CSV experiment reports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


CSV_FIELDS = [
    "System",
    "ASR",
    "Leakage",
    "System Prompt Exposure",
    "Unauthorized Tools",
    "Policy Bypass",
    "Poisoned Retrieval Influence",
    "Benign Success",
    "Avg Latency ms",
    "Latency Overhead ms",
]


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _load(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows(summaries: list[dict[str, Any]]) -> list[dict[str, str]]:
    baseline_latency = summaries[0].get("avg_latency_ms", 0.0) if summaries else 0.0
    rows = []
    for summary in summaries:
        latency = summary.get("avg_latency_ms", 0.0)
        rows.append(
            {
                "System": summary["system"],
                "ASR": _pct(summary["attack_success_rate"]),
                "Leakage": _pct(summary["leakage_rate"]),
                "System Prompt Exposure": _pct(summary["system_prompt_exposure_rate"]),
                "Unauthorized Tools": _pct(summary["unauthorized_tool_call_rate"]),
                "Policy Bypass": _pct(summary["policy_bypass_rate"]),
                "Poisoned Retrieval Influence": _pct(summary["poisoned_retrieval_influence_rate"]),
                "Benign Success": _pct(summary["benign_success_rate"]),
                "Avg Latency ms": f"{latency:.3f}",
                "Latency Overhead ms": f"{latency - baseline_latency:.3f}",
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summaries: list[dict[str, Any]], rows: list[dict[str, str]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RAGShield Experiment Results",
        "",
        "These results are from the deterministic scenario-v2 synthetic benchmark. The corpus",
        "uses varied fictional enterprise records, but results must not be overclaimed as",
        "real-world security guarantees or general model-security measurements.",
        "",
        "## Setup",
        "",
        f"- Systems evaluated: {len(summaries)}",
        f"- Attack and mixed tests: {summaries[0]['attack_n'] if summaries else 0}",
        f"- Benign QA tests: {summaries[0]['benign_n'] if summaries else 0}",
        "- Corpus: 240 synthetic documents across HR, medical, engineering, project, support,",
        "  finance, tool manual, and poisoned document domains, with 32 source types.",
        "- Dataset quality: 100% exact uniqueness; 77.5% normalized corpus uniqueness after",
        "  removing identifiers and numbers. See `reports/data_quality.md`.",
        "",
        "## Summary Table",
        "",
        "| System | ASR ↓ | Leakage ↓ | Unauthorized Tools ↓ | Benign Success ↑ | Latency Overhead ↓ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['System']} | {row['ASR']} | {row['Leakage']} | "
            f"{row['Unauthorized Tools']} | {row['Benign Success']} | "
            f"{row['Latency Overhead ms']} ms |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The baseline retains high benign utility but fails most adversarial scenarios.",
            "- Context separation blocks direct and indirect instruction-following attacks; retrieval",
            "  sanitization then removes residual poisoned-evidence influence and restores benign",
            "  failures caused by contaminated retrieval.",
            "- Redaction, tool gating, and tenant filtering produce distinct incremental reductions,",
            "  making the cumulative ablation easier to interpret than the original template run.",
            "- Full RAGShield combines all layers and has no observed attack success in this fixed",
            "  benchmark. This is an in-distribution result, not evidence of universal robustness.",
            "- The experiment is intentionally conservative in scope: all data, secrets, tools,",
            "  and attacks are synthetic.",
            "",
            "## Category-Level ASR",
            "",
        ]
    )
    for summary in summaries:
        lines.append(f"### {summary['system']}")
        lines.append("")
        lines.append("| Category | N | ASR | Leakage | Unauthorized Tools |")
        lines.append("|---|---:|---:|---:|---:|")
        for category, category_summary in sorted(summary["by_category"].items()):
            lines.append(
                f"| {category} | {category_summary['n']} | "
                f"{_pct(category_summary['attack_success_rate'])} | "
                f"{_pct(category_summary['leakage_rate'])} | "
                f"{_pct(category_summary['unauthorized_tool_call_rate'])} |"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summaries", default="reports/experiment_summaries.json")
    parser.add_argument("--csv-output", default="reports/results.csv")
    parser.add_argument("--markdown-output", default="reports/results.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = _load(args.summaries)
    rows = _rows(summaries)
    write_csv(rows, args.csv_output)
    write_markdown(summaries, rows, args.markdown_output)
    print(f"Wrote {args.markdown_output} and {args.csv_output}.")


if __name__ == "__main__":
    main()
