import unittest

from ragshield.agents.tool_policy_gate import ToolPolicyGate


class ToolPolicyGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ToolPolicyGate("configs/tool_policy.yaml")

    def test_user_can_search_docs(self):
        decision = self.gate.authorize("search_docs", "user", {"query": "refund"})
        self.assertTrue(decision.allowed)

    def test_user_cannot_send_email(self):
        decision = self.gate.authorize(
            "send_email",
            "user",
            {"to": "x@example.invalid", "body": "test"},
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "role_not_allowed:user")

    def test_admin_email_requires_approval(self):
        decision = self.gate.authorize(
            "send_email",
            "admin",
            {"to": "x@example.invalid", "body": "test"},
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "approval_required")


if __name__ == "__main__":
    unittest.main()
