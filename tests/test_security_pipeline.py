import json
import tempfile
import unittest
from pathlib import Path

from ragshield.defenses.tool_gate import ToolRequest
from ragshield.retrieval.tenant_isolation import TenantIsolatedRetriever, TenantPrincipal
from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import Document
from ragshield.security_pipeline import RAGShieldSecurityPipeline
from ragshield.tracing.security_audit import AUDIT_SCHEMA_VERSION, SecurityAuditLogger


class SecurityPipelineTests(unittest.TestCase):
    def test_pipeline_enforces_controls_and_writes_secret_safe_trace(self):
        documents = [
            Document(
                doc_id="alpha-public",
                tenant="tenant-alpha",
                sensitivity="internal",
                contains_pii=False,
                contains_prompt_injection=False,
                trusted_source=True,
                domain="controlled_test",
                title="Alpha plan",
                text="Project Aurora plan for tenant alpha.",
            ),
            Document(
                doc_id="beta-secret",
                tenant="tenant-beta",
                sensitivity="secret",
                contains_pii=True,
                contains_prompt_injection=True,
                trusted_source=False,
                domain="controlled_test",
                title="Beta secret",
                text="Project Aurora private record for tenant beta.",
            ),
        ]
        principal = TenantPrincipal(
            actor_id="alpha-user", tenant_id="tenant-alpha", roles=("researcher",)
        )
        plaintext_secret = "sk-test-not-real-do-not-log"
        plaintext_email = "recipient@example.test"
        raw_query = "Find beta-secret Project Aurora"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "security-trace.jsonl"
            audit = SecurityAuditLogger(
                path,
                case_id="CONTROL-001",
                principal=principal,
                trace_id="trace-control-001",
            )
            pipeline = RAGShieldSecurityPipeline(
                TenantIsolatedRetriever(LexicalVectorStore(documents)), audit
            )

            chunks = pipeline.retrieve(raw_query)
            privacy = pipeline.protect_output(
                f"Send {plaintext_secret} to {plaintext_email}."
            )
            tool = pipeline.handle_tool_request(
                ToolRequest(
                    request_id="tool-1",
                    tool_name="send_email",
                    arguments={"recipient": plaintext_email, "body": plaintext_secret},
                )
            )
            audit.log_metric_summary("privacy", {"leakage_rate": 0.0})

            self.assertEqual([chunk.doc_id for chunk in chunks], ["alpha-public"])
            self.assertNotIn(plaintext_secret, privacy.redacted_text)
            self.assertFalse(tool.decision.allowed)
            self.assertIsNone(tool.execution_result)

            content = path.read_text(encoding="utf-8")
            rows = [json.loads(line) for line in content.splitlines()]
            self.assertEqual([row["sequence"] for row in rows], [1, 2, 3, 4])
            self.assertEqual(
                [row["event_type"] for row in rows],
                [
                    "tenant_retrieval",
                    "privacy_decision",
                    "tool_decision",
                    "metric_summary",
                ],
            )
            self.assertTrue(all(row["schema_version"] == AUDIT_SCHEMA_VERSION for row in rows))
            self.assertNotIn(plaintext_secret, content)
            self.assertNotIn(plaintext_email, content)
            self.assertNotIn(raw_query, content)
            self.assertNotIn("alpha-public", content)
            self.assertEqual(rows[0]["returned_tenant_ids"], ["tenant-alpha"])
            self.assertEqual(rows[2]["decision"]["reason"], "role_not_allowed")


if __name__ == "__main__":
    unittest.main()
