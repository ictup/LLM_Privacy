"""Deterministic privacy controls for controlled RAGShield security tests."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Iterable, Pattern


@dataclass(frozen=True)
class SensitiveFinding:
    """A sensitive span represented without retaining its plaintext value."""

    category: str
    rule_id: str
    start: int
    end: int
    value_sha256: str
    replacement: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class PrivacyDecision:
    redacted_text: str
    findings: tuple[SensitiveFinding, ...]

    @property
    def contains_sensitive_data(self) -> bool:
        return bool(self.findings)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({finding.category for finding in self.findings}))


@dataclass(frozen=True)
class _PrivacyRule:
    rule_id: str
    category: str
    pattern: Pattern[str]
    replacement: str


PRIVACY_RULES = (
    _PrivacyRule(
        "system_prompt_canary",
        "system_prompt",
        re.compile(r"\bRAGSHIELD_SYSTEM_CANARY_[A-Z0-9_-]{6,}\b"),
        "[REDACTED_SYSTEM_PROMPT_CANARY]",
    ),
    _PrivacyRule(
        "fake_api_key",
        "secret",
        re.compile(r"\bsk-test-not-real-[A-Za-z0-9_-]{3,}\b"),
        "[REDACTED_SECRET]",
    ),
    _PrivacyRule(
        "fake_bearer_token",
        "secret",
        re.compile(r"\bRAGSHIELD_TOKEN_[A-Z0-9_-]{6,}\b"),
        "[REDACTED_SECRET]",
    ),
    _PrivacyRule(
        "fake_person_id",
        "pii",
        re.compile(r"\b000-00-\d{4}\b"),
        "[REDACTED_PII]",
    ),
    _PrivacyRule(
        "fake_tax_id",
        "pii",
        re.compile(r"\bTAX-(?:[A-Z]+-)?\d+\b"),
        "[REDACTED_PII]",
    ),
    _PrivacyRule(
        "fake_account_id",
        "account",
        re.compile(r"\bACCT-[A-Z]+-\d+\b"),
        "[REDACTED_ACCOUNT]",
    ),
    _PrivacyRule(
        "email_address",
        "pii",
        re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"),
        "[REDACTED_EMAIL]",
    ),
    _PrivacyRule(
        "fake_phone_number",
        "pii",
        re.compile(r"(?<!\d)\+?358[- ]?000[- ]?\d{4,7}(?!\d)"),
        "[REDACTED_PHONE]",
    ),
)


def sensitive_value_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def select_non_overlapping_findings(
    candidates: Iterable[SensitiveFinding],
) -> tuple[SensitiveFinding, ...]:
    """Prefer the longest finding when multiple detectors return overlapping spans."""

    ordered = sorted(candidates, key=lambda finding: (finding.start, -(finding.end - finding.start)))
    findings: list[SensitiveFinding] = []
    occupied_until = -1
    for finding in ordered:
        if finding.start < occupied_until:
            continue
        findings.append(finding)
        occupied_until = finding.end
    return tuple(findings)


def detect_sensitive_data(text: str) -> tuple[SensitiveFinding, ...]:
    """Detect non-overlapping controlled-test secrets and PII markers."""

    candidates: list[SensitiveFinding] = []
    for rule in PRIVACY_RULES:
        for match in rule.pattern.finditer(text):
            candidates.append(
                SensitiveFinding(
                    category=rule.category,
                    rule_id=rule.rule_id,
                    start=match.start(),
                    end=match.end(),
                    value_sha256=sensitive_value_sha256(match.group(0)),
                    replacement=rule.replacement,
                )
            )
    return select_non_overlapping_findings(candidates)


def redact_findings(
    text: str,
    findings: Iterable[SensitiveFinding],
) -> PrivacyDecision:
    selected = select_non_overlapping_findings(findings)
    if not selected:
        return PrivacyDecision(redacted_text=text, findings=())

    pieces: list[str] = []
    cursor = 0
    for finding in selected:
        if not 0 <= finding.start < finding.end <= len(text):
            raise ValueError(f"Sensitive finding is outside the text boundary: {finding}")
        pieces.append(text[cursor : finding.start])
        pieces.append(finding.replacement)
        cursor = finding.end
    pieces.append(text[cursor:])
    return PrivacyDecision(redacted_text="".join(pieces), findings=selected)


def inspect_and_redact(text: str) -> PrivacyDecision:
    """Return redacted text plus safe metadata describing every finding."""

    return redact_findings(text, detect_sensitive_data(text))
