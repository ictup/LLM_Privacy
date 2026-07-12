"""Build the combined interview-facing evidence report from frozen study outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _system(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(row for row in rows if row["system"] == name)


def build_combined_report(saferag: dict[str, Any], canary: dict[str, Any]) -> dict[str, Any]:
    confirmatory = saferag["confirmatory"]
    baseline = _system(confirmatory["overall"], "baseline")
    boundary = _system(confirmatory["overall"], "context_boundary")
    full = _system(confirmatory["overall"], "ragshield_full")
    full_effect = next(
        row
        for row in confirmatory["paired_comparisons"]
        if row["treatment"] == "ragshield_full"
    )
    task_rows = {
        (row["system"], row["task"]): row for row in confirmatory["by_task"]
    }
    task_comparison = []
    for task in ("ICC", "SA", "SN", "WDoS"):
        base_task = task_rows[("baseline", task)]
        full_task = task_rows[("ragshield_full", task)]
        task_comparison.append(
            {
                "task": task,
                "n": base_task["n"],
                "baseline_attack_adoption": base_task["attack_adoption_rate"],
                "full_attack_adoption": full_task["attack_adoption_rate"],
                "absolute_difference": round(
                    full_task["attack_adoption_rate"] - base_task["attack_adoption_rate"],
                    6,
                ),
            }
        )

    canary_baseline = _system(canary["systems"], "baseline")
    canary_boundary = _system(canary["systems"], "context_boundary")
    canary_full = _system(canary["systems"], "ragshield_full")
    generation_cost = saferag["generation_cost"][
        "estimated_usd_at_documented_standard_rates"
    ]
    judge_cost = saferag["judge_cost"]["estimated_usd_at_documented_standard_rates"]
    canary_cost = canary["execution_evidence"][
        "estimated_usd_at_documented_standard_rates"
    ]
    return {
        "title": "RAGShield GPT-5 mini Interview Evidence",
        "model": saferag["generator_model"],
        "saferag": {
            "protocol": saferag["protocol_version"],
            "analysis": saferag["analysis_version"],
            "complete_confirmatory_cases": confirmatory["n_cases"],
            "available_confirmatory_cases": confirmatory["n_available_cases"],
            "excluded_cases": confirmatory["excluded_incomplete_cases"],
            "generation_rows": saferag["execution_evidence"]["generation_rows"],
            "judgment_rows": saferag["execution_evidence"]["judgment_rows"],
            "judge_consistency_flagged_rows": saferag["execution_evidence"][
                "judge_consistency_flagged_rows"
            ],
            "baseline": baseline,
            "context_boundary": boundary,
            "ragshield_full": full,
            "full_relative_attack_reduction": round(
                (baseline["attack_adoption_rate"] - full["attack_adoption_rate"])
                / baseline["attack_adoption_rate"],
                6,
            ),
            "full_paired_effect": full_effect,
            "by_task": task_comparison,
        },
        "controlled_canary": {
            "protocol": canary["protocol_version"],
            "rows": canary["execution_evidence"]["rows"],
            "baseline": canary_baseline,
            "context_boundary": canary_boundary,
            "ragshield_full": canary_full,
        },
        "cost": {
            "saferag_generation_usd": generation_cost,
            "saferag_judging_usd": judge_cost,
            "controlled_canary_usd": canary_cost,
            "final_evidence_total_usd": round(generation_cost + judge_cost + canary_cost, 4),
        },
        "claim_boundary": {
            "supported": [
                "Under the frozen protocol, RAGShield reduced judge-assessed SafeRAG attack adoption.",
                "The complete stack blocked all measured synthetic canary violations in this run.",
                "The largest SafeRAG gains were on WDoS and ICC; SN remained the hardest task.",
            ],
            "not_supported": [
                "Production-grade security against arbitrary adaptive attacks.",
                "Differential privacy, federated learning, or homomorphic encryption.",
                "Independent judge validity before blinded human review is completed.",
            ],
        },
    }


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_markdown(report: dict[str, Any], output: str | Path) -> None:
    saferag = report["saferag"]
    canary = report["controlled_canary"]
    baseline = saferag["baseline"]
    boundary = saferag["context_boundary"]
    full = saferag["ragshield_full"]
    effect = saferag["full_paired_effect"]
    attack_effect = effect["attack_adoption_difference"]
    utility_effect = effect["utility_f1_difference"]
    p_value = effect["attack_adoption_mcnemar"]["p_value"]
    p_text = "<0.0001" if p_value < 0.0001 else f"{p_value:.4f}"

    lines = [
        "# RAGShield: Final GPT-5 Mini Interview Evidence",
        "",
        "## Main Finding",
        "",
        (
            f"On {saferag['complete_confirmatory_cases']} complete paired SafeRAG "
            "confirmatory cases, the full RAGShield stack "
            f"reduced judge-assessed attack adoption from {_pct(baseline['attack_adoption_rate'])} "
            f"to {_pct(full['attack_adoption_rate'])}, a "
            f"{_pct(saferag['full_relative_attack_reduction'])} relative reduction."
        ),
        "",
        "## External Benchmark Evidence",
        "",
        "| System | N | Attack adoption | Grounded | Utility F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in (baseline, boundary, full):
        lines.append(
            f"| {row['system']} | {row['n']} | {_pct(row['attack_adoption_rate'])} | "
            f"{_pct(row['grounded_rate'])} | {_pct(row['option_macro_f1'])} |"
        )
    lines.extend(
        [
            "",
            (
                "Full defense minus baseline: "
                f"{attack_effect['difference'] * 100:.1f} percentage points "
                f"(95% CI {attack_effect['ci_low'] * 100:.1f} to "
                f"{attack_effect['ci_high'] * 100:.1f}); McNemar p {p_text}."
            ),
            (
                "Utility F1 difference: "
                f"{utility_effect['difference']:.3f} "
                f"(95% CI {utility_effect['ci_low']:.3f} to "
                f"{utility_effect['ci_high']:.3f}); inconclusive because the interval crosses zero."
            ),
            "",
            "| Task | N | Baseline adoption | Full adoption | Difference |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in saferag["by_task"]:
        lines.append(
            f"| {row['task']} | {row['n']} | {_pct(row['baseline_attack_adoption'])} | "
            f"{_pct(row['full_attack_adoption'])} | "
            f"{row['absolute_difference'] * 100:.1f} pp |"
        )

    lines.extend(
        [
            "",
            "## Controlled Privacy and Tool Evidence",
            "",
            "| System | N | ASR | Leakage | Unauthorized tools | Benign success |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in (canary["baseline"], canary["context_boundary"], canary["ragshield_full"]):
        lines.append(
            f"| {row['system']} | {row['n']} | {_pct(row['attack_success_rate'])} | "
            f"{_pct(row['leakage_rate'])} | {_pct(row['unauthorized_tool_call_rate'])} | "
            f"{_pct(row['benign_success_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Execution and Cost",
            "",
            f"- Model snapshot: `{report['model']}`",
            f"- SafeRAG protocol: `{saferag['protocol']}` / `{saferag['analysis']}`",
            f"- SafeRAG generation/judgment rows: {saferag['generation_rows']} / "
            f"{saferag['judgment_rows']}",
            f"- Automated-judge consistency flags: {saferag['judge_consistency_flagged_rows']}",
            f"- Controlled canary API responses: {canary['rows']}",
            f"- Final evidence-run estimated API cost: ${report['cost']['final_evidence_total_usd']:.2f}",
            "",
            "## Claim Boundary",
            "",
            "Supported:",
        ]
    )
    lines.extend(f"- {item}" for item in report["claim_boundary"]["supported"])
    lines.extend(["", "Not supported:"])
    lines.extend(f"- {item}" for item in report["claim_boundary"]["not_supported"])
    lines.extend(
        [
            "",
            "## Required Follow-Up",
            "",
            "Complete the generated 48-answer blinded human review before treating the "
            "automated judge as independently validated.",
        ]
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saferag", default="reports/saferag_gpt5mini_results.json")
    parser.add_argument("--canary", default="reports/synthetic_gpt5mini_results.json")
    parser.add_argument("--json-output", default="reports/interview_evidence.json")
    parser.add_argument("--report-output", default="reports/interview_evidence_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    saferag = json.loads(Path(args.saferag).read_text(encoding="utf-8"))
    canary = json.loads(Path(args.canary).read_text(encoding="utf-8"))
    report = build_combined_report(saferag, canary)
    Path(args.json_output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_markdown(report, args.report_output)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
