import unittest

from ragshield.defenses.pii_redactor import contains_sensitive_data, redact_text


class RedactionTests(unittest.TestCase):
    def test_redacts_fake_api_key(self):
        text = "FAKE_API_KEY: sk-test-not-real-123"
        self.assertEqual(redact_text(text), "FAKE_API_KEY: [REDACTED_SECRET]")

    def test_detects_fake_person_id(self):
        self.assertTrue(contains_sensitive_data("FAKE_PERSON_ID: 000-00-1234"))


if __name__ == "__main__":
    unittest.main()
