import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ragshield.benchmarks.saferag import SafeRAGCase
from ragshield.evaluation.run_saferag_llm import (
    build_generation_context,
    build_input,
    run,
    score_attack_keywords,
    summarize,
    write_audit_manifest,
)
from ragshield.generation.openai_responses import (
    ModelResponse,
    OpenAIAPIError,
    OpenAIResponsesClient,
)


def make_case(task: str = "SA") -> SafeRAGCase:
    return SafeRAGCase(
        task=task,
        case_id=7,
        question="测试问题",
        golden_contexts=("可信一", "可信二", "可信三", "可信四"),
        attack_contexts=("攻击一", "攻击二", "攻击三", "攻击四"),
        attack_keywords=("错误结论", "虚假说法"),
        numbered_options=(),
        correct_options=(),
        incorrect_options=(),
    )


class OpenAIResponsesClientTests(unittest.TestCase):
    def test_rejects_partial_text_from_incomplete_response(self):
        def transport(_payload):
            return {
                "id": "resp_incomplete",
                "model": "gpt-5-mini-2025-08-07",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "partial answer"}],
                    }
                ],
                "usage": {"input_tokens": 10, "output_tokens": 512, "total_tokens": 522},
            }

        client = OpenAIResponsesClient(
            model="gpt-5-mini-2025-08-07", api_key="test-only", transport=transport
        )
        with self.assertRaisesRegex(OpenAIAPIError, "status=incomplete"):
            client.generate("instructions", "input")

    def test_parses_response_text_usage_and_identifiers(self):
        captured = []

        def transport(payload):
            captured.append(payload)
            return {
                "id": "resp_test_123",
                "model": "gpt-5.6-luna-2026-07-01",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "真实模型回答"}],
                    }
                ],
                "usage": {"input_tokens": 31, "output_tokens": 9, "total_tokens": 40},
            }

        client = OpenAIResponsesClient(
            model="gpt-5.6-luna", api_key="test-only", transport=transport
        )
        response = client.generate("系统要求", "用户输入")

        self.assertEqual(response.response_id, "resp_test_123")
        self.assertEqual(response.model, "gpt-5.6-luna-2026-07-01")
        self.assertEqual(response.text, "真实模型回答")
        self.assertEqual(response.total_tokens, 40)
        self.assertFalse(captured[0]["store"])
        self.assertEqual(captured[0]["max_output_tokens"], 512)
        self.assertEqual(captured[0]["instructions"], "系统要求")

    def test_production_client_requires_environment_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is not set"):
                OpenAIResponsesClient(model="gpt-5.6-luna")

    def test_structured_response_uses_strict_json_schema(self):
        captured = []

        def transport(payload):
            captured.append(payload)
            return {
                "id": "resp_structured",
                "model": "gpt-5-mini-2025-08-07",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": '{"allowed": false}'}
                        ],
                    }
                ],
                "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14},
            }

        schema = {
            "type": "object",
            "properties": {"allowed": {"type": "boolean"}},
            "required": ["allowed"],
            "additionalProperties": False,
        }
        client = OpenAIResponsesClient(
            model="gpt-5-mini-2025-08-07", api_key="test-only", transport=transport
        )
        result = client.generate_structured("judge", "input", "decision", schema)
        self.assertEqual(result.data, {"allowed": False})
        self.assertEqual(captured[0]["text"]["format"]["type"], "json_schema")
        self.assertTrue(captured[0]["text"]["format"]["strict"])


class SafeRAGRealLLMTests(unittest.TestCase):
    def test_context_selection_is_deterministic(self):
        case = make_case()
        first = build_generation_context(case)
        second = build_generation_context(case)
        self.assertEqual(first, second)
        self.assertCountEqual(first, ["可信一", "可信二", "可信三", "攻击一", "攻击二", "攻击三"])

    def test_sn_uses_three_clean_and_three_attack_contexts(self):
        contexts = build_generation_context(make_case("SN"))
        self.assertEqual(len(contexts), 6)
        self.assertCountEqual(
            contexts,
            ["可信一", "可信二", "可信三", "攻击一", "攻击二", "攻击三"],
        )

    def test_input_marks_retrieved_text_as_documents(self):
        model_input = build_input(make_case(), ["可信一", "攻击一"])
        self.assertIn("<question>\n测试问题\n</question>", model_input)
        self.assertIn('<document id="1">\n可信一\n</document>', model_input)
        self.assertIn('<document id="2">\n攻击一\n</document>', model_input)

    def test_attack_keyword_scoring_uses_official_case_keywords(self):
        metrics = score_attack_keywords(make_case(), "答案含有错误结论，但没有另一项。")
        self.assertTrue(metrics["attack_keyword_propagated"])
        self.assertEqual(metrics["attack_keyword_ratio"], 0.5)
        self.assertEqual(metrics["matched_attack_keywords"], ["错误结论"])

    def test_run_records_two_real_response_rows_and_resumes(self):
        class FakeClient:
            def __init__(self):
                self.calls = []

            def generate(self, instructions, input_text):
                self.calls.append((instructions, input_text))
                return ModelResponse(
                    response_id=f"resp_{len(self.calls)}",
                    model="gpt-test-snapshot",
                    text="回答包含错误结论" if len(self.calls) == 1 else "防御回答",
                    input_tokens=30,
                    output_tokens=10,
                    total_tokens=40,
                    latency_ms=12.5,
                )

        fake = FakeClient()
        dataset = SimpleNamespace(cases={"SA": [make_case()]})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cases.jsonl"
            audit_output = Path(directory) / "audit.json"
            with patch(
                "ragshield.evaluation.run_saferag_llm.load_saferag",
                return_value=dataset,
            ):
                rows = run(
                    root="unused",
                    model="gpt-test",
                    reasoning_effort="low",
                    max_output_tokens=512,
                    tasks=["SA"],
                    limit_per_task=1,
                    output=output,
                    client=fake,
                )
                resumed_rows = run(
                    root="unused",
                    model="gpt-test",
                    reasoning_effort="low",
                    max_output_tokens=512,
                    tasks=["SA"],
                    limit_per_task=1,
                    output=output,
                    client=fake,
                )
            write_audit_manifest(rows, "gpt-test", audit_output)
            audit = __import__("json").loads(audit_output.read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(resumed_rows), 2)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(fake.calls[0][1], fake.calls[1][1])
        self.assertEqual(rows[0]["response_id"], "resp_1")
        self.assertEqual(rows[0]["usage"]["total_tokens"], 40)
        summary = summarize(rows, "gpt-test")
        self.assertEqual(summary["execution_evidence"]["unique_response_ids"], 2)
        self.assertEqual(summary["execution_evidence"]["total_tokens"], 80)
        self.assertEqual(summary["execution_evidence"]["paired_context_hash_mismatches"], 0)
        self.assertEqual(len(audit["records"]), 2)
        self.assertEqual(len(audit["records"][0]["response_id_sha256"]), 64)
        self.assertNotIn("response_id", audit["records"][0])
        self.assertNotIn("answer", audit["records"][0])


if __name__ == "__main__":
    unittest.main()
