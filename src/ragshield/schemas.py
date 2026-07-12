"""Shared data structures used across the RAGShield prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    doc_id: str
    tenant: str
    sensitivity: str
    contains_pii: bool
    contains_prompt_injection: bool
    trusted_source: bool
    domain: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def tenant_id(self) -> str:
        """Explicit alias used by tenant-isolated security interfaces."""

        return self.tenant

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    title: str
    tenant: str
    sensitivity: str
    trusted_source: bool
    contains_pii: bool
    contains_prompt_injection: bool
    domain: str
    text: str
    score: float
    unsafe_reasons: list[str] = field(default_factory=list)

    @property
    def tenant_id(self) -> str:
        return self.tenant

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[str]
    requested_tool_calls: list[dict[str, Any]] = field(default_factory=list)
    blocked: bool = False
    violation_types: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
