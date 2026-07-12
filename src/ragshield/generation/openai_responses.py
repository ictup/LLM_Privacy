"""Small Responses API client that reads credentials only from the process environment."""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from ragshield.generation.types import ModelResponse, StructuredModelResponse


DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAIAPIError(RuntimeError):
    """Raised for sanitized Responses API failures."""


def _output_text(payload: dict[str, Any]) -> str:
    parts = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


class OpenAIResponsesClient:
    def __init__(
        self,
        model: str,
        reasoning_effort: str = "low",
        timeout_seconds: int = 120,
        max_retries: int = 5,
        max_output_tokens: int = 512,
        api_key: str | None = None,
        transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        self.transport = transport
        if not self.api_key and transport is None:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Use a process environment variable; "
                "never place an API key in source code, config, reports, or command arguments."
            )

    def generate(self, instructions: str, input_text: str) -> ModelResponse:
        return self._generate(instructions, input_text)

    def generate_structured(
        self,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> StructuredModelResponse:
        response = self._generate(
            instructions,
            input_text,
            text_format={
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        )
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as error:
            raise OpenAIAPIError("Structured response was not valid JSON.") from error
        if not isinstance(data, dict):
            raise OpenAIAPIError("Structured response must be a JSON object.")
        return StructuredModelResponse(response=response, data=data)

    def _generate(
        self,
        instructions: str,
        input_text: str,
        text_format: dict[str, Any] | None = None,
    ) -> ModelResponse:
        request_payload = {
            "model": self.model,
            "reasoning": {"effort": self.reasoning_effort},
            "instructions": instructions,
            "input": input_text,
            "max_output_tokens": self.max_output_tokens,
            "store": False,
        }
        if text_format is not None:
            request_payload["text"] = {"format": text_format}
        started = time.perf_counter()
        payload = (
            self.transport(request_payload) if self.transport else self._request(request_payload)
        )
        status = str(payload.get("status", "completed"))
        if status != "completed":
            details = payload.get("incomplete_details") or {}
            reason = str(details.get("reason", "not provided"))
            raise OpenAIAPIError(
                f"Responses API did not complete (status={status}, reason={reason})."
            )
        text = _output_text(payload)
        if not text:
            status = str(payload.get("status", "unknown"))
            details = payload.get("incomplete_details") or {}
            reason = str(details.get("reason", "not provided"))
            raise OpenAIAPIError(
                f"Responses API returned no output text (status={status}, reason={reason})."
            )
        usage = payload.get("usage", {})
        return ModelResponse(
            response_id=str(payload.get("id", "")),
            model=str(payload.get("model", self.model)),
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            status=status,
        )

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                f"{self.base_url}/responses",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                response_text = error.read().decode("utf-8", errors="replace")
                message = _safe_error_message(response_text)
                retryable = error.code in {408, 409, 429, 500, 502, 503, 504}
                if retryable and attempt < self.max_retries:
                    time.sleep(_retry_delay(attempt, error.headers.get("Retry-After")))
                    continue
                raise OpenAIAPIError(f"OpenAI API HTTP {error.code}: {message}") from error
            except urllib.error.URLError as error:
                if attempt < self.max_retries:
                    time.sleep(_retry_delay(attempt))
                    continue
                raise OpenAIAPIError(f"OpenAI API connection failed: {error.reason}") from error
        raise OpenAIAPIError("OpenAI API request failed after retries.")


def _safe_error_message(response_text: str) -> str:
    try:
        payload = json.loads(response_text)
        return str(payload.get("error", {}).get("message", "request failed"))[:500]
    except json.JSONDecodeError:
        return "request failed"


def _retry_delay(attempt: int, retry_after: str | None = None) -> float:
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), 30.0)
        except ValueError:
            pass
    return min(2**attempt, 12) + random.uniform(0.0, 0.75)
