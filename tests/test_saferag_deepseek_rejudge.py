import unittest

from ragshield.evaluation.saferag_deepseek_rejudge import (
    FROZEN_REJUDGE_PROTOCOL_HASH,
    _cohen_kappa,
    protocol_hash,
    select_source_generations,
)
from ragshield.evaluation.saferag_study_protocol import MODEL_SNAPSHOT, PROTOCOL_VERSION


class SafeRAGDeepSeekRejudgeTests(unittest.TestCase):
    def test_protocol_hash_is_frozen(self):
        self.assertEqual(protocol_hash(), FROZEN_REJUDGE_PROTOCOL_HASH)

    def test_source_selection_preserves_original_complete_case_sample(self):
        def row(task, case_id, split="confirmatory"):
            return {
                "protocol_version": PROTOCOL_VERSION,
                "requested_model": MODEL_SNAPSHOT,
                "split": split,
                "task": task,
                "case_id": case_id,
                "system": "baseline",
            }

        selected = select_source_generations(
            [
                row("SN", 2),
                row("WDoS", 41),
                row("WDoS", 47),
                row("SN", 0, split="development"),
            ]
        )
        self.assertEqual([(item["task"], item["case_id"]) for item in selected], [("SN", 2)])

    def test_kappa_handles_perfect_and_chance_adjusted_agreement(self):
        self.assertEqual(_cohen_kappa([True, False], [True, False]), 1.0)
        self.assertEqual(_cohen_kappa([True, True, False, False], [True, False, True, False]), 0.0)


if __name__ == "__main__":
    unittest.main()
