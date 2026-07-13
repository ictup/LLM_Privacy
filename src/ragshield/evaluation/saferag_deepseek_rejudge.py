"""Cross-provider DeepSeek rejudging of the frozen SafeRAG GPT-5 mini answers."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from ragshield.benchmarks.saferag import SafeRAGCase, load_saferag
from ragshield.evaluation.saferag_judge import (
    FROZEN_JUDGE_PROMPT_HASH,
    JUDGE_VERSION,
    judge_answer,
    verify_frozen_judge,
)
from ragshield.evaluation.saferag_statistics import (
    exact_mcnemar,
    paired_bootstrap_difference,
    wilson_interval,
)
from ragshield.evaluation.saferag_study_protocol import (
    MODEL_SNAPSHOT,
    PROTOCOL_VERSION,
)
from ragshield.generation.deepseek_chat import PRO_MODEL, DeepSeekChatClient
from ragshield.utils.jsonl import read_jsonl


REJUDGE_PROTOCOL_VERSION = "saferag-deepseek-independent-rejudge-v1"
REJUDGE_JUDGE_VERSION = f"{JUDGE_VERSION}-deepseek-pro-v1"
ANALYSIS_VERSION = "original-377-complete-cases-v1"
ORIGINAL_CONFIRMATORY_EXCLUSIONS = frozenset({("WDoS", 41), ("WDoS", 47)})
DEEPSEEK_PRO_PRICES = {"input": 0.435, "output": 0.87}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def protocol_hash() -> str:
    payload = {
        "protocol": REJUDGE_PROTOCOL_VERSION,
        "source_protocol": PROTOCOL_VERSION,
        "source_generator": MODEL_SNAPSHOT,
        "judge": PRO_MODEL,
        "judge_prompt_hash": FROZEN_JUDGE_PROMPT_HASH,
        "thinking": False,
        "temperature": 0.0,
        "max_output_tokens": 768,
        "exclusions": sorted([list(item) for item in ORIGINAL_CONFIRMATORY_EXCLUSIONS]),
    }
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True))


FROZEN_REJUDGE_PROTOCOL_HASH = "9bed5045056899025dba08cebfb487ec8bea5a5ae8afd669824db674f184f60a"


def verify_frozen_protocol() -> None:
    if protocol_hash() != FROZEN_REJUDGE_PROTOCOL_HASH:
        raise RuntimeError("Frozen DeepSeek rejudge protocol changed.")


def _read(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    return list(read_jsonl(source)) if source.exists() else []


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _load_key(path: str | Path) -> str:
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError("DeepSeek API key file is empty.")
    return value


def select_source_generations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.get("protocol_version") == PROTOCOL_VERSION
        and row.get("requested_model") == MODEL_SNAPSHOT
        and row.get("split") == "confirmatory"
        and (row.get("task"), int(row.get("case_id", -1)))
        not in ORIGINAL_CONFIRMATORY_EXCLUSIONS
    ]
    selected.sort(key=lambda row: (row["task"], int(row["case_id"]), row["system"]))
    return selected


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (row["source_generation_response_id"], row["judge_model"])


def _judge_one(
    client: DeepSeekChatClient,
    case: SafeRAGCase,
    generation: dict[str, Any],
) -> dict[str, Any]:
    judged = judge_answer(client, case, generation["answer"])
    return {
        "benchmark": "SafeRAG",
        "rejudge_protocol_version": REJUDGE_PROTOCOL_VERSION,
        "rejudge_protocol_hash": FROZEN_REJUDGE_PROTOCOL_HASH,
        "source_protocol_version": generation["protocol_version"],
        "source_generator_model": generation["requested_model"],
        "source_generation_response_id": generation["response_id"],
        "judged_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": generation["split"],
        "system": generation["system"],
        "task": generation["task"],
        "case_id": generation["case_id"],
        "judge_model": client.model,
        "judge_version": REJUDGE_JUDGE_VERSION,
        "judge_prompt_hash": FROZEN_JUDGE_PROMPT_HASH,
        "response_model": judged.response_model,
        "response_id": judged.response_id,
        "response_status": judged.response_status,
        "labels": judged.labels,
        "metrics": judged.metrics,
        "usage": judged.usage,
        "latency_ms": judged.latency_ms,
    }


def run_rejudge(
    root: str | Path,
    generations: list[dict[str, Any]],
    output: str | Path,
    api_key_file: str | Path,
    workers: int = 32,
    max_calls: int | None = None,
    allow_incomplete: bool = False,
) -> list[dict[str, Any]]:
    dataset = load_saferag(root)
    cases = {
        (case.task, case.case_id): case
        for task_cases in dataset.cases.values()
        for case in task_cases
    }
    output_path = Path(output)
    existing_rows = _read(output_path)
    existing = {_row_key(row) for row in existing_rows}
    work = [
        generation
        for generation in generations
        if (generation["response_id"], PRO_MODEL) not in existing
    ]
    if max_calls is not None:
        work = work[:max_calls]
    print(f"DeepSeek rejudge calls remaining: {len(work)}")
    if not work:
        return existing_rows

    client = DeepSeekChatClient(
        model=PRO_MODEL,
        thinking=False,
        temperature=0.0,
        max_output_tokens=768,
        max_retries=5,
        api_key=_load_key(api_key_file),
    )
    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _judge_one,
                client,
                cases[(generation["task"], int(generation["case_id"]))],
                generation,
            ): generation
            for generation in work
        }
        for future in as_completed(futures):
            generation = futures[future]
            try:
                row = future.result()
                _append_jsonl(output_path, row)
                completed += 1
                if completed % 25 == 0 or completed == len(work):
                    print(f"REJUDGE {completed}/{len(work)}")
            except Exception as error:  # noqa: BLE001 - resumable paid runner
                failures.append(
                    f"{generation['system']} {generation['task']}-{generation['case_id']}: {error}"
                )
                print(f"REJUDGE ERROR {failures[-1]}")
    if failures and not allow_incomplete:
        raise RuntimeError(f"{len(failures)} DeepSeek rejudge calls failed; rerun to resume.")
    if failures:
        print(f"WARNING: {len(failures)} rejudge calls failed; reporting complete cases only.")
    return _read(output_path)


def _cohen_kappa(left: list[bool], right: list[bool]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    observed = mean(a == b for a, b in zip(left, right, strict=True))
    left_positive = mean(left)
    right_positive = mean(right)
    expected = left_positive * right_positive + (1 - left_positive) * (1 - right_positive)
    if expected == 1:
        return 1.0
    return round((observed - expected) / (1 - expected), 6)


def _agreement_rows(
    original: list[dict[str, Any]], rejudged: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    original_map = {
        (row["system"], row["task"], int(row["case_id"])): row for row in original
    }
    rows = []
    for row in rejudged:
        key = (row["system"], row["task"], int(row["case_id"]))
        source = original_map.get(key)
        if source is None:
            continue
        rows.append(
            {
                "system": row["system"],
                "task": row["task"],
                "case_id": int(row["case_id"]),
                "original": bool(source["metrics"]["attack_adopted"]),
                "deepseek": bool(row["metrics"]["attack_adopted"]),
            }
        )
    return rows


def _agreement_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def summarize(selected: list[dict[str, Any]]) -> dict[str, Any]:
        left = [row["original"] for row in selected]
        right = [row["deepseek"] for row in selected]
        return {
            "n": len(selected),
            "exact_agreement": round(mean(a == b for a, b in zip(left, right, strict=True)), 6)
            if selected
            else None,
            "cohen_kappa": _cohen_kappa(left, right) if selected else None,
            "gpt_positive_deepseek_positive": sum(a and b for a, b in zip(left, right, strict=True)),
            "gpt_positive_deepseek_negative": sum(a and not b for a, b in zip(left, right, strict=True)),
            "gpt_negative_deepseek_positive": sum(not a and b for a, b in zip(left, right, strict=True)),
            "gpt_negative_deepseek_negative": sum(not a and not b for a, b in zip(left, right, strict=True)),
        }

    return {
        "overall": summarize(rows),
        "by_system": {
            system: summarize([row for row in rows if row["system"] == system])
            for system in sorted({row["system"] for row in rows})
        },
        "by_task": {
            task: summarize([row for row in rows if row["task"] == task])
            for task in sorted({row["task"] for row in rows})
        },
    }


def _aggregate(rows: list[dict[str, Any]], system: str) -> dict[str, Any]:
    selected = [row for row in rows if row["system"] == system]
    values = [bool(row["metrics"]["attack_adopted"]) for row in selected]
    return {
        "system": system,
        "n": len(selected),
        "attack_adoption_rate": round(mean(values), 6),
        "attack_adoption_ci95": list(wilson_interval(values)),
        "utility_f1": round(mean(row["metrics"]["option_macro_f1"] for row in selected), 6),
        "grounded_rate": round(mean(bool(row["metrics"]["grounded"]) for row in selected), 6),
    }


def _paired(rows: list[dict[str, Any]], treatment: str) -> dict[str, Any]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["task"], int(row["case_id"]))][row["system"]] = row
    common = [value for value in grouped.values() if "baseline" in value and treatment in value]
    attack_pairs = [
        (
            bool(value["baseline"]["metrics"]["attack_adopted"]),
            bool(value[treatment]["metrics"]["attack_adopted"]),
        )
        for value in common
    ]
    utility_pairs = [
        (
            float(value["baseline"]["metrics"]["option_macro_f1"]),
            float(value[treatment]["metrics"]["option_macro_f1"]),
        )
        for value in common
    ]
    return {
        "treatment": treatment,
        "attack_adoption_difference": paired_bootstrap_difference(
            [(float(left), float(right)) for left, right in attack_pairs]
        ),
        "attack_adoption_mcnemar": exact_mcnemar(attack_pairs),
        "utility_f1_difference": paired_bootstrap_difference(utility_pairs),
    }


def build_results(
    generations: list[dict[str, Any]],
    original: list[dict[str, Any]],
    rejudged: list[dict[str, Any]],
) -> dict[str, Any]:
    generation_ids = {row["response_id"] for row in generations}
    selected_rejudged = [
        row
        for row in rejudged
        if row.get("rejudge_protocol_version") == REJUDGE_PROTOCOL_VERSION
        and row.get("source_generation_response_id") in generation_ids
        and row.get("judge_model") == PRO_MODEL
    ]
    complete: dict[tuple[str, int], set[str]] = defaultdict(set)
    for row in selected_rejudged:
        complete[(row["task"], int(row["case_id"]))].add(row["system"])
    complete_keys = {key for key, systems in complete.items() if len(systems) == 3}
    selected_rejudged = [
        row
        for row in selected_rejudged
        if (row["task"], int(row["case_id"])) in complete_keys
    ]
    original = [
        row
        for row in original
        if (row["task"], int(row["case_id"])) in complete_keys
    ]
    agreement_rows = _agreement_rows(original, selected_rejudged)
    input_tokens = sum(row["usage"]["input_tokens"] for row in selected_rejudged)
    output_tokens = sum(row["usage"]["output_tokens"] for row in selected_rejudged)
    systems = sorted({row["system"] for row in selected_rejudged})
    return {
        "benchmark": "SafeRAG",
        "study": "cross_provider_independent_rejudge",
        "rejudge_protocol_version": REJUDGE_PROTOCOL_VERSION,
        "rejudge_protocol_hash": FROZEN_REJUDGE_PROTOCOL_HASH,
        "analysis_version": ANALYSIS_VERSION,
        "source_protocol_version": PROTOCOL_VERSION,
        "source_generator_model": MODEL_SNAPSHOT,
        "original_judge_model": MODEL_SNAPSHOT,
        "independent_judge_model": PRO_MODEL,
        "judge_prompt_hash": FROZEN_JUDGE_PROMPT_HASH,
        "confirmatory_cases": len(complete_keys),
        "judgment_rows": len(selected_rejudged),
        "unique_response_ids": len({row["response_id"] for row in selected_rejudged}),
        "overall": [_aggregate(selected_rejudged, system) for system in systems],
        "paired_comparisons": [
            _paired(selected_rejudged, system) for system in systems if system != "baseline"
        ],
        "agreement_with_original_gpt_judge": _agreement_summary(agreement_rows),
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_usd_cache_miss": round(
                input_tokens / 1_000_000 * DEEPSEEK_PRO_PRICES["input"]
                + output_tokens / 1_000_000 * DEEPSEEK_PRO_PRICES["output"],
                6,
            ),
        },
        "limitations": [
            "DeepSeek provides cross-provider automatic judgment, not human ground truth.",
            "The rejudge preserves the original 377-case complete-case sample and frozen GPT answers.",
            "Judge agreement does not establish correctness when both automatic judges share a bias.",
        ],
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def write_report(results: dict[str, Any], output: str | Path) -> None:
    lines = [
        "# SafeRAG Cross-Provider DeepSeek Rejudge",
        "",
        "## Study Identity",
        "",
        f"- Protocol: `{results['rejudge_protocol_version']}`",
        f"- Source generator: `{results['source_generator_model']}`",
        f"- Original judge: `{results['original_judge_model']}`",
        f"- Independent judge: `{results['independent_judge_model']}`",
        f"- Confirmatory cases: {results['confirmatory_cases']}",
        f"- Independent judgments: {results['judgment_rows']}",
        "- System identity was not included in the judge input.",
        "",
        "## DeepSeek Rejudge Results",
        "",
        "| System | N | Attack adoption (95% CI) | Utility F1 | Grounded |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in results["overall"]:
        interval = row["attack_adoption_ci95"]
        lines.append(
            f"| {row['system']} | {row['n']} | {_pct(row['attack_adoption_rate'])} "
            f"({_pct(interval[0])}-{_pct(interval[1])}) | {_pct(row['utility_f1'])} | "
            f"{_pct(row['grounded_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Paired Effects",
            "",
            "| Treatment | Attack difference (95% CI) | McNemar p | Utility difference (95% CI) |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in results["paired_comparisons"]:
        attack = row["attack_adoption_difference"]
        utility = row["utility_f1_difference"]
        p_value = row["attack_adoption_mcnemar"]["p_value"]
        p_text = "<0.0001" if p_value < 0.0001 else f"{p_value:.4f}"
        lines.append(
            f"| {row['treatment']} | {attack['difference']:.3f} "
            f"[{attack['ci_low']:.3f}, {attack['ci_high']:.3f}] | {p_text} | "
            f"{utility['difference']:.3f} [{utility['ci_low']:.3f}, {utility['ci_high']:.3f}] |"
        )
    agreement = results["agreement_with_original_gpt_judge"]
    lines.extend(
        [
            "",
            "## Agreement With Original GPT Judge",
            "",
            "| Scope | N | Exact agreement | Cohen kappa |",
            "|---|---:|---:|---:|",
            f"| Overall | {agreement['overall']['n']} | "
            f"{_pct(agreement['overall']['exact_agreement'])} | "
            f"{agreement['overall']['cohen_kappa']:.3f} |",
        ]
    )
    for system, row in agreement["by_system"].items():
        lines.append(
            f"| {system} | {row['n']} | {_pct(row['exact_agreement'])} | "
            f"{row['cohen_kappa']:.3f} |"
        )
    usage = results["usage"]
    lines.extend(
        [
            "",
            "## Execution Evidence",
            "",
            f"- Unique DeepSeek response IDs: {results['unique_response_ids']}",
            f"- Input tokens: {usage['input_tokens']}",
            f"- Output tokens: {usage['output_tokens']}",
            f"- Estimated cache-miss cost: `${usage['estimated_usd_cache_miss']:.4f}`",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in results["limitations"])
    Path(output).write_text("\n".join(lines), encoding="utf-8")


def write_public_audit(
    generations: list[dict[str, Any]],
    original: list[dict[str, Any]],
    rejudged: list[dict[str, Any]],
    output: str | Path,
) -> None:
    generation_map = {
        (row["system"], row["task"], int(row["case_id"])): row for row in generations
    }
    original_map = {
        (row["system"], row["task"], int(row["case_id"])): row for row in original
    }
    records = []
    for row in rejudged:
        key = (row["system"], row["task"], int(row["case_id"]))
        generation = generation_map.get(key)
        source = original_map.get(key)
        if generation is None or source is None:
            continue
        records.append(
            {
                "system": row["system"],
                "task": row["task"],
                "case_id": row["case_id"],
                "source_generation_response_id_sha256": _sha256(generation["response_id"]),
                "answer_sha256": _sha256(generation["answer"]),
                "original_judge_response_id_sha256": _sha256(source["response_id"]),
                "deepseek_judge_response_id_sha256": _sha256(row["response_id"]),
                "original_attack_adopted": bool(source["metrics"]["attack_adopted"]),
                "deepseek_attack_adopted": bool(row["metrics"]["attack_adopted"]),
                "judge_prompt_hash": row["judge_prompt_hash"],
                "usage": row["usage"],
            }
        )
    payload = {
        "rejudge_protocol_version": REJUDGE_PROTOCOL_VERSION,
        "rejudge_protocol_hash": FROZEN_REJUDGE_PROTOCOL_HASH,
        "note": "Raw benchmark text, answers, and opaque response IDs are not redistributed.",
        "records": records,
    }
    Path(output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("dry-run", "judge", "report", "all"), default="dry-run")
    parser.add_argument("--root", default="data/external/saferag")
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--max-calls", type=int, default=None)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument(
        "--api-key-file",
        default="../.secrets/deepseek_api_key.txt",
    )
    parser.add_argument(
        "--generation-input",
        default="reports/saferag_gpt5mini_generations.jsonl",
    )
    parser.add_argument(
        "--original-judgment-input",
        default="reports/saferag_gpt5mini_judgments.jsonl",
    )
    parser.add_argument(
        "--rejudge-output",
        default="reports/saferag_deepseek_rejudge_judgments.jsonl",
    )
    parser.add_argument(
        "--results-output",
        default="reports/saferag_deepseek_rejudge_results.json",
    )
    parser.add_argument(
        "--report-output",
        default="reports/saferag_deepseek_rejudge_report.md",
    )
    parser.add_argument(
        "--audit-output",
        default="reports/saferag_deepseek_rejudge_audit.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_frozen_judge()
    verify_frozen_protocol()
    generations = select_source_generations(_read(args.generation_input))
    print(
        json.dumps(
            {
                "protocol": REJUDGE_PROTOCOL_VERSION,
                "protocol_hash": FROZEN_REJUDGE_PROTOCOL_HASH,
                "source_generations": len(generations),
                "judge": PRO_MODEL,
                "workers": args.workers,
            },
            indent=2,
        )
    )
    if len(generations) != 1131:
        raise RuntimeError(f"Expected 1,131 frozen source answers, found {len(generations)}.")
    if args.phase == "dry-run":
        return

    rejudged = _read(args.rejudge_output)
    if args.phase in {"judge", "all"}:
        rejudged = run_rejudge(
            args.root,
            generations,
            args.rejudge_output,
            args.api_key_file,
            workers=args.workers,
            max_calls=args.max_calls,
            allow_incomplete=args.allow_incomplete,
        )

    if args.phase in {"report", "all"}:
        original = [
            row
            for row in _read(args.original_judgment_input)
            if row.get("protocol_version") == PROTOCOL_VERSION
            and row.get("generator_model") == MODEL_SNAPSHOT
            and row.get("judge_model") == MODEL_SNAPSHOT
            and row.get("split") == "confirmatory"
            and (row.get("task"), int(row.get("case_id", -1)))
            not in ORIGINAL_CONFIRMATORY_EXCLUSIONS
        ]
        results = build_results(generations, original, rejudged)
        Path(args.results_output).write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        write_report(results, args.report_output)
        write_public_audit(generations, original, rejudged, args.audit_output)
        print(json.dumps(results["overall"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
