"""Unified, secret-safe audit events for RAGShield security controls."""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from pathlib import Path
from typing import Any

from ragshield.defenses.privacy_guard import PrivacyDecision
from ragshield.defenses.context_screener import ScreeningDecision
from ragshield.defenses.tool_gate import ToolDecision, ToolRequest
from ragshield.retrieval.tenant_isolation import TenantPrincipal, TenantSearchObservation
from ragshield.tracing.logger import AuditLogger


AUDIT_SCHEMA_VERSION = "ragshield.security.audit.v1"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return _sha256(serialized)


class SecurityAuditLogger:
    """Write a sequenced event stream without raw prompts, outputs, or arguments."""

    def __init__(
        self,
        path: str | Path,
        case_id: str,
        principal: TenantPrincipal,
        trace_id: str | None = None,
    ):
        if not case_id.strip():
            raise ValueError("case_id is required.")
        self.logger = AuditLogger(path)
        self.case_id = case_id
        self.principal = principal
        self.trace_id = trace_id or uuid.uuid4().hex
        self._sequence = 0
        self._sequence_lock = threading.Lock()

    def _log(self, event_type: str, component: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._sequence_lock:
            self._sequence += 1
            sequence = self._sequence
            return self.logger.log(
                event_type,
                {
                    "schema_version": AUDIT_SCHEMA_VERSION,
                    "trace_id": self.trace_id,
                    "case_id": self.case_id,
                    "sequence": sequence,
                    "component": component,
                    "actor_id": self.principal.actor_id,
                    "tenant_id": self.principal.tenant_id,
                    **payload,
                },
            )

    def log_tenant_retrieval(
        self,
        query: str,
        observation: TenantSearchObservation,
    ) -> dict[str, Any]:
        return self._log(
            "tenant_retrieval",
            "retrieval",
            {
                "query_sha256": _sha256(query),
                "returned_doc_id_sha256": tuple(
                    _sha256(doc_id) for doc_id in observation.returned_doc_ids
                ),
                "returned_tenant_ids": observation.returned_tenant_ids,
                "cross_tenant_doc_id_sha256": tuple(
                    _sha256(doc_id) for doc_id in observation.cross_tenant_doc_ids
                ),
                "isolated": observation.isolated,
            },
        )

    def log_privacy_decision(
        self,
        stage: str,
        original_text: str,
        decision: PrivacyDecision,
    ) -> dict[str, Any]:
        return self._log(
            "privacy_decision",
            "privacy_guard",
            {
                "stage": stage,
                "input_sha256": _sha256(original_text),
                "redacted_output_sha256": _sha256(decision.redacted_text),
                "contains_sensitive_data": decision.contains_sensitive_data,
                "categories": decision.categories,
                "finding_count": len(decision.findings),
                "findings": [finding.to_dict() for finding in decision.findings],
            },
        )

    def log_context_defense(
        self,
        query: str,
        decisions: tuple[ScreeningDecision, ...],
        redacted_count: int,
        output_hashes: tuple[str, ...],
    ) -> dict[str, Any]:
        return self._log(
            "context_defense",
            "context_pipeline",
            {
                "query_sha256": _sha256(query),
                "input_count": len(decisions),
                "kept_count": len(output_hashes),
                "removed_count": len(decisions) - len(output_hashes),
                "redacted_count": redacted_count,
                "decisions": [
                    {
                        "context_hash": decision.context_hash,
                        "kept": decision.kept and "fallback_retained" not in decision.reasons,
                        "reasons": decision.reasons,
                        "relevance": decision.relevance,
                    }
                    for decision in decisions
                ],
                "output_sha256": output_hashes,
                "untrusted_boundary_applied": True,
            },
        )

    def log_tool_decision(
        self,
        request: ToolRequest,
        decision: ToolDecision,
    ) -> dict[str, Any]:
        return self._log(
            "tool_decision",
            "tool_gate",
            {
                "request_id": request.request_id,
                "tool_name": request.tool_name,
                "argument_keys": tuple(sorted(request.arguments)),
                "arguments_sha256": _canonical_sha256(request.arguments),
                "decision": decision.to_dict(),
            },
        )

    def log_metric_summary(
        self,
        metric_family: str,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        return self._log(
            "metric_summary",
            "evaluation",
            {"metric_family": metric_family, "metrics": metrics},
        )
