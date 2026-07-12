"""Aggregate authorization metrics for controlled tool-call studies."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable

from ragshield.defenses.tool_gate import ToolDecision, ToolDecisionStatus


@dataclass(frozen=True)
class ToolAuthorizationMetrics:
    total_requests: int
    allowed_requests: int
    denied_requests: int
    approval_required_requests: int
    unauthorized_tool_call_rate: float
    decisions_by_reason: dict[str, int]

    def to_dict(self) -> dict[str, int | float | dict[str, int]]:
        return asdict(self)


def calculate_tool_authorization_metrics(
    decisions: Iterable[ToolDecision],
) -> ToolAuthorizationMetrics:
    rows = list(decisions)
    allowed = sum(row.status is ToolDecisionStatus.ALLOWED for row in rows)
    denied = sum(row.status is ToolDecisionStatus.DENIED for row in rows)
    approval_required = sum(
        row.status is ToolDecisionStatus.APPROVAL_REQUIRED for row in rows
    )
    rate = denied / len(rows) if rows else 0.0
    reasons = Counter(row.reason for row in rows)
    return ToolAuthorizationMetrics(
        total_requests=len(rows),
        allowed_requests=allowed,
        denied_requests=denied,
        approval_required_requests=approval_required,
        unauthorized_tool_call_rate=round(rate, 6),
        decisions_by_reason=dict(sorted(reasons.items())),
    )
