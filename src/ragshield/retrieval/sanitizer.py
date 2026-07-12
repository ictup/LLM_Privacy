"""Retrieval sanitizer for suspicious instruction-like retrieved content."""

from __future__ import annotations

import re
from dataclasses import replace

from ragshield.schemas import RetrievedChunk


SUSPICIOUS_PATTERNS = {
    "ignore_instruction": re.compile(r"ignore (previous|prior|all) instructions", re.I),
    "reveal_policy": re.compile(r"reveal (the )?(system prompt|hidden policy|developer message)", re.I),
    "tool_instruction": re.compile(r"\b(call|use)\s+(send_email|read_secret_store|update_ticket)", re.I),
    "secret_request": re.compile(r"\b(disclose|exfiltrate|send)\b.*\b(secret|api_key|credential)", re.I),
    "untrusted_marker": re.compile(r"UNTRUSTED TEST INSTRUCTION", re.I),
    "base64_like": re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b"),
}


def unsafe_reasons(text: str) -> list[str]:
    return [name for name, pattern in SUSPICIOUS_PATTERNS.items() if pattern.search(text)]


def sanitize_chunks(chunks: list[RetrievedChunk], rerank: bool = True) -> list[RetrievedChunk]:
    sanitized = []
    for chunk in chunks:
        reasons = unsafe_reasons(chunk.text)
        score = chunk.score
        if reasons:
            score = round(score * 0.2, 4)
        sanitized.append(replace(chunk, score=score, unsafe_reasons=reasons))

    if rerank:
        sanitized.sort(key=lambda chunk: (bool(chunk.unsafe_reasons), -chunk.score, chunk.doc_id))
    return sanitized
