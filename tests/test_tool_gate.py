import unittest
from datetime import datetime, timedelta, timezone

from ragshield.agents.mock_tools import MockToolExecutor
from ragshield.defenses.tool_gate import (
    ApprovalGrant,
    ToolDecisionStatus,
    ToolRequest,
    default_tool_policy,
)
from ragshield.evaluation.tool_metrics import calculate_tool_authorization_metrics


class ToolGateTests(unittest.TestCase):
    def setUp(self):
        self.policy = default_tool_policy()
        self.now = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)

    def test_low_risk_tool_is_allowed_for_authorized_role(self):
        request = ToolRequest("req-1", "search_documents", {"query": "SafeRAG"})
        decision = self.policy.authorize(request, {"researcher"}, now=self.now)
        self.assertEqual(decision.status, ToolDecisionStatus.ALLOWED)

    def test_role_check_denies_before_tool_execution(self):
        request = ToolRequest("req-2", "send_email", {"recipient": "fake@example.test"})
        decision = self.policy.authorize(request, {"researcher"}, now=self.now)
        self.assertEqual(decision.status, ToolDecisionStatus.DENIED)
        self.assertEqual(decision.reason, "role_not_allowed")
        with self.assertRaises(PermissionError):
            MockToolExecutor().execute(request, decision)

    def test_high_risk_tool_requires_scoped_human_approval(self):
        request = ToolRequest("req-3", "export_records", {"record_ids": ["fake-1"]})
        pending = self.policy.authorize(request, {"admin"}, now=self.now)
        self.assertEqual(pending.status, ToolDecisionStatus.APPROVAL_REQUIRED)

        wrong_scope = ApprovalGrant(
            request_id="another-request",
            tool_name="export_records",
            approved=True,
            approved_by="reviewer-1",
            expires_at_utc=self.now + timedelta(minutes=5),
        )
        denied = self.policy.authorize(
            request, {"admin"}, approval=wrong_scope, now=self.now
        )
        self.assertEqual(denied.reason, "approval_scope_mismatch")

        approval = ApprovalGrant(
            request_id=request.request_id,
            tool_name=request.tool_name,
            approved=True,
            approved_by="reviewer-1",
            expires_at_utc=self.now + timedelta(minutes=5),
        )
        allowed = self.policy.authorize(request, {"admin"}, approval=approval, now=self.now)
        result = MockToolExecutor().execute(request, allowed)
        self.assertTrue(allowed.allowed)
        self.assertEqual(result["status"], "simulated_no_side_effect")
        self.assertEqual(result["requested_record_count"], 1)

    def test_expired_approval_is_denied(self):
        request = ToolRequest("req-4", "export_records", {"record_ids": []})
        approval = ApprovalGrant(
            request_id=request.request_id,
            tool_name=request.tool_name,
            approved=True,
            approved_by="reviewer-1",
            expires_at_utc=self.now - timedelta(seconds=1),
        )
        decision = self.policy.authorize(request, {"admin"}, approval=approval, now=self.now)
        self.assertEqual(decision.reason, "approval_expired")

    def test_unknown_tool_is_denied_and_counted(self):
        request = ToolRequest("req-5", "delete_everything", {})
        denied = self.policy.authorize(request, {"admin"}, now=self.now)
        allowed = self.policy.authorize(
            ToolRequest("req-6", "search_documents", {}), {"admin"}, now=self.now
        )
        metrics = calculate_tool_authorization_metrics([denied, allowed])
        self.assertEqual(denied.reason, "unknown_tool")
        self.assertEqual(metrics.unauthorized_tool_call_rate, 0.5)
        self.assertEqual(metrics.decisions_by_reason["unknown_tool"], 1)


if __name__ == "__main__":
    unittest.main()
