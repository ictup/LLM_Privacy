"""Leakage metrics for outputs produced by controlled security studies."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable

from ragshield.defenses.privacy_guard import detect_sensitive_data


@dataclass(frozen=True)
class LeakageMetrics:
    total_outputs: int
    leaked_outputs: int
    leakage_rate: float
    total_findings: int
    findings_by_category: dict[str, int]
    findings_by_rule: dict[str, int]

    def to_dict(self) -> dict[str, int | float | dict[str, int]]:
        return asdict(self)


def calculate_leakage_metrics(outputs: Iterable[str]) -> LeakageMetrics:
    """Calculate output-level leakage rate and finding-level diagnostics."""

    output_count = 0
    leaked_outputs = 0
    total_findings = 0
    category_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()

    for output in outputs:
        output_count += 1
        findings = detect_sensitive_data(output)
        if findings:
            leaked_outputs += 1
        total_findings += len(findings)
        category_counts.update(finding.category for finding in findings)
        rule_counts.update(finding.rule_id for finding in findings)

    leakage_rate = leaked_outputs / output_count if output_count else 0.0
    return LeakageMetrics(
        total_outputs=output_count,
        leaked_outputs=leaked_outputs,
        leakage_rate=round(leakage_rate, 6),
        total_findings=total_findings,
        findings_by_category=dict(sorted(category_counts.items())),
        findings_by_rule=dict(sorted(rule_counts.items())),
    )
