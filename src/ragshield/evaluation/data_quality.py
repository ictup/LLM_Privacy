"""Profile corpus and evaluation-set diversity and validate benchmark references."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ragshield.utils.jsonl import read_jsonl


NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
IDENTIFIER_RE = re.compile(
    r"\b(?:[a-z_]+_\d+|KB-P\d+|ACCT-[A-Z]+-\d+|TAX-[A-Z]+-\d+|INV-\d+|PRJ-\d+)\b",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")


def normalized_signature(text: str) -> str:
    """Remove IDs and numbers so near-template duplicates become visible."""
    value = IDENTIFIER_RE.sub("<id>", text.lower())
    value = NUMBER_RE.sub("<n>", value)
    return " ".join(value.split())


def profile_texts(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    texts = [str(row[field]) for row in rows]
    words = [TOKEN_RE.findall(text.lower()) for text in texts]
    vocabulary = {token for tokens in words for token in tokens}
    token_count = sum(len(tokens) for tokens in words)
    return {
        "rows": len(rows),
        "exact_unique": len(set(texts)),
        "exact_unique_rate": round(len(set(texts)) / len(texts), 4) if texts else 0.0,
        "normalized_unique": len({normalized_signature(text) for text in texts}),
        "normalized_unique_rate": round(
            len({normalized_signature(text) for text in texts}) / len(texts), 4
        )
        if texts
        else 0.0,
        "average_words": round(token_count / len(texts), 1) if texts else 0.0,
        "vocabulary_size": len(vocabulary),
        "type_token_ratio": round(len(vocabulary) / token_count, 4) if token_count else 0.0,
    }


def build_quality_report(
    corpus: list[dict[str, Any]],
    attacks: list[dict[str, Any]],
    benign: list[dict[str, Any]],
    mixed: list[dict[str, Any]],
) -> dict[str, Any]:
    doc_ids = {row["doc_id"] for row in corpus}
    all_cases = attacks + benign + mixed
    targets = [row["retrieval_target_doc"] for row in all_cases if row.get("retrieval_target_doc")]
    missing_targets = sorted(set(targets) - doc_ids)
    metadata_complete = sum(
        bool(row.get("metadata", {}).get("source_type"))
        and bool(row.get("metadata", {}).get("topic"))
        and bool(row.get("metadata", {}).get("created_date"))
        for row in corpus
    )
    return {
        "corpus": profile_texts(corpus, "text"),
        "attacks": profile_texts(attacks, "user_query"),
        "benign": profile_texts(benign, "user_query"),
        "mixed": profile_texts(mixed, "user_query"),
        "domain_counts": dict(sorted(Counter(row["domain"] for row in corpus).items())),
        "category_counts": dict(sorted(Counter(row["category"] for row in attacks).items())),
        "source_type_count": len({row.get("metadata", {}).get("source_type") for row in corpus}),
        "metadata_complete_rate": round(metadata_complete / len(corpus), 4) if corpus else 0.0,
        "target_references": len(targets),
        "missing_target_references": missing_targets,
        "validation_passed": not missing_targets
        and len({row["text"] for row in corpus}) == len(corpus)
        and len({row["user_query"] for row in all_cases}) == len(all_cases),
    }


def write_markdown(report: dict[str, Any], output: str | Path) -> None:
    lines = [
        "# Dataset Quality Report",
        "",
        "The benchmark contains synthetic organizational scenarios only. Diversity metrics are",
        "reported to make template repetition and dataset limitations visible.",
        "",
        "## Diversity",
        "",
        "| Split | Rows | Exact unique | Normalized unique | Avg. words | Vocabulary |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label in ("corpus", "attacks", "benign", "mixed"):
        row = report[label]
        lines.append(
            f"| {label.title()} | {row['rows']} | {row['exact_unique_rate']:.1%} | "
            f"{row['normalized_unique_rate']:.1%} | {row['average_words']:.1f} | "
            f"{row['vocabulary_size']} |"
        )
    lines.extend(
        [
            "",
            "Normalized uniqueness removes document identifiers and numbers before comparison,",
            "so it is stricter than ordinary duplicate detection.",
            "",
            "## Coverage",
            "",
            "| Validation | Result |",
            "|---|---:|",
            f"| Source types | {report['source_type_count']} |",
            f"| Complete document metadata | {report['metadata_complete_rate']:.1%} |",
            f"| Referenced targets | {report['target_references']} |",
            f"| Missing targets | {len(report['missing_target_references'])} |",
            f"| Validation passed | {report['validation_passed']} |",
            "",
            "### Domain Distribution",
            "",
            "| Domain | Documents |",
            "|---|---:|",
        ]
    )
    for domain, count in report["domain_counts"].items():
        lines.append(f"| {domain} | {count} |")
    lines.extend(["", "### Attack Distribution", "", "| Category | Tests |", "|---|---:|"])
    for category, count in report["category_counts"].items():
        lines.append(f"| {category} | {count} |")
    lines.extend(
        [
            "",
            "## Remaining Limitations",
            "",
            "- Scenario combinations are deterministic and authored from controlled templates.",
            "- Fictional English enterprise text does not reproduce every real document style or language.",
            "- The corpus is author-generated component evidence, not an external model leaderboard.",
        ]
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default="data/synthetic_docs/corpus.jsonl")
    parser.add_argument("--attacks", default="data/attacks/all.jsonl")
    parser.add_argument("--benign", default="data/eval_sets/benign_qa.jsonl")
    parser.add_argument("--mixed", default="data/eval_sets/mixed_qa.jsonl")
    parser.add_argument("--json-output", default="reports/data_quality.json")
    parser.add_argument("--markdown-output", default="reports/data_quality.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_quality_report(
        list(read_jsonl(args.corpus)),
        list(read_jsonl(args.attacks)),
        list(read_jsonl(args.benign)),
        list(read_jsonl(args.mixed)),
    )
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.markdown_output)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["validation_passed"]:
        raise SystemExit("Dataset validation failed.")


if __name__ == "__main__":
    main()
