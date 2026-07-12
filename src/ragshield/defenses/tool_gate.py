"""Least-privilege authorization for model-requested tool calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolDecisionStatus(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    risk_level: RiskLevel
    allowed_roles: frozenset[str]
    requires_approval: bool = False


@dataclass(frozen=True)
class ToolRequest:
    request_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ApprovalGrant:
    request_id: str
    tool_name: str
    approved: bool
    approved_by: str
    expires_at_utc: datetime


@dataclass(frozen=True)
class ToolDecision:
    request_id: str
    tool_name: str
    status: ToolDecisionStatus
    reason: str
    risk_level: RiskLevel | None
    actor_roles: tuple[str, ...]
    approval_required: bool
    approved_by: str | None = None

    @property
    def allowed(self) -> bool:
        return self.status is ToolDecisionStatus.ALLOWED

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["status"] = self.status.value
        row["risk_level"] = self.risk_level.value if self.risk_level else None
        row["allowed"] = self.allowed
        return row


class ToolPolicy:
    def __init__(self, specs: Iterable[ToolSpec]):
        rows = tuple(specs)
        self.specs = {spec.name: spec for spec in rows}
        if len(self.specs) != len(rows):
            raise ValueError("Tool names must be unique.")

    def authorize(
        self,
        request: ToolRequest,
        actor_roles: Iterable[str],
        approval: ApprovalGrant | None = None,
        now: datetime | None = None,
    ) -> ToolDecision:
        roles = tuple(sorted(set(actor_roles)))
        spec = self.specs.get(request.tool_name)
        if spec is None:
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.DENIED,
                reason="unknown_tool",
                risk_level=None,
                actor_roles=roles,
                approval_required=False,
            )

        if not spec.allowed_roles.intersection(roles):
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.DENIED,
                reason="role_not_allowed",
                risk_level=spec.risk_level,
                actor_roles=roles,
                approval_required=spec.requires_approval,
            )

        if not spec.requires_approval:
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.ALLOWED,
                reason="policy_allow",
                risk_level=spec.risk_level,
                actor_roles=roles,
                approval_required=False,
            )

        if approval is None:
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.APPROVAL_REQUIRED,
                reason="human_approval_required",
                risk_level=spec.risk_level,
                actor_roles=roles,
                approval_required=True,
            )

        if approval.request_id != request.request_id or approval.tool_name != request.tool_name:
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.DENIED,
                reason="approval_scope_mismatch",
                risk_level=spec.risk_level,
                actor_roles=roles,
                approval_required=True,
            )

        current_time = now or datetime.now(timezone.utc)
        if approval.expires_at_utc.tzinfo is None:
            raise ValueError("Approval expiry must be timezone-aware.")
        if approval.expires_at_utc <= current_time:
            reason = "approval_expired"
        elif not approval.approved:
            reason = "approval_denied"
        else:
            return ToolDecision(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolDecisionStatus.ALLOWED,
                reason="human_approval_granted",
                risk_level=spec.risk_level,
                actor_roles=roles,
                approval_required=True,
                approved_by=approval.approved_by,
            )

        return ToolDecision(
            request_id=request.request_id,
            tool_name=request.tool_name,
            status=ToolDecisionStatus.DENIED,
            reason=reason,
            risk_level=spec.risk_level,
            actor_roles=roles,
            approval_required=True,
            approved_by=approval.approved_by,
        )


def default_tool_policy() -> ToolPolicy:
    return ToolPolicy(
        [
            ToolSpec(
                name="search_documents",
                risk_level=RiskLevel.LOW,
                allowed_roles=frozenset({"researcher", "analyst", "admin"}),
            ),
            ToolSpec(
                name="send_email",
                risk_level=RiskLevel.MEDIUM,
                allowed_roles=frozenset({"analyst", "admin"}),
            ),
            ToolSpec(
                name="export_records",
                risk_level=RiskLevel.HIGH,
                allowed_roles=frozenset({"admin"}),
                requires_approval=True,
            ),
        ]
    )
