import json
import tempfile
import unittest
from pathlib import Path

from ragshield.evaluation.build_interview_report import build_combined_report, write_markdown


class InterviewReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.saferag = json.loads(
            Path("reports/saferag_gpt5mini_results.json").read_text(encoding="utf-8")
        )
        cls.canary = json.loads(
            Path("reports/synthetic_gpt5mini_results.json").read_text(encoding="utf-8")
        )

    def test_combines_frozen_outputs(self) -> None:
        report = build_combined_report(self.saferag, self.canary)

        self.assertEqual(report["saferag"]["complete_confirmatory_cases"], 377)
        self.assertEqual(report["saferag"]["available_confirmatory_cases"], 379)
        self.assertEqual(report["controlled_canary"]["rows"], 612)
        self.assertAlmostEqual(report["saferag"]["full_relative_attack_reduction"], 0.583644)

    def test_markdown_uses_report_case_count(self) -> None:
        report = build_combined_report(self.saferag, self.canary)
        report["saferag"]["complete_confirmatory_cases"] = 123

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            write_markdown(report, output)
            rendered = output.read_text(encoding="utf-8")

        self.assertIn("On 123 complete paired SafeRAG", rendered)


if __name__ == "__main__":
    unittest.main()
