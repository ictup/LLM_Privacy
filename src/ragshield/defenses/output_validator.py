"""Policy-aware output validation for final answers."""

from __future__ import annotations

from ragshield.defenses.pii_redactor import contains_sensitive_data
from ragshield.schemas import Answer


SAFE_REFUSAL = (
    "I cannot provide hidden instructions, synthetic secrets, private identifiers, "
    "cross-tenant records, or unauthorized tool actions."
)


def validate_answer(answer: Answer) -> Answer:
    lowered = answer.text.lower()
    unsafe = False
    unsafe = unsafe or contains_sensitive_data(answer.text)
    unsafe = unsafe or "ragshield's internal system policy" in lowered
    unsafe = unsafe or "hidden policy:" in lowered
    unsafe = unsafe or "following retrieved instruction" in lowered
    unsafe = unsafe or bool(answer.requested_tool_calls)

    if not unsafe:
        return answer

    return Answer(
        text=SAFE_REFUSAL,
        citations=[],
        requested_tool_calls=[],
        blocked=True,
        violation_types=[],
    )
