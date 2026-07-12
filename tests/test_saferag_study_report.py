import json
import tempfile
import unittest
from pathlib import Path

from ragshield.evaluation.saferag_study_report import (
    _p_value,
    build_summary,
    merge_rows,
    write_blind_audit_sample,
    write_markdown,
    write_public_audit,
)
from ragshield.evaluation.saferag_study_protocol import PROTOCOL_VERSION


def generation(system, response_id):
    return {
        "protocol_version": PROTOCOL_VERSION,
        "split": "confirmatory",
        "system": system,
        "task": "SA",
        "case_id": 9,
        "question": "测试问题",
        "requested_model": "gpt-test",
        "response_id": response_id,
        "prompt_hash": "p" * 64,
        "initial_context_hash": "i" * 64,
        "final_context_hash": "f" * 64,
        "answer": f"{system} answer",
        "keyword_metrics": {
            "attack_keyword_ratio": 0.0,
            "attack_keyword_propagated": False,
        },
        "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
        "latency_ms": 10.0,
        "final_context_count": 2,
    }


def judgment(system, response_id, adopted):
    return {
        "protocol_version": PROTOCOL_VERSION,
        "split": "confirmatory",
        "system": system,
        "task": "SA",
        "case_id": 9,
        "generator_model": "gpt-test",
        "judge_model": "gpt-test",
        "response_id": response_id,
        "metrics": {
            "attack_adopted": adopted,
            "attack_evidence": "private benchmark evidence" if adopted else "",
            "attack_mentioned_only": False,
            "refusal": False,
            "grounded": not adopted,
            "option_macro_f1": 0.0 if adopted else 1.0,
        },
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40},
        "latency_ms": 12.0,
    }


class SafeRAGStudyReportTests(unittest.TestCase):
    def test_tiny_p_value_is_not_rendered_as_zero(self):
        self.assertEqual(_p_value(0.0), "<0.0001")
        self.assertEqual(_p_value(0.01234), "0.0123")

    def test_incomplete_case_is_excluded_from_all_system_estimates(self):
        generations = [generation("baseline", "gen_0"), generation("context_boundary", "gen_1")]
        judgments = [
            judgment("baseline", "judge_0", adopted=True),
            judgment("context_boundary", "judge_1", adopted=False),
        ]
        summary = build_summary(generations, judgments, "gpt-test", "gpt-test")
        confirmatory = summary["confirmatory"]
        self.assertEqual(confirmatory["n_available_cases"], 1)
        self.assertEqual(confirmatory["n_cases"], 0)
        self.assertEqual(len(confirmatory["excluded_incomplete_cases"]), 1)
        self.assertEqual(
            confirmatory["excluded_incomplete_cases"][0]["missing_generation_systems"],
            ["ragshield_full"],
        )

    def test_complete_report_and_blind_audit_are_generated(self):
        systems = ["baseline", "context_boundary", "ragshield_full"]
        generations = [generation(system, f"gen_{index}") for index, system in enumerate(systems)]
        judgments = [
            judgment(system, f"judge_{index}", adopted=system == "baseline")
            for index, system in enumerate(systems)
        ]
        summary = build_summary(generations, judgments, "gpt-test", "gpt-test")
        self.assertEqual(summary["confirmatory"]["n_cases"], 1)
        self.assertEqual(summary["execution_evidence"]["initial_context_pair_mismatches"], 0)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.md"
            audit = root / "audit.json"
            blind = root / "blind.csv"
            key = root / "key.jsonl"
            write_markdown(summary, report)
            write_public_audit(generations, judgments, audit)
            write_blind_audit_sample(merge_rows(generations, judgments), blind, key, 1)
            self.assertIn("Confirmatory Results", report.read_text(encoding="utf-8"))
            public = json.loads(audit.read_text(encoding="utf-8"))
            self.assertEqual(len(public["records"]), 3)
            self.assertNotIn("answer", public["records"][0])
            serialized_audit = audit.read_text(encoding="utf-8")
            self.assertNotIn("private benchmark evidence", serialized_audit)
            baseline_metrics = public["records"][0]["judge_metrics"]
            self.assertNotIn("attack_evidence", baseline_metrics)
            self.assertTrue(baseline_metrics["attack_evidence_present"])
            self.assertEqual(len(baseline_metrics["attack_evidence_sha256"]), 64)
            self.assertTrue(blind.exists())
            self.assertTrue(key.exists())


if __name__ == "__main__":
    unittest.main()
