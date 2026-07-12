"""Run the frozen, real-LLM SafeRAG confirmatory study with resumable logs."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ragshield.benchmarks.saferag import SafeRAGCase, load_saferag
from ragshield.evaluation.saferag_judge import judge_answer
from ragshield.evaluation.saferag_study_protocol import (
    MODEL_SNAPSHOT,
    PROTOCOL_VERSION,
    SYSTEM_SPECS,
    apply_output_defense,
    build_bm25_stores,
    build_initial_contexts,
    prepare_system_input,
    prompt_hash,
    study_split,
    verify_frozen_protocol,
)
from ragshield.evaluation.saferag_study_report import (
    build_summary,
    merge_rows,
    write_blind_audit_sample,
    write_markdown,
    write_public_audit,
)
from ragshield.generation.openai_responses import OpenAIResponsesClient
from ragshield.utils.jsonl import read_jsonl


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read(path: str | Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path)) if Path(path).exists() else []


def _keyword_metrics(case: SafeRAGCase, answer: str) -> dict[str, Any]:
    if not case.attack_keywords:
        return {
            "attack_keyword_ratio": None,
            "attack_keyword_propagated": None,
            "matched_attack_keywords": [],
        }
    matched = [keyword for keyword in case.attack_keywords if keyword in answer]
    return {
        "attack_keyword_ratio": round(len(matched) / len(case.attack_keywords), 6),
        "attack_keyword_propagated": bool(matched),
        "matched_attack_keywords": matched,
    }


def _case_selected(case: SafeRAGCase, split: str) -> bool:
    return split == "all" or study_split(case) == split


def _generation_key(row: dict[str, Any]) -> tuple[str, str, str, str, int]:
    return (
        row["protocol_version"],
        row["requested_model"],
        row["system"],
        row["task"],
        int(row["case_id"]),
    )


def _judgment_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, int]:
    return (
        row["protocol_version"],
        row["generator_model"],
        row["judge_model"],
        row["system"],
        row["task"],
        int(row["case_id"]),
    )


def _generate_one(
    client: OpenAIResponsesClient,
    case: SafeRAGCase,
    initial_contexts,
    spec,
) -> dict[str, Any]:
    prepared = prepare_system_input(case, initial_contexts, spec)
    response = client.generate(prepared.instructions, prepared.input_text)
    answer, output_blocked = apply_output_defense(spec, response.text)
    return {
        "benchmark": "SafeRAG",
        "protocol_version": PROTOCOL_VERSION,
        "split": study_split(case),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "system": spec.name,
        "task": case.task,
        "case_id": case.case_id,
        "question": case.question,
        "requested_model": client.model,
        "response_model": response.model,
        "response_id": response.response_id,
        "prompt_hash": prompt_hash(spec),
        "reasoning_effort": client.reasoning_effort,
        "raw_answer": response.text,
        "answer": answer,
        "output_blocked": output_blocked,
        "initial_context_hash": prepared.initial_context_hash,
        "final_context_hash": prepared.final_context_hash,
        "initial_context_count": prepared.initial_context_count,
        "final_context_count": prepared.final_context_count,
        "screening": list(prepared.screening),
        "redaction_count": prepared.redaction_count,
        "defense_components": prepared.components,
        "keyword_metrics": _keyword_metrics(case, answer),
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
        },
        "latency_ms": response.latency_ms,
    }


def run_generation(
    root: str | Path,
    client: OpenAIResponsesClient,
    systems: list[str],
    split: str,
    output: str | Path,
    workers: int,
    max_calls: int | None,
) -> list[dict[str, Any]]:
    dataset = load_saferag(root)
    stores = build_bm25_stores(dataset)
    specs = {spec.name: spec for spec in SYSTEM_SPECS if spec.name in systems}
    output_path = Path(output)
    existing_rows = _read(output_path)
    existing = {_generation_key(row) for row in existing_rows}
    work = []
    for task, cases in dataset.cases.items():
        for case in cases:
            if not _case_selected(case, split):
                continue
            initial_contexts = build_initial_contexts(case, stores[task])
            for system in systems:
                key = (PROTOCOL_VERSION, client.model, system, task, case.case_id)
                if key not in existing:
                    work.append((case, initial_contexts, specs[system]))
    if max_calls is not None:
        work = work[:max_calls]
    print(f"Generation calls remaining: {len(work)}")

    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_generate_one, client, case, contexts, spec): (case, spec)
            for case, contexts, spec in work
        }
        for future in as_completed(futures):
            case, spec = futures[future]
            try:
                row = future.result()
                _append_jsonl(output_path, row)
                completed += 1
                print(
                    f"GEN {completed}/{len(work)} {spec.name} {case.task}-{case.case_id:03d} "
                    f"tokens={row['usage']['total_tokens']}"
                )
            except Exception as error:  # noqa: BLE001 - preserve resumability across API failures
                failures.append(f"{spec.name} {case.task}-{case.case_id}: {error}")
                print(f"GEN ERROR {failures[-1]}")
    if failures:
        raise RuntimeError(f"{len(failures)} generation calls failed; rerun to resume.")
    return _read(output_path)


def _judge_one(
    client: OpenAIResponsesClient,
    case: SafeRAGCase,
    generation: dict[str, Any],
) -> dict[str, Any]:
    judged = judge_answer(client, case, generation["answer"])
    return {
        "benchmark": "SafeRAG",
        "protocol_version": PROTOCOL_VERSION,
        "judged_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": generation["split"],
        "system": generation["system"],
        "task": generation["task"],
        "case_id": generation["case_id"],
        "generator_model": generation["requested_model"],
        "generator_response_id": generation["response_id"],
        "judge_model": client.model,
        "response_model": judged.response_model,
        "response_id": judged.response_id,
        "labels": judged.labels,
        "metrics": judged.metrics,
        "usage": judged.usage,
        "latency_ms": judged.latency_ms,
    }


def run_judging(
    root: str | Path,
    client: OpenAIResponsesClient,
    generation_rows: list[dict[str, Any]],
    systems: list[str],
    split: str,
    output: str | Path,
    workers: int,
    max_calls: int | None,
) -> list[dict[str, Any]]:
    dataset = load_saferag(root)
    case_map = {
        (case.task, case.case_id): case
        for cases in dataset.cases.values()
        for case in cases
    }
    output_path = Path(output)
    existing_rows = _read(output_path)
    existing = {_judgment_key(row) for row in existing_rows}
    work = []
    for generation in generation_rows:
        if generation.get("protocol_version") != PROTOCOL_VERSION:
            continue
        if generation["system"] not in systems:
            continue
        if split != "all" and generation["split"] != split:
            continue
        key = (
            PROTOCOL_VERSION,
            generation["requested_model"],
            client.model,
            generation["system"],
            generation["task"],
            int(generation["case_id"]),
        )
        if key not in existing:
            work.append((case_map[(generation["task"], int(generation["case_id"]))], generation))
    if max_calls is not None:
        work = work[:max_calls]
    print(f"Judge calls remaining: {len(work)}")

    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_judge_one, client, case, generation): (case, generation)
            for case, generation in work
        }
        for future in as_completed(futures):
            case, generation = futures[future]
            try:
                row = future.result()
                _append_jsonl(output_path, row)
                completed += 1
                print(
                    f"JUDGE {completed}/{len(work)} {generation['system']} "
                    f"{case.task}-{case.case_id:03d} adopted={row['metrics']['attack_adopted']}"
                )
            except Exception as error:  # noqa: BLE001 - preserve resumability across API failures
                failures.append(f"{generation['system']} {case.task}-{case.case_id}: {error}")
                print(f"JUDGE ERROR {failures[-1]}")
    if failures:
        raise RuntimeError(f"{len(failures)} judge calls failed; rerun to resume.")
    return _read(output_path)


def _filter_generation(
    rows: list[dict[str, Any]], model: str, systems: list[str], split: str
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("protocol_version") == PROTOCOL_VERSION
        and row.get("requested_model") == model
        and row.get("system") in systems
        and (split == "all" or row.get("split") == split)
    ]


def _filter_judgments(
    rows: list[dict[str, Any]],
    generator_model: str,
    judge_model: str,
    systems: list[str],
    split: str,
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("protocol_version") == PROTOCOL_VERSION
        and row.get("generator_model") == generator_model
        and row.get("judge_model") == judge_model
        and row.get("system") in systems
        and (split == "all" or row.get("split") == split)
    ]


def expected_calls(root: str | Path, systems: list[str], split: str) -> dict[str, int]:
    dataset = load_saferag(root)
    cases = [
        case
        for task_cases in dataset.cases.values()
        for case in task_cases
        if _case_selected(case, split)
    ]
    return {
        "cases": len(cases),
        "systems": len(systems),
        "generation_calls": len(cases) * len(systems),
        "judge_calls": len(cases) * len(systems),
        "total_api_calls": len(cases) * len(systems) * 2,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("dry-run", "generate", "judge", "report", "all"),
        default="dry-run",
    )
    parser.add_argument("--root", default="data/external/saferag")
    parser.add_argument("--model", default=MODEL_SNAPSHOT)
    parser.add_argument("--judge-model", default=MODEL_SNAPSHOT)
    parser.add_argument("--split", choices=("development", "confirmatory", "all"), default="all")
    parser.add_argument(
        "--systems",
        nargs="+",
        choices=[spec.name for spec in SYSTEM_SPECS],
        default=[spec.name for spec in SYSTEM_SPECS],
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-generation-calls", type=int, default=None)
    parser.add_argument("--max-judge-calls", type=int, default=None)
    parser.add_argument("--generation-output", default="reports/saferag_gpt55_generations.jsonl")
    parser.add_argument("--judgment-output", default="reports/saferag_gpt55_judgments.jsonl")
    parser.add_argument("--results-output", default="reports/saferag_gpt55_results.json")
    parser.add_argument("--report-output", default="reports/saferag_gpt55_report.md")
    parser.add_argument("--audit-output", default="reports/saferag_gpt55_audit.json")
    parser.add_argument("--blind-audit-output", default="reports/saferag_gpt55_blind_audit.csv")
    parser.add_argument("--blind-audit-key", default="reports/saferag_gpt55_blind_audit_key.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_frozen_protocol()
    calls = expected_calls(args.root, args.systems, args.split)
    print(json.dumps({"protocol": PROTOCOL_VERSION, "model": args.model, **calls}, indent=2))
    if args.phase == "dry-run":
        return

    generation_rows = _read(args.generation_output)
    if args.phase in {"generate", "all"}:
        generation_client = OpenAIResponsesClient(
            model=args.model,
            reasoning_effort="low",
            max_output_tokens=512,
        )
        generation_rows = run_generation(
            args.root,
            generation_client,
            args.systems,
            args.split,
            args.generation_output,
            args.workers,
            args.max_generation_calls,
        )
    generation_rows = _filter_generation(generation_rows, args.model, args.systems, args.split)

    judgment_rows = _read(args.judgment_output)
    if args.phase in {"judge", "all"}:
        judge_client = OpenAIResponsesClient(
            model=args.judge_model,
            reasoning_effort="medium",
            max_output_tokens=4096,
        )
        judgment_rows = run_judging(
            args.root,
            judge_client,
            generation_rows,
            args.systems,
            args.split,
            args.judgment_output,
            args.workers,
            args.max_judge_calls,
        )
    judgment_rows = _filter_judgments(
        judgment_rows,
        args.model,
        args.judge_model,
        args.systems,
        args.split,
    )

    if args.phase in {"report", "all"}:
        summary = build_summary(generation_rows, judgment_rows, args.model, args.judge_model)
        Path(args.results_output).write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        write_markdown(summary, args.report_output)
        write_public_audit(generation_rows, judgment_rows, args.audit_output)
        write_blind_audit_sample(
            merge_rows(generation_rows, judgment_rows),
            args.blind_audit_output,
            args.blind_audit_key,
        )
        print(json.dumps(summary["confirmatory"]["overall"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
