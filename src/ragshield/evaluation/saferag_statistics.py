"""Paired statistics for the confirmatory SafeRAG study."""

from __future__ import annotations

import math
import random
from statistics import mean


def wilson_interval(values: list[bool], z: float = 1.959964) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    count = len(values)
    proportion = sum(values) / count
    denominator = 1 + z * z / count
    center = (proportion + z * z / (2 * count)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / count + z * z / (4 * count * count))
        / denominator
    )
    return (round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6))


def paired_bootstrap_difference(
    pairs: list[tuple[float, float]],
    samples: int = 5000,
    seed: int = 20260712,
) -> dict[str, float | int]:
    """Return treatment minus baseline with a paired percentile interval."""

    if not pairs:
        return {"n": 0, "difference": 0.0, "ci_low": 0.0, "ci_high": 0.0}
    differences = [treatment - baseline for baseline, treatment in pairs]
    generator = random.Random(seed)
    bootstrap = []
    for _ in range(samples):
        bootstrap.append(mean(generator.choice(differences) for _ in differences))
    bootstrap.sort()
    low_index = int(0.025 * (samples - 1))
    high_index = int(0.975 * (samples - 1))
    return {
        "n": len(pairs),
        "difference": round(mean(differences), 6),
        "ci_low": round(bootstrap[low_index], 6),
        "ci_high": round(bootstrap[high_index], 6),
    }


def exact_mcnemar(
    pairs: list[tuple[bool, bool]],
) -> dict[str, float | int]:
    baseline_only = sum(baseline and not treatment for baseline, treatment in pairs)
    treatment_only = sum(treatment and not baseline for baseline, treatment in pairs)
    discordant = baseline_only + treatment_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = min(baseline_only, treatment_only)
        probability = sum(
            math.comb(discordant, index) * (0.5**discordant)
            for index in range(tail + 1)
        )
        p_value = min(1.0, 2 * probability)
    return {
        "baseline_only": baseline_only,
        "treatment_only": treatment_only,
        "discordant": discordant,
        "p_value": round(p_value, 8),
    }
