"""Reporting, audit artifacts, and paired analysis for the SafeRAG GPT-5.5 study."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from ragshield.evaluation.saferag_judge import FROZEN_JUDGE_PROMPT_HASH, JUDGE_VERSION
from ragshield.evaluation.saferag_statistics import (
    exact_mcnemar,
    paired_bootstrap_difference,
    wilson_interval,
)
from ragshield.evaluation.saferag_study_protocol import (
    PROTOCOL_VERSION,
    SAFERAG_COMMIT,
)


GPT55_INPUT_PRICE_PER_MILLION = 5.0
GPT55_OUTPUT_PRICE_PER_MILLION = 30.0


def _key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (row["system"], row["task"], int(row["case_id"]))


def merge_rows(
    generation_rows: list[dict[str, Any]],
    judgment_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    judgment_map = {_key(row): row for row in judgment_rows}
    merged = []
    for generation in generation_rows:
        judgment = judgment_map.get(_key(generation))
        if judgment is not None:
            merged.append({"generation": generation, "judgment": judgment})
    return merged


def _aggregate(rows: list[dict[str, Any]], system: str, task: str | None = None) -> dict:
    selected = [
        row
        for row in rows
        if row["generation"]["system"] == system
        and (task is None or row["generation"]["task"] == task)
    ]
    attack_values = [row["judgment"]["metrics"]["attack_adopted"] for row in selected]
    keyword_rows = [
        row
        for row in selected
        if row["generation"]["keyword_metrics"]["attack_keyword_ratio"] is not None
    ]
    interval = wilson_interval(attack_values)
    return {
        "system": system,
        "task": task or "ALL",
        "n": len(selected),
        "attack_adoption_rate": round(mean(attack_values), 6) if attack_values else None,
        "attack_adoption_ci95": list(interval) if attack_values else None,
        "attack_mention_only_rate": round(
            mean(row["judgment"]["metrics"]["attack_mentioned_only"] for row in selected),
            6,
        )
        if selected
        else None,
        "refusal_rate": round(
            mean(row["judgment"]["metrics"]["refusal"] for row in selected), 6
        )
        if selected
        else None,
        "grounded_rate": round(
            mean(row["judgment"]["metrics"]["grounded"] for row in selected), 6
        )
        if selected
        else None,
        "option_macro_f1": round(
            mean(row["judgment"]["metrics"]["option_macro_f1"] for row in selected), 6
        )
        if selected
        else None,
        "attack_keyword_case_rate": round(
            mean(
                row["generation"]["keyword_metrics"]["attack_keyword_propagated"]
                for row in keyword_rows
            ),
            6,
        )
        if keyword_rows
        else None,
        "avg_generation_latency_ms": round(
            mean(row["generation"]["latency_ms"] for row in selected), 3
        )
        if selected
        else None,
        "avg_final_context_count": round(
            mean(row["generation"]["final_context_count"] for row in selected), 3
        )
        if selected
        else None,
        "judge_consistent_rate": round(
            mean(
                row["judgment"]["metrics"].get("judge_consistent", True)
                for row in selected
            ),
            6,
        )
        if selected
        else None,
    }


def _paired(rows: list[dict[str, Any]], treatment: str) -> dict[str, Any]:
    by_case: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        generation = row["generation"]
        by_case[(generation["task"], int(generation["case_id"]))][generation["system"]] = row

    common = [
        systems
        for systems in by_case.values()
        if "baseline" in systems and treatment in systems
    ]
    attack_pairs = [
        (
            systems["baseline"]["judgment"]["metrics"]["attack_adopted"],
            systems[treatment]["judgment"]["metrics"]["attack_adopted"],
        )
        for systems in common
    ]
    utility_pairs = [
        (
            systems["baseline"]["judgment"]["metrics"]["option_macro_f1"],
            systems[treatment]["judgment"]["metrics"]["option_macro_f1"],
        )
        for systems in common
    ]
    refusal_pairs = [
        (
            systems["baseline"]["judgment"]["metrics"]["refusal"],
            systems[treatment]["judgment"]["metrics"]["refusal"],
        )
        for systems in common
    ]
    return {
        "baseline": "baseline",
        "treatment": treatment,
        "attack_adoption_difference": paired_bootstrap_difference(
            [(float(left), float(right)) for left, right in attack_pairs]
        ),
        "attack_adoption_mcnemar": exact_mcnemar(attack_pairs),
        "utility_f1_difference": paired_bootstrap_difference(utility_pairs),
        "refusal_difference": paired_bootstrap_difference(
            [(float(left), float(right)) for left, right in refusal_pairs]
        ),
    }


def _split_summary(rows: list[dict[str, Any]], split: str) -> dict[str, Any]:
    selected = [row for row in rows if row["generation"]["split"] == split]
    systems = sorted({row["generation"]["system"] for row in selected})
    tasks = sorted({row["generation"]["task"] for row in selected})
    return {
        "n_cases": len(
            {(row["generation"]["task"], row["generation"]["case_id"]) for row in selected}
        ),
        "overall": [_aggregate(selected, system) for system in systems],
        "by_task": [
            _aggregate(selected, system, task) for system in systems for task in tasks
        ],
        "paired_comparisons": [
            _paired(selected, system) for system in systems if system != "baseline"
        ],
    }


def _cost(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    input_tokens = sum(row["usage"]["input_tokens"] for row in rows)
    output_tokens = sum(row["usage"]["output_tokens"] for row in rows)
    usd = (
        input_tokens / 1_000_000 * GPT55_INPUT_PRICE_PER_MILLION
        + output_tokens / 1_000_000 * GPT55_OUTPUT_PRICE_PER_MILLION
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_usd_at_documented_gpt55_standard_rates": round(usd, 4),
    }


def build_summary(
    generation_rows: list[dict[str, Any]],
    judgment_rows: list[dict[str, Any]],
    generator_model: str,
    judge_model: str,
) -> dict[str, Any]:
    merged = merge_rows(generation_rows, judgment_rows)
    initial_hashes: dict[tuple[str, int], set[str]] = defaultdict(set)
    for row in generation_rows:
        initial_hashes[(row["task"], int(row["case_id"]))].add(row["initial_context_hash"])
    mismatches = sum(len(values) != 1 for values in initial_hashes.values())
    return {
        "benchmark": "SafeRAG",
        "saferag_commit": SAFERAG_COMMIT,
        "protocol_version": PROTOCOL_VERSION,
        "generator_model": generator_model,
        "judge_model": judge_model,
        "judge_version": JUDGE_VERSION,
        "judge_prompt_hash": FROZEN_JUDGE_PROMPT_HASH,
        "execution_evidence": {
            "generation_rows": len(generation_rows),
            "judgment_rows": len(judgment_rows),
            "unique_generation_response_ids": len(
                {row["response_id"] for row in generation_rows}
            ),
            "unique_judge_response_ids": len({row["response_id"] for row in judgment_rows}),
            "initial_context_pair_mismatches": mismatches,
            "judge_consistency_flagged_rows": sum(
                not row["metrics"].get("judge_consistent", True) for row in judgment_rows
            ),
            "judge_low_confidence_rows": sum(
                row["metrics"].get("judge_confidence") == "low" for row in judgment_rows
            ),
        },
        "generation_cost": _cost(generation_rows),
        "judge_cost": _cost(judgment_rows),
        "development": _split_summary(merged, "development"),
        "confirmatory": _split_summary(merged, "confirmatory"),
        "limitations": [
            "The generator and automated judge use the same model family.",
            "Human blind review is required before claiming judge validity.",
            "SafeRAG evaluates data-injection security, not differential privacy.",
            "The label-free defense may miss plausible, semantically injected facts.",
            "Raw SafeRAG text and model answers are retained locally due source licensing.",
        ],
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def write_markdown(summary: dict[str, Any], output: str | Path) -> None:
    confirmatory = summary["confirmatory"]
    lines = [
        "# RAGShield SafeRAG GPT-5.5 Confirmatory Study",
        "",
        "## Study Identity",
        "",
        f"- Protocol: `{summary['protocol_version']}`",
        f"- SafeRAG commit: `{summary['saferag_commit']}`",
        f"- Generator: `{summary['generator_model']}`",
        f"- Judge: `{summary['judge_model']}`",
        f"- Judge protocol: `{summary['judge_version']}`",
        f"- Judge prompt hash: `{summary['judge_prompt_hash']}`",
        f"- Confirmatory cases: {confirmatory['n_cases']}",
        "- Primary endpoint: judge-assessed attack adoption",
        "- Utility endpoint: macro F1 over supported correct and contradicted incorrect options",
        "",
        "## Execution Evidence",
        "",
    ]
    evidence = summary["execution_evidence"]
    lines.extend(f"- {key.replace('_', ' ').title()}: {value}" for key, value in evidence.items())
    development = summary["development"]
    lines.extend(
        [
            "",
            "## Development Results (Tuning Only)",
            "",
            "These eight cases are excluded from the primary confirmatory claim.",
            "",
            "| System | N | Attack Adoption | Utility F1 | Grounded |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in development["overall"]:
        lines.append(
            f"| {row['system']} | {row['n']} | {_pct(row['attack_adoption_rate'])} | "
            f"{_pct(row['option_macro_f1'])} | {_pct(row['grounded_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Confirmatory Results",
            "",
            (
                "| System | N | Attack Adoption (95% CI) | Mention Only | "
                "Utility F1 | Grounded | Refusal |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in confirmatory["overall"]:
        interval = row["attack_adoption_ci95"]
        ci = "n/a" if interval is None else f"{_pct(interval[0])}-{_pct(interval[1])}"
        lines.append(
            f"| {row['system']} | {row['n']} | {_pct(row['attack_adoption_rate'])} "
            f"({ci}) | {_pct(row['attack_mention_only_rate'])} | "
            f"{_pct(row['option_macro_f1'])} | {_pct(row['grounded_rate'])} | "
            f"{_pct(row['refusal_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Paired Effects",
            "",
            "Negative attack-adoption differences favor the defense; positive utility differences",
            "favor the defense. Intervals crossing zero are inconclusive.",
            "",
            "| Treatment | Attack Difference (95% CI) | McNemar p | Utility Difference (95% CI) |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in confirmatory["paired_comparisons"]:
        attack = row["attack_adoption_difference"]
        utility = row["utility_f1_difference"]
        lines.append(
            f"| {row['treatment']} | {attack['difference']:.3f} "
            f"[{attack['ci_low']:.3f}, {attack['ci_high']:.3f}] | "
            f"{row['attack_adoption_mcnemar']['p_value']:.4f} | "
            f"{utility['difference']:.3f} [{utility['ci_low']:.3f}, "
            f"{utility['ci_high']:.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Results by Task",
            "",
            "| System | Task | N | Attack Adoption | Utility F1 | Keyword Cases |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in confirmatory["by_task"]:
        lines.append(
            f"| {row['system']} | {row['task']} | {row['n']} | "
            f"{_pct(row['attack_adoption_rate'])} | {_pct(row['option_macro_f1'])} | "
            f"{_pct(row['attack_keyword_case_rate'])} |"
        )
    generation_cost = summary["generation_cost"]
    judge_cost = summary["judge_cost"]
    total_estimated_cost = (
        generation_cost["estimated_usd_at_documented_gpt55_standard_rates"]
        + judge_cost["estimated_usd_at_documented_gpt55_standard_rates"]
    )
    lines.extend(
        [
            "",
            "## Token and Cost Record",
            "",
            f"- Generation tokens: {generation_cost['total_tokens']}",
            f"- Judge tokens: {judge_cost['total_tokens']}",
            (
                "- Estimated API cost at documented GPT-5.5 standard rates: "
                f"${total_estimated_cost:.2f}"
            ),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["limitations"])
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_public_audit(
    generation_rows: list[dict[str, Any]],
    judgment_rows: list[dict[str, Any]],
    output: str | Path,
) -> None:
    merged = merge_rows(generation_rows, judgment_rows)
    records = []
    for row in merged:
        generation = row["generation"]
        judgment = row["judgment"]
        records.append(
            {
                "system": generation["system"],
                "task": generation["task"],
                "case_id": generation["case_id"],
                "split": generation["split"],
                "prompt_hash": generation["prompt_hash"],
                "initial_context_hash": generation["initial_context_hash"],
                "final_context_hash": generation["final_context_hash"],
                "generation_response_id_sha256": _sha256(generation["response_id"]),
                "answer_sha256": _sha256(generation["answer"]),
                "judge_response_id_sha256": _sha256(judgment["response_id"]),
                "judge_prompt_hash": judgment.get("judge_prompt_hash"),
                "judge_metrics": judgment["metrics"],
                "generation_usage": generation["usage"],
                "judge_usage": judgment["usage"],
            }
        )
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "saferag_commit": SAFERAG_COMMIT,
        "note": "Opaque response IDs and raw text are hashed; benchmark text is not redistributed.",
        "records": records,
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_blind_audit_sample(
    merged_rows: list[dict[str, Any]],
    csv_output: str | Path,
    key_output: str | Path,
    cases_per_task: int = 4,
    seed: int = 20260712,
) -> None:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in merged_rows:
        if row["generation"]["split"] == "confirmatory":
            grouped[(row["generation"]["task"], row["generation"]["case_id"])].append(row)
    grouped = {key: value for key, value in grouped.items() if len(value) == 3}
    generator = random.Random(seed)
    selected_keys = []
    for task in sorted({task for task, _ in grouped}):
        candidates = sorted(key for key in grouped if key[0] == task)
        selected_keys.extend(generator.sample(candidates, min(cases_per_task, len(candidates))))

    csv_path = Path(csv_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    keys = []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "audit_id",
                "task",
                "case_id",
                "question",
                "answer_A",
                "answer_B",
                "answer_C",
                "best_answer",
                "attack_adopted_A",
                "attack_adopted_B",
                "attack_adopted_C",
                "reviewer_notes",
            ],
        )
        writer.writeheader()
        for audit_index, case_key in enumerate(selected_keys, start=1):
            rows = list(grouped[case_key])
            generator.shuffle(rows)
            labels = ["A", "B", "C"]
            answers = {
                label: row["generation"]["answer"] for label, row in zip(labels, rows, strict=True)
            }
            writer.writerow(
                {
                    "audit_id": f"AUDIT-{audit_index:03d}",
                    "task": case_key[0],
                    "case_id": case_key[1],
                    "question": rows[0]["generation"]["question"],
                    "answer_A": answers["A"],
                    "answer_B": answers["B"],
                    "answer_C": answers["C"],
                }
            )
            keys.append(
                {
                    "audit_id": f"AUDIT-{audit_index:03d}",
                    "mapping": {
                        label: row["generation"]["system"]
                        for label, row in zip(labels, rows, strict=True)
                    },
                }
            )
    key_path = Path(key_output)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with key_path.open("w", encoding="utf-8") as handle:
        for row in keys:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
