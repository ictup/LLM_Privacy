import unittest

from ragshield.evaluation.data_quality import build_quality_report
from ragshield.ingestion.build_attack_sets import build_attack_tests, build_benign_tests, build_mixed_tests
from ragshield.ingestion.build_corpus import generate_corpus


class DatasetQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = [row.to_dict() for row in generate_corpus()]
        cls.attacks = [row.to_dict() for row in build_attack_tests()]
        cls.benign = [row.to_dict() for row in build_benign_tests()]
        cls.mixed = [row.to_dict() for row in build_mixed_tests()]

    def test_has_no_exact_text_or_query_duplicates(self):
        self.assertEqual(len(self.corpus), len({row["text"] for row in self.corpus}))
        all_cases = self.attacks + self.benign + self.mixed
        self.assertEqual(len(all_cases), len({row["user_query"] for row in all_cases}))

    def test_every_target_document_exists(self):
        report = build_quality_report(self.corpus, self.attacks, self.benign, self.mixed)
        self.assertTrue(report["validation_passed"])
        self.assertEqual(report["missing_target_references"], [])

    def test_normalized_text_is_not_single_template(self):
        report = build_quality_report(self.corpus, self.attacks, self.benign, self.mixed)
        self.assertGreaterEqual(report["corpus"]["normalized_unique_rate"], 0.4)
        self.assertGreaterEqual(report["attacks"]["normalized_unique_rate"], 0.75)
        self.assertGreaterEqual(report["benign"]["normalized_unique_rate"], 0.9)
        self.assertGreaterEqual(report["mixed"]["normalized_unique_rate"], 0.9)


if __name__ == "__main__":
    unittest.main()
