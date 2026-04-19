"""Opt-in Monte Carlo / bootstrap stability validation."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from ..config import AnalysisConfig
from ..domain.result_models import SimulationPairStability, SimulationValidationResult


def run_simulation_validation(
    *,
    metric_name: str,
    groups: Mapping[str, Sequence[Any]],
    spec_limits: Any,
    config: AnalysisConfig,
    iterations: int,
    seed: int,
) -> SimulationValidationResult:
    from .engine import analyze_groups

    rng = np.random.default_rng(seed)
    warnings: list[str] = []
    if iterations < 50:
        warnings.append("simulation_low_iterations")

    selected_test_counts: Counter[str] = Counter()
    omnibus_significant = 0
    pair_significant_counts: dict[tuple[str, str], int] = defaultdict(int)
    pair_adjusted_values: dict[tuple[str, str], list[float]] = defaultdict(list)

    normalized_groups = {str(label): np.asarray(values, dtype=object) for label, values in groups.items()}
    for _ in range(iterations):
        sampled_groups = {}
        for label, values in normalized_groups.items():
            if values.size == 0:
                sampled_groups[label] = []
                continue
            indices = rng.integers(0, values.size, values.size)
            sampled_groups[label] = values[indices].tolist()

        result = analyze_groups(
            metric_name=metric_name,
            groups=sampled_groups,
            spec_limits=spec_limits,
            config=config,
        )
        selected_test_counts[str(result.omnibus.test_name)] += 1
        if result.omnibus.p_value is not None and result.omnibus.p_value < config.alpha:
            omnibus_significant += 1
        for row in result.pairwise_results:
            pair = (row.group_a, row.group_b)
            if row.significant:
                pair_significant_counts[pair] += 1
            if row.adjusted_p_value is not None:
                pair_adjusted_values[pair].append(float(row.adjusted_p_value))

    pairwise_stability = tuple(
        SimulationPairStability(
            group_a=group_a,
            group_b=group_b,
            significant_rate=pair_significant_counts[(group_a, group_b)] / iterations,
            median_adjusted_p_value=(
                float(np.median(pair_adjusted_values[(group_a, group_b)]))
                if pair_adjusted_values[(group_a, group_b)]
                else None
            ),
        )
        for group_a, group_b in sorted(pair_adjusted_values)
    )

    most_common_method = selected_test_counts.most_common(1)
    method_consistency_rate = (
        float(most_common_method[0][1] / iterations)
        if most_common_method
        else None
    )
    return SimulationValidationResult(
        iterations=iterations,
        seed=seed,
        omnibus_significant_rate=float(omnibus_significant / iterations) if iterations > 0 else None,
        method_consistency_rate=method_consistency_rate,
        selected_test_counts=tuple(sorted(selected_test_counts.items())),
        pairwise_stability=pairwise_stability,
        warnings=tuple(warnings),
    )


__all__ = ["run_simulation_validation"]
