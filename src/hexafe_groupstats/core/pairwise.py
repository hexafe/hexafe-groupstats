"""Pairwise comparison logic."""

from __future__ import annotations

import numpy as np

from ..config import AnalysisConfig
from ..domain.enums import SelectionMode
from ..domain.result_models import AssumptionSummary, GroupPreprocessResult, PairwiseResult
from ..native.protocols import GroupStatsBackend
from .confidence_intervals import bootstrap_pairwise_effect_cis
from .corrections import describe_correction_policy, format_correction_method
from .effect_sizes import pairwise_effect_type


def describe_pairwise_strategy(*, non_parametric: bool, equal_var: bool, correction_method: str) -> str:
    correction_label = format_correction_method(correction_method)
    if non_parametric:
        return f"pairwise Mann-Whitney + {correction_label}"
    if equal_var:
        return f"pairwise t-tests + {correction_label}"
    return f"pairwise Welch t-tests + {correction_label}"


def compute_pairwise_results(
    *,
    metric_name: str,
    preprocessed: tuple[GroupPreprocessResult, ...],
    assumptions: AssumptionSummary,
    config: AnalysisConfig,
    backend: GroupStatsBackend,
) -> tuple[PairwiseResult, ...]:
    labels = [group.label for group in preprocessed]
    groups = [group.values for group in preprocessed]

    is_non_parametric = assumptions.selection_mode == SelectionMode.NON_PARAMETRIC
    equal_var = assumptions.variance_outcome == "passed"
    backend_rows = backend.compute_pairwise_batch(
        labels=labels,
        groups=groups,
        alpha=config.alpha,
        correction_method=config.correction_method,
        non_parametric=is_non_parametric,
        equal_var=equal_var,
    )

    effect_type = pairwise_effect_type(non_parametric=is_non_parametric)
    effect_cis: dict[tuple[str, str], tuple[float, float] | None] = {}
    if config.include_effect_size_ci:
        eligible_pairs = [
            (row.group_a, row.group_b)
            for row in backend_rows
            if row.effect_size is not None
        ]
        effect_cis = bootstrap_pairwise_effect_cis(
            backend=backend,
            effect_kernel=effect_type,
            labels=labels,
            groups=groups,
            pairs=eligible_pairs,
            level=config.ci_level,
            iterations=config.ci_bootstrap_iterations,
        )

    return tuple(
        PairwiseResult(
            metric=metric_name,
            group_a=row.group_a,
            group_b=row.group_b,
            test_name=row.test_name,
            p_value=row.p_value,
            adjusted_p_value=row.adjusted_p_value,
            significant=row.significant,
            effect_size=row.effect_size,
            effect_type=effect_type,
            method_family="legacy_pairwise",
            comparison_estimate=(
                float(np.mean(preprocessed[labels.index(row.group_a)].values) - np.mean(preprocessed[labels.index(row.group_b)].values))
                if not is_non_parametric
                and preprocessed[labels.index(row.group_a)].values.size > 0
                and preprocessed[labels.index(row.group_b)].values.size > 0
                else None
            ),
            comparison_estimate_label="mean_difference" if not is_non_parametric else None,
            effect_size_ci=effect_cis.get((row.group_a, row.group_b)),
            warnings=("insufficient_n",) if row.test_name == "insufficient_n" else (),
        )
        for row in backend_rows
    )


__all__ = ["compute_pairwise_results", "describe_correction_policy", "describe_pairwise_strategy", "format_correction_method"]
