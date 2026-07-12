"""Minimal DeepSeek Chat Completions client with resumable-run friendly errors."""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from ragshield.generation.types import ModelResponse, StructuredModelResponse


DEFAULT_BASE_URL = "https://api.deepseek.com"
FLASH_MODEL = "deepseek-v4-flash"
PRO_MODEL = "deepseek-v4-pro"


class DeepSeekAPIError(RuntimeError):
    """Raised with sanitized details when a DeepSeek request cannot complete."""


class DeepSeekChatClient:
    def __init__(
        self,
        model: str = FLASH_MODEL,
        *,
        thinking: bool = False,
        temperature: float = 0.0,
        timeout_seconds: int = 120,
        max_retries: int = 5,
        max_output_tokens: int = 512,
        api_key: str | None = None,
        transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.model = model
        self.thinking = thinking
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        self.transport = transport
        self.sleep = sleep
        if not self.api_key and transport is None:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. Load it into the process environment; "
                "never place an API key in source code, reports, or command arguments."
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
        schema_prompt = (
            f"\nReturn one valid JSON object for schema {schema_name}. "
            "Do not include markdown or additional text. The required JSON schema is:\n"
            f"{json.dumps(schema, ensure_ascii=False, sort_keys=True)}"
        )
        last_error: DeepSeekAPIError | None = None
        for attempt in range(self.max_retries + 1):
            response = self._generate(
                instructions + schema_prompt,
                input_text,
                response_format={"type": "json_object"},
            )
            try:
                data = json.loads(response.text)
                if not isinstance(data, dict):
                    raise DeepSeekAPIError("Structured response must be a JSON object.")
                _validate_required_shape(data, schema)
                return StructuredModelResponse(response=response, data=data)
            except json.JSONDecodeError as error:
                last_error = DeepSeekAPIError("Structured response was not valid JSON.")
                last_error.__cause__ = error
            except DeepSeekAPIError as error:
                last_error = error
            if attempt < self.max_retries:
                self.sleep(_retry_delay(attempt))
        assert last_error is not None
        raise last_error

    def _generate(
        self,
        instructions: str,
        input_text: str,
        response_format: dict[str, str] | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "max_tokens": self.max_output_tokens,
            "stream": False,
            "temperature": self.temperature,
            "thinking": {"type": "enabled" if self.thinking else "disabled"},
        }
        if response_format is not None:
            payload["response_format"] = response_format
        started = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            body = self.transport(payload) if self.transport else self._request(payload)
            choices = body.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                usage = body.get("usage") or {}
                input_tokens = int(usage.get("prompt_tokens", 0))
                output_tokens = int(usage.get("completion_tokens", 0))
                return ModelResponse(
                    response_id=str(body.get("id", "")),
                    model=str(body.get("model", self.model)),
                    text=content.strip(),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=int(usage.get("total_tokens", input_tokens + output_tokens)),
                    latency_ms=round((time.perf_counter() - started) * 1000, 3),
                    status="completed",
                )
            if attempt < self.max_retries:
                self.sleep(_retry_delay(attempt))
        raise DeepSeekAPIError("DeepSeek returned no output content after retries.")

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                f"{self.base_url}/chat/completions",
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
                    self.sleep(_retry_delay(attempt, error.headers.get("Retry-After")))
                    continue
                raise DeepSeekAPIError(f"DeepSeek API HTTP {error.code}: {message}") from error
            except urllib.error.URLError as error:
                if attempt < self.max_retries:
                    self.sleep(_retry_delay(attempt))
                    continue
                raise DeepSeekAPIError(f"DeepSeek API connection failed: {error.reason}") from error
        raise DeepSeekAPIError("DeepSeek API request failed after retries.")


def _validate_required_shape(data: dict[str, Any], schema: dict[str, Any]) -> None:
    missing = [key for key in schema.get("required", []) if key not in data]
    if missing:
        raise DeepSeekAPIError(f"Structured response omitted required fields: {missing}")
    properties = schema.get("properties", {})
    for key, value in data.items():
        specification = properties.get(key)
        if specification is None:
            if schema.get("additionalProperties") is False:
                raise DeepSeekAPIError(f"Structured response included unknown field: {key}")
            continue
        expected = specification.get("type")
        if expected and not _matches_json_type(value, expected):
            raise DeepSeekAPIError(f"Structured response field {key!r} was not {expected}.")
        if "enum" in specification and value not in specification["enum"]:
            raise DeepSeekAPIError(f"Structured response field {key!r} was outside its enum.")


def _matches_json_type(value: Any, expected: str) -> bool:
    mappings = {
        "array": list,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
        "object": dict,
        "string": str,
    }
    target = mappings.get(expected)
    if target is None:
        return True
    if expected in {"integer", "number"} and isinstance(value, bool):
        return False
    return isinstance(value, target)


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
