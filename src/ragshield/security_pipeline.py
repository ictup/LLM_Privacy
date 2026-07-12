"""Integrated security-control path for controlled RAG demonstrations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ragshield.agents.mock_tools import MockToolExecutor
from ragshield.defenses.privacy_guard import PrivacyDecision, inspect_and_redact
from ragshield.defenses.tool_gate import (
    ApprovalGrant,
    ToolDecision,
    ToolPolicy,
    ToolRequest,
    default_tool_policy,
)
from ragshield.retrieval.tenant_isolation import TenantIsolatedRetriever
from ragshield.schemas import RetrievedChunk
from ragshield.tracing.security_audit import SecurityAuditLogger


@dataclass(frozen=True)
class ToolHandlingResult:
    decision: ToolDecision
    execution_result: dict[str, Any] | None


class RAGShieldSecurityPipeline:
    """Compose tenant retrieval, output privacy, tool policy, and audit controls."""

    def __init__(
        self,
        retriever: TenantIsolatedRetriever,
        audit: SecurityAuditLogger,
        tool_policy: ToolPolicy | None = None,
        tool_executor: MockToolExecutor | None = None,
    ):
        self.retriever = retriever
        self.audit = audit
        self.tool_policy = tool_policy or default_tool_policy()
        self.tool_executor = tool_executor or MockToolExecutor()

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        chunks, observation = self.retriever.search(
            query=query,
            principal=self.audit.principal,
            top_k=top_k,
        )
        self.audit.log_tenant_retrieval(query, observation)
        return chunks

    def protect_output(self, output: str) -> PrivacyDecision:
        decision = inspect_and_redact(output)
        self.audit.log_privacy_decision("model_output", output, decision)
        return decision

    def handle_tool_request(
        self,
        request: ToolRequest,
        approval: ApprovalGrant | None = None,
        now: datetime | None = None,
    ) -> ToolHandlingResult:
        decision = self.tool_policy.authorize(
            request=request,
            actor_roles=self.audit.principal.roles,
            approval=approval,
            now=now,
        )
        self.audit.log_tool_decision(request, decision)
        result = self.tool_executor.execute(request, decision) if decision.allowed else None
        return ToolHandlingResult(decision=decision, execution_result=result)
