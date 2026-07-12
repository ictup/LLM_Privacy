import tempfile
import unittest
from pathlib import Path

from ragshield.evaluation.tab_study import write_tab_markdown


class TABStudyReportTests(unittest.TestCase):
    def test_markdown_discloses_offline_claim_boundary(self):
        metrics = {
            "character_f1": 0.6,
            "exact_mention_f1": 0.4,
            "full_coverage_recall": 0.7,
            "overlap_recall": 0.8,
            "false_positive_character_rate": 0.1,
            "text_retention_rate": 0.9,
            "full_coverage_recall_by_type": {"PERSON": 0.5},
        }
        summary = {
            "study": {
                "protocol_version": "tab-test",
                "benchmark_commit": "abc",
                "split": "test",
                "documents": 127,
                "spacy_model": "fake",
            },
            "systems": {
                "regex_rules": metrics,
                "spacy_ner": metrics,
                "combined": metrics,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            write_tab_markdown(summary, output)
            report = output.read_text(encoding="utf-8")

        self.assertIn("LLM API calls: 0", report)
        self.assertIn("not an LLM generation study", report)


if __name__ == "__main__":
    unittest.main()
