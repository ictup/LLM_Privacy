"""Build a cross-benchmark evidence and ablation summary from committed results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_systems(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["system"]: row for row in result["confirmatory"]["overall"]}


def build_summary(report_dir: str | Path = "reports") -> dict[str, Any]:
    root = Path(report_dir)
    saferag = _load(root / "saferag_gpt5mini_results.json")
    tab = _load(root / "tab_offline_results.json")
    tensor = _load(root / "tensor_trust_deepseek_results.json")
    privacy = _load(root / "privacylens_deepseek_results.json")
    controls = _load(root / "security_controls_results.json")

    safe_systems = _safe_systems(saferag)
    tab_systems = tab["systems"]
    tensor_systems = tensor["overall"]
    privacy_systems = privacy["overall"]

    integrity_checks = {
        "saferag_complete_paired_cases": (
            saferag["confirmatory"]["n_cases"] == 377
            and all(row["n"] == 377 for row in safe_systems.values())
        ),
        "tab_full_official_test_split": all(
            row["documents"] == 127 and row["gold_mentions"] == 7248
            for row in tab_systems.values()
        ),
        "tensor_trust_complete_paired_cases": (
            tensor["study"]["complete_cases"] == tensor["study"]["planned_cases"] == 100
            and tensor["study"]["generation_rows"] == 600
        ),
        "privacylens_complete_paired_cases": (
            privacy["study"]["complete_cases"] == privacy["study"]["planned_cases"] == 50
            and len(privacy["study"]["judge_models"]) == 2
        ),
        "integrated_control_regression": bool(controls["all_checks_passed"]),
    }

    ablations = {
        "saferag": [
            {
                "system": system,
                "n": row["n"],
                "security_metric": "attack_adoption_rate",
                "security_value": row["attack_adoption_rate"],
                "utility_metric": "option_macro_f1",
                "utility_value": row["option_macro_f1"],
                "grounded_rate": row["grounded_rate"],
            }
            for system, row in safe_systems.items()
        ],
        "tab": [
            {
                "system": system,
                "n": row["documents"],
                "security_metric": "character_f1",
                "security_value": row["character_f1"],
                "utility_metric": "text_retention_rate",
                "utility_value": row["text_retention_rate"],
                "full_coverage_recall": row["full_coverage_recall"],
            }
            for system, row in tab_systems.items()
        ],
        "tensor_trust": [
            {
                "system": system,
                "n": row["attack_success"]["n"],
                "security_metric": "attack_success_rate",
                "security_value": row["attack_success"]["rate"],
                "raw_attack_success": row["raw_attack_success"]["rate"],
                "utility_metric": "valid_access_success",
                "utility_value": row["utility_success"]["rate"],
            }
            for system, row in tensor_systems.items()
        ],
        "privacylens": [
            {
                "system": system,
                "n": row["dual_judge_leakage"]["n"],
                "security_metric": "conservative_dual_judge_leakage",
                "security_value": row["dual_judge_leakage"]["rate"],
                "utility_metric": "dual_judge_helpful_rate",
                "utility_value": row["dual_judge_helpful"]["rate"],
                "block_rate": row["validator_block_rate"]["rate"],
            }
            for system, row in privacy_systems.items()
        ],
    }

    headline = [
        {
            "benchmark": "SafeRAG",
            "evidence_type": "external_peer_reviewed_real_model",
            "n": saferag["confirmatory"]["n_cases"],
            "baseline_security": safe_systems["baseline"]["attack_adoption_rate"],
            "selected_security": safe_systems["ragshield_full"]["attack_adoption_rate"],
            "baseline_utility": safe_systems["baseline"]["option_macro_f1"],
            "selected_utility": safe_systems["ragshield_full"]["option_macro_f1"],
            "selected_system": "ragshield_full",
            "interpretation": "Strong overall reduction; Silver Noise remains weak.",
        },
        {
            "benchmark": "TAB",
            "evidence_type": "external_peer_reviewed_human_annotated_offline",
            "n": tab_systems["combined"]["documents"],
            "baseline_security": tab_systems["regex_rules"]["character_f1"],
            "selected_security": tab_systems["combined"]["character_f1"],
            "baseline_utility": tab_systems["regex_rules"]["text_retention_rate"],
            "selected_utility": tab_systems["combined"]["text_retention_rate"],
            "selected_system": "combined",
            "interpretation": "NER adds coverage but over-redacts document text.",
        },
        {
            "benchmark": "Tensor Trust",
            "evidence_type": "external_peer_reviewed_real_model",
            "n": tensor["study"]["complete_cases"],
            "baseline_security": tensor_systems["baseline"]["attack_success"]["rate"],
            "selected_security": tensor_systems["ragshield_full"]["attack_success"]["rate"],
            "baseline_utility": tensor_systems["baseline"]["utility_success"]["rate"],
            "selected_utility": tensor_systems["ragshield_full"]["utility_success"]["rate"],
            "selected_system": "ragshield_full",
            "interpretation": "Final zero relies on deterministic authorization and output gating.",
        },
        {
            "benchmark": "PrivacyLens",
            "evidence_type": "external_peer_reviewed_real_model_dual_auto_judge",
            "n": privacy["study"]["complete_cases"],
            "baseline_security": privacy_systems["baseline"]["dual_judge_leakage"]["rate"],
            "selected_security": privacy_systems["ragshield_full"]["dual_judge_leakage"]["rate"],
            "baseline_utility": privacy_systems["baseline"]["dual_judge_helpful"]["rate"],
            "selected_utility": privacy_systems["ragshield_full"]["dual_judge_helpful"]["rate"],
            "selected_system": "ragshield_full",
            "interpretation": "Lowest leakage has a 14-point helpfulness cost; prompt-only is the best measured trade-off.",
        },
    ]

    return {
        "summary_version": "ragshield-evidence-v1",
        "all_integrity_checks_passed": all(integrity_checks.values()),
        "integrity_checks": integrity_checks,
        "headline": headline,
        "ablations": ablations,
        "judge_and_scoring_scope": {
            "saferag": "single same-model structured automatic judge",
            "tab": "human span annotations; deterministic offline scoring",
            "tensor_trust": "deterministic secret and access-string scoring",
            "privacylens": "conservative dual-model automatic judging from one provider",
            "controlled_regression": "deterministic assertions on controlled fixtures",
        },
        "evidence_totals": {
            "external_benchmarks": 4,
            "external_evaluated_units": (
                saferag["confirmatory"]["n_cases"]
                + tab_systems["combined"]["documents"]
                + tensor["study"]["complete_cases"]
                + privacy["study"]["complete_cases"]
            ),
            "real_model_response_ids_in_deepseek_pilots": 1200,
            "deterministic_end_to_end_checks": len(controls["checks"]),
        },
        "claim_boundary": {
            "supported": [
                "Measured effects under each frozen benchmark protocol.",
                "Paired module comparisons within SafeRAG, Tensor Trust, and PrivacyLens.",
                "TAB span-detection performance against official human annotations.",
                "Composition and fail-closed behavior of the integrated controls on fixtures.",
            ],
            "unsupported": [
                "Production-grade or universal LLM security.",
                "Generalization to untested model families, languages, or adaptive attacks.",
                "Human-validated accuracy for the automatic LLM judges.",
                "Differential privacy, federated learning, or homomorphic encryption.",
            ],
        },
    }


def _percent(value: float) -> str:
    return f"{value:.1%}"


def write_markdown(summary: dict[str, Any], output: str | Path) -> None:
    lines = [
        "# RAGShield Unified Evidence and Ablation Summary",
        "",
        "## Evidence Scorecard",
        "",
        "| Benchmark | Evidence | N | Security: baseline -> selected | Utility: baseline -> selected | Selected system |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in summary["headline"]:
        lines.append(
            f"| {row['benchmark']} | `{row['evidence_type']}` | {row['n']} | "
            f"{_percent(row['baseline_security'])} -> {_percent(row['selected_security'])} | "
            f"{_percent(row['baseline_utility'])} -> {_percent(row['selected_utility'])} | "
            f"`{row['selected_system']}` |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- **{row['benchmark']}:** {row['interpretation']}" for row in summary["headline"])

    metric_names = {
        "saferag": ("Attack adoption (lower)", "Option F1 (higher)"),
        "tab": ("Character F1 (higher)", "Text retention (higher)"),
        "tensor_trust": ("Attack success (lower)", "Valid access (higher)"),
        "privacylens": ("Leakage (lower)", "Helpful (higher)"),
    }
    lines.extend(["", "## Complete Ablations", ""])
    for benchmark, rows in summary["ablations"].items():
        security_name, utility_name = metric_names[benchmark]
        lines.extend(
            [
                f"### {benchmark.replace('_', ' ').title()}",
                "",
                f"| System | N | {security_name} | {utility_name} |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in rows:
            lines.append(
                f"| `{row['system']}` | {row['n']} | {_percent(row['security_value'])} | "
                f"{_percent(row['utility_value'])} |"
            )
        lines.append("")

    lines.extend(["## Integrity Checks", ""])
    lines.extend(
        f"- [{'x' if passed else ' '}] `{name}`"
        for name, passed in summary["integrity_checks"].items()
    )
    totals = summary["evidence_totals"]
    lines.extend(
        [
            "",
            "## Evidence Totals",
            "",
            f"- External peer-reviewed benchmarks: {totals['external_benchmarks']}",
            f"- Evaluated external units across benchmark primary analyses: {totals['external_evaluated_units']}",
            f"- DeepSeek response IDs in the two new pilots: {totals['real_model_response_ids_in_deepseek_pilots']}",
            f"- Integrated deterministic checks: {totals['deterministic_end_to_end_checks']}",
            "",
            "Counts are not pooled into one effectiveness estimate because the benchmarks measure different tasks.",
            "",
            "## Claim Boundary",
            "",
            "Supported:",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in summary["claim_boundary"]["supported"])
    lines.extend(["", "Not supported:", ""])
    lines.extend(f"- {claim}" for claim in summary["claim_boundary"]["unsupported"])
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="reports")
    parser.add_argument("--results-output", default="reports/evidence_results.json")
    parser.add_argument("--report-output", default="reports/evidence_summary.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_summary(args.report_dir)
    results_path = Path(args.results_output)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, args.report_output)
    print(
        json.dumps(
            {
                "all_integrity_checks_passed": summary["all_integrity_checks_passed"],
                **summary["evidence_totals"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
