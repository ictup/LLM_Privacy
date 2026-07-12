import unittest

from ragshield.evaluation.metrics import summarize_results


class MetricsTests(unittest.TestCase):
    def test_summarizes_attack_success_rate(self):
        rows = [
            {
                "category": "direct_prompt_injection",
                "score": {
                    "attack_success": True,
                    "leakage": False,
                    "system_prompt_exposure": True,
                    "unauthorized_tool_call": False,
                    "policy_bypass": False,
                    "poisoned_retrieval_influence": False,
                    "benign_success": False,
                    "violations": ["system_prompt_exposure"],
                },
            },
            {
                "category": "direct_prompt_injection",
                "score": {
                    "attack_success": False,
                    "leakage": False,
                    "system_prompt_exposure": False,
                    "unauthorized_tool_call": False,
                    "policy_bypass": False,
                    "poisoned_retrieval_influence": False,
                    "benign_success": False,
                    "violations": [],
                },
            },
        ]
        summary = summarize_results(rows)
        self.assertEqual(summary["attack_success_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
