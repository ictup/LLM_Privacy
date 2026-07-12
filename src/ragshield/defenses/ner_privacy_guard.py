"""Optional local NER layer for broader contextual-identifier redaction."""

from __future__ import annotations

from typing import Any

from ragshield.defenses.privacy_guard import (
    PrivacyDecision,
    SensitiveFinding,
    detect_sensitive_data,
    redact_findings,
    select_non_overlapping_findings,
    sensitive_value_sha256,
)


NER_LABELS = {
    "PERSON": ("pii_person", "[REDACTED_PERSON]"),
    "ORG": ("pii_organization", "[REDACTED_ORGANIZATION]"),
    "GPE": ("pii_location", "[REDACTED_LOCATION]"),
    "LOC": ("pii_location", "[REDACTED_LOCATION]"),
    "FAC": ("pii_location", "[REDACTED_LOCATION]"),
    "DATE": ("quasi_identifier", "[REDACTED_DATETIME]"),
    "TIME": ("quasi_identifier", "[REDACTED_DATETIME]"),
    "NORP": ("quasi_identifier", "[REDACTED_GROUP]"),
    "MONEY": ("quasi_identifier", "[REDACTED_QUANTITY]"),
    "PERCENT": ("quasi_identifier", "[REDACTED_QUANTITY]"),
    "QUANTITY": ("quasi_identifier", "[REDACTED_QUANTITY]"),
    "CARDINAL": ("quasi_identifier", "[REDACTED_QUANTITY]"),
    "ORDINAL": ("quasi_identifier", "[REDACTED_QUANTITY]"),
    "EVENT": ("contextual_identifier", "[REDACTED_CONTEXT]"),
    "LAW": ("contextual_identifier", "[REDACTED_CONTEXT]"),
    "PRODUCT": ("contextual_identifier", "[REDACTED_CONTEXT]"),
}


class SpacyPrivacyGuard:
    """Combine local spaCy entities with deterministic RAGShield secret rules."""

    def __init__(self, nlp: Any, model_name: str = "injected"):
        self.nlp = nlp
        self.model_name = model_name

    @classmethod
    def from_model(cls, model_name: str = "en_core_web_sm") -> "SpacyPrivacyGuard":
        try:
            import spacy
        except ImportError as exc:
            raise RuntimeError("Install the optional 'privacy' dependencies to use NER.") from exc
        return cls(spacy.load(model_name), model_name=model_name)

    def detect(self, text: str) -> tuple[SensitiveFinding, ...]:
        candidates = list(detect_sensitive_data(text))
        candidates.extend(self.detect_entities(text))
        return select_non_overlapping_findings(candidates)

    def detect_entities(self, text: str) -> tuple[SensitiveFinding, ...]:
        candidates = []
        document = self.nlp(text)
        for entity in document.ents:
            mapping = NER_LABELS.get(str(entity.label_))
            if mapping is None:
                continue
            category, replacement = mapping
            candidates.append(
                SensitiveFinding(
                    category=category,
                    rule_id=f"spacy_{str(entity.label_).lower()}",
                    start=int(entity.start_char),
                    end=int(entity.end_char),
                    value_sha256=sensitive_value_sha256(str(entity.text)),
                    replacement=replacement,
                )
            )
        return select_non_overlapping_findings(candidates)

    def inspect_and_redact(self, text: str) -> PrivacyDecision:
        return redact_findings(text, self.detect(text))
