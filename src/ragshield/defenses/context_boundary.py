"""Context boundary helpers for marking retrieved evidence as untrusted."""

from __future__ import annotations

from dataclasses import replace

from ragshield.schemas import RetrievedChunk


START_TAG = "<UNTRUSTED_RETRIEVED_CONTEXT>"
END_TAG = "</UNTRUSTED_RETRIEVED_CONTEXT>"


def wrap_untrusted_context(text: str) -> str:
    return f"{START_TAG}\n{text}\n{END_TAG}"


def wrap_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    return [replace(chunk, text=wrap_untrusted_context(chunk.text)) for chunk in chunks]
