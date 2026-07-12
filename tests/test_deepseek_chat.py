import unittest

from ragshield.generation.deepseek_chat import DeepSeekAPIError, DeepSeekChatClient


def response_payload(text: str = "ok") -> dict:
    return {
        "id": "response-test",
        "model": "deepseek-v4-flash",
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
    }


class DeepSeekChatClientTests(unittest.TestCase):
    def test_generate_disables_thinking_and_maps_usage(self):
        requests = []

        def transport(payload):
            requests.append(payload)
            return response_payload("answer")

        client = DeepSeekChatClient(transport=transport)
        response = client.generate("system", "question")

        self.assertEqual(response.text, "answer")
        self.assertEqual(response.total_tokens, 14)
        self.assertEqual(requests[0]["thinking"], {"type": "disabled"})
        self.assertNotIn("DEEPSEEK_API_KEY", str(requests[0]))

    def test_structured_output_checks_required_fields_and_types(self):
        client = DeepSeekChatClient(
            transport=lambda _: response_payload('{"blocked": true, "reason": "policy"}')
        )
        result = client.generate_structured(
            "Return JSON.",
            "input",
            "decision",
            {
                "type": "object",
                "properties": {
                    "blocked": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["blocked", "reason"],
                "additionalProperties": False,
            },
        )
        self.assertTrue(result.data["blocked"])

    def test_structured_output_rejects_wrong_shape(self):
        client = DeepSeekChatClient(
            transport=lambda _: response_payload('{"blocked": "yes"}'), max_retries=0
        )
        with self.assertRaises(DeepSeekAPIError):
            client.generate_structured(
                "Return JSON.",
                "input",
                "decision",
                {
                    "type": "object",
                    "properties": {"blocked": {"type": "boolean"}},
                    "required": ["blocked"],
                    "additionalProperties": False,
                },
            )

    def test_empty_output_is_retried(self):
        responses = iter([response_payload(""), response_payload("answer")])
        client = DeepSeekChatClient(
            transport=lambda _: next(responses), max_retries=1, sleep=lambda _: None
        )

        self.assertEqual(client.generate("system", "question").text, "answer")

    def test_invalid_structured_output_is_retried(self):
        responses = iter([response_payload("not-json"), response_payload('{"blocked": true}')])
        client = DeepSeekChatClient(
            transport=lambda _: next(responses), max_retries=1, sleep=lambda _: None
        )

        result = client.generate_structured(
            "Return JSON.",
            "input",
            "decision",
            {
                "type": "object",
                "properties": {"blocked": {"type": "boolean"}},
                "required": ["blocked"],
                "additionalProperties": False,
            },
        )

        self.assertTrue(result.data["blocked"])

    def test_missing_key_is_rejected_before_network_use(self):
        with self.assertRaisesRegex(RuntimeError, "DEEPSEEK_API_KEY"):
            DeepSeekChatClient(api_key="")


if __name__ == "__main__":
    unittest.main()
