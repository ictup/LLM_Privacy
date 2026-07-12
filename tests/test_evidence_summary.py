import unittest

from ragshield.evaluation.build_evidence_summary import build_summary


class EvidenceSummaryTests(unittest.TestCase):
    def test_committed_evidence_is_complete_and_consistent(self):
        summary = build_summary("reports")

        self.assertTrue(summary["all_integrity_checks_passed"])
        self.assertEqual(summary["evidence_totals"]["external_benchmarks"], 4)
        self.assertEqual(summary["evidence_totals"]["external_evaluated_units"], 654)
        self.assertEqual(
            summary["evidence_totals"]["real_model_response_ids_in_deepseek_pilots"],
            1200,
        )

    def test_summary_preserves_negative_tradeoffs(self):
        summary = build_summary("reports")
        privacy = {
            row["system"]: row for row in summary["ablations"]["privacylens"]
        }
        tab = {row["system"]: row for row in summary["ablations"]["tab"]}

        self.assertLess(
            privacy["ragshield_full"]["utility_value"],
            privacy["baseline"]["utility_value"],
        )
        self.assertLess(tab["combined"]["utility_value"], tab["regex_rules"]["utility_value"])


if __name__ == "__main__":
    unittest.main()
