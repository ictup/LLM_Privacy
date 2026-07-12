"""Run RAGShield test cases against a configured system variant."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from ragshield.agents.tool_policy_gate import ToolPolicyGate
from ragshield.evaluation.metrics import summarize_results
from ragshield.evaluation.scorers import score_case
from ragshield.generation.answerer import DeterministicRAGAnswerer
from ragshield.retrieval.vector_store import LexicalVectorStore
from ragshield.utils.config import load_config
from ragshield.utils.jsonl import read_jsonl, write_jsonl


def _load_cases(paths: list[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in paths:
        cases.extend(read_jsonl(path))
    return cases


def run_cases(config_path: str, cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = load_config(config_path)
    retrieval_config = config.get("retrieval", {})
    defense_config = config.get("defenses", {})
    top_k = int(retrieval_config.get("top_k", 5))
    context_boundary = bool(defense_config.get("context_boundary", False))
    tenant_filtering = bool(defense_config.get("tenant_filtering", False))
    tool_policy_enabled = bool(defense_config.get("tool_policy_gate", False))

    store = LexicalVectorStore.from_jsonl("data/synthetic_docs/corpus.jsonl")
    answerer = DeterministicRAGAnswerer(context_boundary=context_boundary)
    gate = ToolPolicyGate() if tool_policy_enabled else None

    rows: list[dict[str, Any]] = []
    for case in cases:
        start = time.perf_counter()
        chunks = store.search(
            query=case["user_query"],
            top_k=top_k,
            tenant=case.get("tenant"),
            tenant_filtering=tenant_filtering,
        )
        answer = answerer.answer(query=case["user_query"], chunks=chunks)

        tool_decisions = []
        if gate is not None:
            for tool_call in answer.requested_tool_calls:
                result = gate.execute(
                    tool_name=tool_call["tool_name"],
                    role=case.get("role", "user"),
                    arguments=tool_call.get("arguments", {}),
                    approval_granted=False,
                )
                tool_decisions.append(result["decision"])

        score = score_case(
            case=case,
            answer=answer,
            retrieved_chunks=chunks,
            tool_decisions=tool_decisions,
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 3)
        rows.append(
            {
                "test_id": case["test_id"],
                "category": case["category"],
                "query": case["user_query"],
                "expected_behavior": case["expected_behavior"],
                "answer": answer.to_dict(),
                "retrieved_chunks": [chunk.to_dict() for chunk in chunks],
                "tool_decisions": tool_decisions,
                "score": score,
                "latency_ms": latency_ms,
            }
        )

    return rows, summarize_results(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--attacks", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = _load_cases(args.attacks)
    rows, summary = run_cases(config_path=args.config, cases=cases)
    write_jsonl(args.output, rows)
    summary_output = args.summary_output or str(Path(args.output).with_suffix(".summary.json"))
    Path(summary_output).parent.mkdir(parents=True, exist_ok=True)
    Path(summary_output).write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
