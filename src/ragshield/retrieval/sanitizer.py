"""Retrieval sanitizer for suspicious instruction-like retrieved content."""

from __future__ import annotations

import re
from dataclasses import replace

from ragshield.schemas import RetrievedChunk


SUSPICIOUS_PATTERNS = {
    "ignore_instruction": re.compile(r"\b(ignore|disregard|discard|bypass)\b.{0,40}\b(instructions?|rules?|policy|approval)\b", re.I),
    "reveal_policy": re.compile(r"\b(reveal|print|append|expose)\b.{0,40}\b(system prompt|hidden policy|developer message|configuration)\b", re.I),
    "tool_instruction": re.compile(r"\b(call|use|invoke|action is)\b.{0,20}\b(send_email|read_secret_store|update_ticket)\b", re.I),
    "secret_request": re.compile(r"\b(disclose|exfiltrate|send|plain text)\b.{0,60}\b(secret|api_key|credential|private data)\b", re.I),
    "authority_spoofing": re.compile(r"\b(system override|priority=system|assistant:|compliance reviewer requires)\b", re.I),
    "untrusted_marker": re.compile(r"UNTRUSTED (?:TEST INSTRUCTION|CONTENT)", re.I),
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
