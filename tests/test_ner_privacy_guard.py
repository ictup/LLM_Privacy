import unittest
from dataclasses import dataclass

from ragshield.defenses.ner_privacy_guard import SpacyPrivacyGuard


@dataclass
class FakeEntity:
    text: str
    start_char: int
    end_char: int
    label_: str


@dataclass
class FakeDocument:
    ents: list[FakeEntity]


class FakeNLP:
    def __call__(self, text: str) -> FakeDocument:
        person = "Jane Doe"
        organization = "Example Hospital"
        return FakeDocument(
            [
                FakeEntity(
                    person,
                    text.index(person),
                    text.index(person) + len(person),
                    "PERSON",
                ),
                FakeEntity(
                    organization,
                    text.index(organization),
                    text.index(organization) + len(organization),
                    "ORG",
                ),
            ]
        )


class NERPrivacyGuardTests(unittest.TestCase):
    def test_combines_ner_entities_and_deterministic_secrets(self):
        text = (
            "Jane Doe works at Example Hospital. "
            "Contact jane@example.test with sk-test-not-real-demo."
        )
        guard = SpacyPrivacyGuard(FakeNLP())
        decision = guard.inspect_and_redact(text)

        self.assertNotIn("Jane Doe", decision.redacted_text)
        self.assertNotIn("Example Hospital", decision.redacted_text)
        self.assertNotIn("jane@example.test", decision.redacted_text)
        self.assertNotIn("sk-test-not-real-demo", decision.redacted_text)
        self.assertEqual(len(decision.findings), 4)
        self.assertIn("pii_person", decision.categories)
        self.assertIn("pii_organization", decision.categories)
        self.assertIn("secret", decision.categories)


if __name__ == "__main__":
    unittest.main()
