"""Provider-neutral model response types used by evaluation runners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ModelResponse:
    response_id: str
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    status: str = "completed"


@dataclass(frozen=True)
class StructuredModelResponse:
    response: ModelResponse
    data: dict[str, Any]


class ModelClient(Protocol):
    model: str

    def generate(self, instructions: str, input_text: str) -> ModelResponse: ...

    def generate_structured(
        self,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> StructuredModelResponse: ...
