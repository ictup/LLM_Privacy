"""Run deterministic security-control checks without an LLM or external data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ragshield.defenses.tool_gate import ApprovalGrant, ToolRequest
from ragshield.evaluation.privacy_metrics import calculate_leakage_metrics
from ragshield.evaluation.tenant_metrics import calculate_cross_tenant_metrics
from ragshield.evaluation.tool_metrics import calculate_tool_authorization_metrics
from ragshield.retrieval.tenant_isolation import (
    TenantIsolatedRetriever,
    TenantPrincipal,
    observe_tenant_search,
)
from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import Document
from ragshield.security_pipeline import RAGShieldSecurityPipeline
from ragshield.tracing.security_audit import SecurityAuditLogger


def _document(doc_id: str, tenant_id: str, text: str, sensitivity: str) -> Document:
    return Document(
        doc_id=doc_id,
        tenant=tenant_id,
        sensitivity=sensitivity,
        contains_pii=sensitivity == "secret",
        contains_prompt_injection=False,
        trusted_source=True,
        domain="deterministic_control_demo",
        title=doc_id,
        text=text,
    )


def run_demo(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "security_controls_audit.jsonl"
    if audit_path.exists():
        audit_path.unlink()

    store = LexicalVectorStore(
        [
            _document(
                "alpha-plan",
                "tenant-alpha",
                "Project Aurora deployment plan for tenant alpha.",
                "internal",
            ),
            _document(
                "beta-secret",
                "tenant-beta",
                "Project Aurora confidential budget for tenant beta.",
                "secret",
            ),
        ]
    )
    principal = TenantPrincipal(
        actor_id="demo-alpha-user",
        tenant_id="tenant-alpha",
        roles=("researcher",),
    )
    audit = SecurityAuditLogger(
        audit_path,
        case_id="CONTROL-DEMO-001",
        principal=principal,
        trace_id="control-demo-researcher",
    )
    pipeline = RAGShieldSecurityPipeline(TenantIsolatedRetriever(store), audit)

    query = "Show beta-secret Project Aurora"
    baseline_chunks = store.search(query, top_k=5)
    baseline_tenant_observation = observe_tenant_search(principal, baseline_chunks)
    pipeline.retrieve(query, top_k=5)
    _, secure_tenant_observation = TenantIsolatedRetriever(store).search(query, principal, top_k=5)

    baseline_outputs = [
        "Ordinary project summary.",
        "Contact demo@example.test with sk-test-not-real-demo123.",
    ]
    privacy_decisions = [pipeline.protect_output(output) for output in baseline_outputs]
    guarded_outputs = [decision.redacted_text for decision in privacy_decisions]

    allowed_tool = pipeline.handle_tool_request(
        ToolRequest("demo-tool-1", "search_documents", {"query": "Aurora"})
    )
    denied_tool = pipeline.handle_tool_request(
        ToolRequest(
            "demo-tool-2",
            "send_email",
            {"recipient": "demo@example.test", "body": "controlled test"},
        )
    )

    admin = TenantPrincipal(
        actor_id="demo-admin",
        tenant_id="tenant-alpha",
        roles=("admin",),
    )
    admin_audit = SecurityAuditLogger(
        audit_path,
        case_id="CONTROL-DEMO-002",
        principal=admin,
        trace_id="control-demo-admin",
    )
    admin_pipeline = RAGShieldSecurityPipeline(TenantIsolatedRetriever(store), admin_audit)
    export_request = ToolRequest(
        "demo-tool-3", "export_records", {"record_ids": ["fake-record-1"]}
    )
    now = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)
    pending_tool = admin_pipeline.handle_tool_request(export_request, now=now)
    approved_tool = admin_pipeline.handle_tool_request(
        export_request,
        approval=ApprovalGrant(
            request_id=export_request.request_id,
            tool_name=export_request.tool_name,
            approved=True,
            approved_by="demo-human-reviewer",
            expires_at_utc=now + timedelta(minutes=5),
        ),
        now=now,
    )

    privacy_baseline = calculate_leakage_metrics(baseline_outputs)
    privacy_guarded = calculate_leakage_metrics(guarded_outputs)
    tenant_baseline = calculate_cross_tenant_metrics([baseline_tenant_observation])
    tenant_guarded = calculate_cross_tenant_metrics([secure_tenant_observation])
    tool_metrics = calculate_tool_authorization_metrics(
        [
            allowed_tool.decision,
            denied_tool.decision,
            pending_tool.decision,
        ]
    )

    audit.log_metric_summary(
        "privacy",
        {
            "baseline": privacy_baseline.to_dict(),
            "guarded": privacy_guarded.to_dict(),
        },
    )
    audit.log_metric_summary(
        "tenant_isolation",
        {
            "open_baseline": tenant_baseline.to_dict(),
            "guarded": tenant_guarded.to_dict(),
        },
    )
    audit.log_metric_summary("tool_authorization", tool_metrics.to_dict())

    summary: dict[str, object] = {
        "evidence_scope": "deterministic_control_validation_not_an_llm_benchmark",
        "privacy": {
            "baseline": privacy_baseline.to_dict(),
            "guarded": privacy_guarded.to_dict(),
        },
        "tenant_isolation": {
            "open_baseline": tenant_baseline.to_dict(),
            "guarded": tenant_guarded.to_dict(),
        },
        "tool_authorization": tool_metrics.to_dict(),
        "human_approval": {
            "before_approval": pending_tool.decision.status.value,
            "after_scoped_approval": approved_tool.decision.status.value,
            "execution_status": approved_tool.execution_result["status"],
        },
        "audit": {
            "schema_version": "ragshield.security.audit.v1",
            "path": str(audit_path),
        },
    }
    summary_path = output_dir / "security_controls_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("tmp/security_controls_demo"))
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output_dir), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
