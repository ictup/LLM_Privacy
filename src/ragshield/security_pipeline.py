"""Integrated security-control path for controlled RAG demonstrations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from ragshield.agents.mock_tools import MockToolExecutor
from ragshield.defenses.context_boundary import wrap_chunks
from ragshield.defenses.context_screener import ScreeningDecision, screen_contexts
from ragshield.defenses.pii_redactor import contains_sensitive_data, redact_chunks
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


@dataclass(frozen=True)
class ContextHandlingResult:
    chunks: tuple[RetrievedChunk, ...]
    decisions: tuple[ScreeningDecision, ...]
    input_count: int
    removed_count: int
    redacted_count: int


class RAGShieldSecurityPipeline:
    """Compose tenant retrieval, output privacy, tool policy, and audit controls."""

    def __init__(
        self,
        retriever: TenantIsolatedRetriever,
        audit: SecurityAuditLogger,
        tool_policy: ToolPolicy | None = None,
        tool_executor: MockToolExecutor | None = None,
        privacy_inspector: Callable[[str], PrivacyDecision] = inspect_and_redact,
    ):
        self.retriever = retriever
        self.audit = audit
        self.tool_policy = tool_policy or default_tool_policy()
        self.tool_executor = tool_executor or MockToolExecutor()
        self.privacy_inspector = privacy_inspector

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        chunks, observation = self.retriever.search(
            query=query,
            principal=self.audit.principal,
            top_k=top_k,
        )
        self.audit.log_tenant_retrieval(query, observation)
        return chunks

    def retrieve_and_defend(self, query: str, top_k: int = 5) -> ContextHandlingResult:
        """Apply tenant scope, attack screening, redaction, and context boundaries."""

        chunks = self.retrieve(query, top_k=top_k)
        _, decisions = screen_contexts(query, [chunk.text for chunk in chunks])
        kept = [
            chunk
            for chunk, decision in zip(chunks, decisions, strict=True)
            if decision.kept and "fallback_retained" not in decision.reasons
        ]
        redacted_count = sum(contains_sensitive_data(chunk.text) for chunk in kept)
        protected = wrap_chunks(redact_chunks(kept))
        protected_tuple = tuple(protected)
        self.audit.log_context_defense(
            query,
            tuple(decisions),
            redacted_count,
            tuple(_text_sha256(chunk.text) for chunk in protected_tuple),
        )
        return ContextHandlingResult(
            chunks=protected_tuple,
            decisions=tuple(decisions),
            input_count=len(chunks),
            removed_count=len(chunks) - len(protected_tuple),
            redacted_count=redacted_count,
        )

    def protect_output(self, output: str) -> PrivacyDecision:
        decision = self.privacy_inspector(output)
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


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
