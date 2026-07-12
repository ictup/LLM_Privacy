"""Generate failure-case analysis from experiment result JSONL files."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from ragshield.defenses.pii_redactor import redact_text
from ragshield.evaluation.run_experiments import EXPERIMENTS
from ragshield.utils.jsonl import read_jsonl


def _load_failures(report_dir: Path) -> dict[str, list[dict]]:
    failures: dict[str, list[dict]] = {}
    for display_name, slug, _config in EXPERIMENTS:
        path = report_dir / f"{slug}_results.jsonl"
        if not path.exists():
            continue
        rows = list(read_jsonl(path))
        failures[display_name] = [
            row
            for row in rows
            if row["category"] != "benign_qa" and row["score"]["attack_success"]
        ]
    return failures


def _example(row: dict) -> str:
    retrieved = ", ".join(row["score"]["retrieved_doc_ids"][:5])
    violations = ", ".join(row["score"]["violations"]) or "none"
    answer = redact_text(row["answer"]["text"])
    answer = answer.replace(
        "You are RAGShield's internal system policy.",
        "[SYNTHETIC_HIDDEN_POLICY].",
    )
    return (
        f"- `{row['test_id']}` / `{row['category']}`: violations={violations}; "
        f"retrieved={retrieved}; answer={answer[:180]!r}"
    )


def write_failure_report(report_dir: Path, output: Path) -> None:
    failures = _load_failures(report_dir)
    lines = [
        "# RAGShield Failure Case Analysis",
        "",
        "This analysis is based on synthetic experiment outputs. It is intended to identify",
        "residual weaknesses and research questions, not to claim real-world security proof.",
        "",
        "## Residual Failures by System",
        "",
    ]

    for system, rows in failures.items():
        counts = Counter(row["category"] for row in rows)
        lines.append(f"### {system}")
        lines.append("")
        if not rows:
            lines.append("No attack-success failures were observed in this synthetic run.")
            lines.append("")
            continue
        lines.append("| Category | Failures |")
        lines.append("|---|---:|")
        for category, count in sorted(counts.items()):
            lines.append(f"| {category} | {count} |")
        lines.append("")
        lines.append("Representative examples:")
        lines.append("")
        by_category: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_category[row["category"]].append(row)
        for category in sorted(by_category):
            lines.append(_example(by_category[category][0]))
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- The baseline fails broadly because it treats user and retrieved instructions as",
            "  trustworthy and does not enforce privacy or tool boundaries.",
            "- Context separation blocks direct leakage and unsafe tool behavior in this toy",
            "  setup, but poisoned documents can still influence citations and evidence choice.",
            "- Retrieval sanitization and redaction reduce specific leakage paths but do not",
            "  replace tenant-level access control and final output validation.",
            "- Full RAGShield succeeds in this benchmark because tenant filtering, context",
            "  boundaries, sanitization, redaction, tool gating, and output validation are combined.",
            "",
            "## Remaining Research Questions",
            "",
            "1. How can a RAG system distinguish malicious retrieved instructions from legitimate",
            "   procedural content without over-filtering useful evidence?",
            "2. How should retrieval systems quantify source trust, tenant isolation, and poisoning",
            "   risk before generation?",
            "3. Can output validators detect paraphrased secret leakage and policy leakage, not only",
            "   regex-obvious synthetic markers?",
            "4. How can least-privilege tool policies be learned, verified, and audited for complex",
            "   multi-step agents?",
            "5. What is the best way to preserve benign utility when defenses become less rule-based",
            "   and the benchmark moves from synthetic templates to realistic documents?",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="reports")
    parser.add_argument("--output", default="reports/failure_cases.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_failure_report(Path(args.report_dir), Path(args.output))
    print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main()
