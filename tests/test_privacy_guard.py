import unittest

from ragshield.defenses.privacy_guard import detect_sensitive_data, inspect_and_redact
from ragshield.evaluation.privacy_metrics import calculate_leakage_metrics


class PrivacyGuardTests(unittest.TestCase):
    def test_detects_and_redacts_multiple_sensitive_categories(self):
        text = (
            "Contact researcher@example.test using sk-test-not-real-abc123 "
            "for account ACCT-ALPHA-42."
        )
        decision = inspect_and_redact(text)

        self.assertEqual(decision.categories, ("account", "pii", "secret"))
        self.assertNotIn("researcher@example.test", decision.redacted_text)
        self.assertNotIn("sk-test-not-real-abc123", decision.redacted_text)
        self.assertNotIn("ACCT-ALPHA-42", decision.redacted_text)
        self.assertIn("[REDACTED_EMAIL]", decision.redacted_text)

    def test_detects_system_prompt_canary_without_retaining_plaintext(self):
        canary = "RAGSHIELD_SYSTEM_CANARY_INTERVIEW42"
        findings = detect_sensitive_data(f"Hidden marker: {canary}")

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "system_prompt")
        self.assertNotEqual(findings[0].value_sha256, canary)
        self.assertNotIn(canary, str(findings[0].to_dict()))

    def test_leakage_metric_counts_outputs_not_only_findings(self):
        metrics = calculate_leakage_metrics(
            [
                "A safe answer.",
                "Key: sk-test-not-real-one and ID 000-00-1234.",
                "Canary RAGSHIELD_SYSTEM_CANARY_ABCDEF.",
                "Another safe answer.",
            ]
        )

        self.assertEqual(metrics.total_outputs, 4)
        self.assertEqual(metrics.leaked_outputs, 2)
        self.assertEqual(metrics.leakage_rate, 0.5)
        self.assertEqual(metrics.total_findings, 3)
        self.assertEqual(metrics.findings_by_category["secret"], 1)
        self.assertEqual(metrics.findings_by_category["pii"], 1)
        self.assertEqual(metrics.findings_by_category["system_prompt"], 1)

    def test_empty_study_has_zero_leakage_rate(self):
        metrics = calculate_leakage_metrics([])
        self.assertEqual(metrics.total_outputs, 0)
        self.assertEqual(metrics.leakage_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
