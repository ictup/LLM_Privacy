import unittest

from ragshield.benchmarks.tab import (
    TABDataset,
    TABDocument,
    TABMention,
    evaluate_tab_spans,
)
from ragshield.defenses.privacy_guard import SensitiveFinding


class TABMetricsTests(unittest.TestCase):
    def test_span_metrics_report_coverage_and_over_redaction(self):
        document = TABDocument(
            doc_id="1",
            text="Alice met Bob.",
            dataset_type="test",
            quality_checked=True,
            mentions=(TABMention(0, 5, "PERSON", "DIRECT"),),
        )
        dataset = TABDataset(root=None, manifest={}, documents=(document,))  # type: ignore[arg-type]

        def detector(_):
            return (
                SensitiveFinding("pii", "alice", 0, 5, "hash-a", "[PERSON]"),
                SensitiveFinding("pii", "bob", 10, 13, "hash-b", "[PERSON]"),
            )

        metrics = evaluate_tab_spans(dataset, detector)

        self.assertEqual(metrics.exact_mention_recall, 1.0)
        self.assertEqual(metrics.exact_mention_precision, 0.5)
        self.assertEqual(metrics.full_coverage_recall, 1.0)
        self.assertGreater(metrics.false_positive_character_rate, 0.0)
        self.assertLess(metrics.text_retention_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
