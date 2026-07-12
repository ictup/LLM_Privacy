"""Aggregate RAGShield run metrics."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    attacks = [row for row in rows if row["category"] not in {"benign_qa"}]
    benign = [row for row in rows if row["category"] == "benign_qa"]

    by_category: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(row)

    for category, category_rows in grouped.items():
        by_category[category] = {
            "n": len(category_rows),
            "avg_latency_ms": round(
                sum(row.get("latency_ms", 0.0) for row in category_rows) / len(category_rows),
                3,
            ),
            "attack_success_rate": _rate(
                sum(row["score"]["attack_success"] for row in category_rows),
                len(category_rows),
            ),
            "leakage_rate": _rate(sum(row["score"]["leakage"] for row in category_rows), len(category_rows)),
            "unauthorized_tool_call_rate": _rate(
                sum(row["score"]["unauthorized_tool_call"] for row in category_rows),
                len(category_rows),
            ),
        }

    violation_counter: Counter[str] = Counter()
    for row in rows:
        violation_counter.update(row["score"]["violations"])

    return {
        "n": total,
        "attack_n": len(attacks),
        "benign_n": len(benign),
        "avg_latency_ms": round(sum(row.get("latency_ms", 0.0) for row in rows) / total, 3)
        if rows
        else 0.0,
        "attack_success_rate": _rate(
            sum(row["score"]["attack_success"] for row in attacks),
            len(attacks),
        ),
        "leakage_rate": _rate(sum(row["score"]["leakage"] for row in attacks), len(attacks)),
        "system_prompt_exposure_rate": _rate(
            sum(row["score"]["system_prompt_exposure"] for row in attacks),
            len(attacks),
        ),
        "unauthorized_tool_call_rate": _rate(
            sum(row["score"]["unauthorized_tool_call"] for row in attacks),
            len(attacks),
        ),
        "policy_bypass_rate": _rate(sum(row["score"]["policy_bypass"] for row in attacks), len(attacks)),
        "poisoned_retrieval_influence_rate": _rate(
            sum(row["score"]["poisoned_retrieval_influence"] for row in attacks),
            len(attacks),
        ),
        "benign_success_rate": _rate(
            sum(row["score"]["benign_success"] for row in benign),
            len(benign),
        ),
        "violations": dict(sorted(violation_counter.items())),
        "by_category": by_category,
    }
