import unittest

from ragshield.evaluation.saferag_silver_noise_study import (
    FROZEN_PROTOCOL_HASH,
    PROTOCOL_VERSION,
    normalize_semantic_decisions,
    protocol_hash,
    semantic_screen_metrics,
)
from ragshield.generation.deepseek_chat import DeepSeekAPIError


class SafeRAGSilverNoiseStudyTests(unittest.TestCase):
    def test_protocol_hash_is_frozen(self):
        self.assertEqual(protocol_hash(), FROZEN_PROTOCOL_HASH)

    def test_semantic_decisions_require_every_document_once(self):
        data = {
            "decisions": [
                {
                    "document_id": "D2",
                    "action": "keep",
                    "reason": "corroborated",
                    "confidence": "high",
                },
                {
                    "document_id": "D1",
                    "action": "quarantine",
                    "reason": "unsupported_new_claim",
                    "confidence": "medium",
                },
            ]
        }
        normalized = normalize_semantic_decisions(data, expected_count=2)
        self.assertEqual([item["document_id"] for item in normalized], ["D1", "D2"])

        data["decisions"][1]["document_id"] = "D2"
        with self.assertRaises(DeepSeekAPIError):
            normalize_semantic_decisions(data, expected_count=2)

    def test_screen_metrics_use_labels_only_after_screening(self):
        rows = [
            {
                "protocol_version": PROTOCOL_VERSION,
                "split": "confirmatory",
                "decisions": [
                    {"action": "quarantine"},
                    {"action": "quarantine"},
                    {"action": "keep"},
                    {"action": "keep"},
                    {"action": "keep"},
                    {"action": "quarantine"},
                ],
            }
        ]
        metrics = semantic_screen_metrics(rows, "confirmatory")
        self.assertAlmostEqual(metrics["attack_context_quarantine_recall"], 2 / 3, places=6)
        self.assertAlmostEqual(metrics["clean_context_retention_rate"], 2 / 3, places=6)
        self.assertAlmostEqual(metrics["quarantine_precision"], 2 / 3, places=6)
        self.assertEqual(metrics["mean_contexts_quarantined"], 3.0)


if __name__ == "__main__":
    unittest.main()
