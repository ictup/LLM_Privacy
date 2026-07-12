"""Regex-based fake PII and secret redaction for synthetic benchmark data."""

from __future__ import annotations

import re
from dataclasses import replace

from ragshield.schemas import RetrievedChunk


REDACTION_RULES = [
    (re.compile(r"FAKE_API_KEY:\s*sk-test-not-real-[A-Za-z0-9_\-]+"), "FAKE_API_KEY: [REDACTED_SECRET]"),
    (re.compile(r"FAKE_PERSON_ID:\s*000-00-\d{4}"), "FAKE_PERSON_ID: [REDACTED_PII]"),
    (re.compile(r"FAKE_TAX_ID:\s*TAX-(?:[A-Z]+-)?\d+"), "FAKE_TAX_ID: [REDACTED_PII]"),
    (re.compile(r"\bACCT-[A-Z]+-\d+\b"), "[REDACTED_ACCOUNT]"),
    (re.compile(r"sk-test-not-real-[A-Za-z0-9_\-]+"), "[REDACTED_SECRET]"),
    (re.compile(r"000-00-\d{4}"), "[REDACTED_PII]"),
    (re.compile(r"TAX-(?:[A-Z]+-)?\d+"), "[REDACTED_PII]"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def contains_sensitive_data(text: str) -> bool:
    return redact_text(text) != text


def redact_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    return [replace(chunk, text=redact_text(chunk.text)) for chunk in chunks]
