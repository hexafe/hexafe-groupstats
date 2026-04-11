"""Dedicated post-hoc procedures for multi-group analysis."""

from __future__ import annotations

import inspect
from itertools import combinations

import numpy as np
from scipy.stats import norm, rankdata, studentized_range, tiecorrect, tukey_hsd

from ..config import AnalysisConfig
from ..domain.enums import PostHocMethod, SelectionMode
from ..domain.result_models import (
    AssumptionSummary,
    GroupPreprocessResult,
    PairwiseResult,
    PostHocComparisonResult,
    PostHocSummary,
)
from ..native.protocols import GroupStatsBackend
from .confidence_intervals import bootstrap_pairwise_effect_cis
from .corrections import adjust_pvalues, format_correction_method
from .effect_sizes import cliffs_delta, cohen_d
from .pairwise import compute_pairwise_results, describe_pairwise_strategy


def select_posthoc_family(
    *,
    assumptions: AssumptionSummary,
    group_count: int,
    config: AnalysisConfig,
) -> str | None:
    if group_count < 3:
        return None

    configured = str(config.posthoc_method).strip().lower()
    if configured == PostHocMethod.LEGACY.value:
        return None
    if configured == PostHocMethod.TUKEY.value:
        return "tukey"
    if configured == PostHocMethod.GAMES_HOWELL.value:
        return "games_howell"
    if configured == PostHocMethod.DUNN.value:
        return "dunn"

    if assumptions.selection_mode == SelectionMode.PARAMETRIC_EQUAL_VARIANCE:
        return "tukey"
    if assumptions.selection_mode == SelectionMode.PARAMETRIC_UNEQUAL_VARIANCE:
        return "games_howell"
    if assumptions.selection_mode == SelectionMode.NON_PARAMETRIC:
        return "dunn"
    return None


def describe_posthoc_strategy(*, family: str | None, correction_method: str) -> str:
    if family is None:
        return ""
    if family == "tukey":
        return "Tukey HSD / Tukey-Kramer"
    if family == "games_howell":
        return "Games-Howell"
    if family == "dunn":
        return f"Dunn + {format_correction_method(correction_method)}"
    return family


def _pairwise_effect_ci_lookup(
    *,
    backend: GroupStatsBackend,
    family: str,
    labels: list[str],
    groups: list[np.ndarray],
    pairs: list[tuple[str, str]],
    config: AnalysisConfig,
) -> dict[tuple[str, str], tuple[float, float] | None]:
    if not config.include_effect_size_ci:
        return {}
    effect_kernel = "cliffs_delta" if family == "dunn" else "cohen_d"
    return bootstrap_pairwise_effect_cis(
        backend=backend,
        effect_kernel=effect_kernel,
        labels=labels,
        groups=groups,
        pairs=pairs,
        level=config.ci_level,
        iterations=config.ci_bootstrap_iterations,
    )


def _tukey_supports_equal_var() -> bool:
    try:
        return "equal_var" in inspect.signature(tukey_hsd).parameters
    except (TypeError, ValueError):  # pragma: no cover - defensive fallback
        return False


def _games_howell_row(
    *,
    metric_name: str,
    group_a: str,
    group_b: str,
    left: np.ndarray,
    right: np.ndarray,
    group_count: int,
    alpha: float,
    ci_level: float,
    effect_size_ci: tuple[float, float] | None,
) -> PostHocComparisonResult:
    mean_left = float(np.mean(left))
    mean_right = float(np.mean(right))
    diff = mean_left - mean_right
    var_left = float(np.var(left, ddof=1))
    var_right = float(np.var(right, ddof=1))
    se_sq = (var_left / left.size) + (var_right / right.size)
    if not np.isfinite(se_sq) or se_sq <= 0.0:
        return PostHocComparisonResult(
            metric=metric_name,
            group_a=group_a,
            group_b=group_b,
            family="games_howell",
            method_name="Games-Howell",
            statistic=None,
            raw_p_value=None,
            adjusted_p_value=None,
            significant=False,
            effect_size=cohen_d(left, right),
            effect_type="cohen_d",
            comparison_estimate=diff,
            comparison_estimate_label="mean_difference",
            comparison_ci=None,
            effect_size_ci=effect_size_ci,
            warnings=("games_howell_unavailable",),
        )

    se = float(np.sqrt(se_sq))
    df_denom = ((var_left / left.size) ** 2) / max(left.size - 1, 1) + ((var_right / right.size) ** 2) / max(right.size - 1, 1)
    df = None if not np.isfinite(df_denom) or np.isclose(df_denom, 0.0) else float((se_sq**2) / df_denom)
    if df is None or not np.isfinite(df) or df <= 0.0:
        return PostHocComparisonResult(
            metric=metric_name,
            group_a=group_a,
            group_b=group_b,
            family="games_howell",
            method_name="Games-Howell",
            statistic=None,
            raw_p_value=None,
            adjusted_p_value=None,
            significant=False,
            effect_size=cohen_d(left, right),
            effect_type="cohen_d",
            comparison_estimate=diff,
            comparison_estimate_label="mean_difference",
            comparison_ci=None,
            effect_size_ci=effect_size_ci,
            warnings=("games_howell_df_unavailable",),
        )

    q_stat = abs(diff) * np.sqrt(2.0) / se
    adjusted_p = float(studentized_range.sf(q_stat, group_count, df))
    q_crit = float(studentized_range.ppf(ci_level, group_count, df))
    margin = q_crit * se / np.sqrt(2.0)
    return PostHocComparisonResult(
        metric=metric_name,
        group_a=group_a,
        group_b=group_b,
        family="games_howell",
        method_name="Games-Howell",
        statistic=diff,
        raw_p_value=adjusted_p,
        adjusted_p_value=adjusted_p,
        significant=bool(adjusted_p < alpha),
        effect_size=cohen_d(left, right),
        effect_type="cohen_d",
        comparison_estimate=diff,
        comparison_estimate_label="mean_difference",
        comparison_ci=(diff - margin, diff + margin),
        effect_size_ci=effect_size_ci,
    )


def _run_games_howell_fallback(
    *,
    metric_name: str,
    labels: list[str],
    groups: list[np.ndarray],
    backend: GroupStatsBackend,
    config: AnalysisConfig,
) -> PostHocSummary:
    pairs = [(labels[left], labels[right]) for left, right in combinations(range(len(labels)), 2)]
    effect_cis = _pairwise_effect_ci_lookup(
        backend=backend,
        family="games_howell",
        labels=labels,
        groups=groups,
        pairs=pairs,
        config=config,
    )
    rows = []
    for left_index, right_index in combinations(range(len(labels)), 2):
        group_a = labels[left_index]
        group_b = labels[right_index]
        rows.append(
            _games_howell_row(
                metric_name=metric_name,
                group_a=group_a,
                group_b=group_b,
                left=groups[left_index],
                right=groups[right_index],
                group_count=len(groups),
                alpha=config.alpha,
                ci_level=config.ci_level,
                effect_size_ci=effect_cis.get((group_a, group_b)),
            )
        )

    return PostHocSummary(
        family="games_howell",
        method_name="Games-Howell",
        correction_method=None,
        selection_detail="Unequal-variance parametric multi-group path selected Games-Howell.",
        results=tuple(rows),
        warnings=("games_howell_manual_fallback",),
    )


def _run_tukey_family(
    *,
    metric_name: str,
    labels: list[str],
    groups: list[np.ndarray],
    backend: GroupStatsBackend,
    config: AnalysisConfig,
    equal_var: bool,
) -> PostHocSummary:
    warnings: list[str] = []
    try:
        if equal_var:
            result = tukey_hsd(*groups)
        elif _tukey_supports_equal_var():
            result = tukey_hsd(*groups, equal_var=False)
        else:
            return _run_games_howell_fallback(
                metric_name=metric_name,
                labels=labels,
                groups=groups,
                backend=backend,
                config=config,
            )
        comparison_ci = result.confidence_interval(confidence_level=config.ci_level)
    except Exception as exc:  # pragma: no cover - defensive fallback
        warnings.append(f"posthoc_error:{exc}")
        return PostHocSummary(
            family=None,
            method_name=None,
            correction_method=None,
            selection_detail="Dedicated post-hoc failed and legacy pairwise fallback should be used.",
            warnings=tuple(warnings),
        )

    balanced = len({group.size for group in groups}) == 1
    family = "games_howell" if not equal_var else ("tukey_hsd" if balanced else "tukey_kramer")
    method_name = (
        "Games-Howell"
        if family == "games_howell"
        else ("Tukey HSD" if family == "tukey_hsd" else "Tukey-Kramer")
    )
    pairs = [(labels[left], labels[right]) for left, right in combinations(range(len(labels)), 2)]
    effect_cis = _pairwise_effect_ci_lookup(
        backend=backend,
        family=family,
        labels=labels,
        groups=groups,
        pairs=pairs,
        config=config,
    )

    rows: list[PostHocComparisonResult] = []
    for left, right in combinations(range(len(labels)), 2):
        group_a = labels[left]
        group_b = labels[right]
        statistic = float(result.statistic[left, right])
        adjusted_p = float(result.pvalue[left, right])
        rows.append(
            PostHocComparisonResult(
                metric=metric_name,
                group_a=group_a,
                group_b=group_b,
                family=family,
                method_name=method_name,
                statistic=statistic,
                raw_p_value=adjusted_p,
                adjusted_p_value=adjusted_p,
                significant=bool(adjusted_p < config.alpha),
                effect_size=cohen_d(groups[left], groups[right]),
                effect_type="cohen_d",
                comparison_estimate=statistic,
                comparison_estimate_label="mean_difference",
                comparison_ci=(
                    float(comparison_ci.low[left, right]),
                    float(comparison_ci.high[left, right]),
                ),
                effect_size_ci=effect_cis.get((group_a, group_b)),
            )
        )

    selection_detail = (
        "Equal-variance parametric multi-group path selected Tukey HSD."
        if family == "tukey_hsd"
        else (
            "Equal-variance parametric multi-group path selected Tukey-Kramer for unequal group sizes."
            if family == "tukey_kramer"
            else "Unequal-variance parametric multi-group path selected Games-Howell."
        )
    )
    return PostHocSummary(
        family=family,
        method_name=method_name,
        correction_method=None,
        selection_detail=selection_detail,
        results=tuple(rows),
        warnings=tuple(warnings),
    )


def _dunn_statistic(
    left_ranks: np.ndarray,
    right_ranks: np.ndarray,
    *,
    total_n: int,
    tie_factor: float,
) -> float | None:
    if left_ranks.size == 0 or right_ranks.size == 0 or tie_factor <= 0:
        return None
    mean_rank_left = float(np.mean(left_ranks))
    mean_rank_right = float(np.mean(right_ranks))
    denominator = np.sqrt((total_n * (total_n + 1) / 12.0) * tie_factor * ((1.0 / left_ranks.size) + (1.0 / right_ranks.size)))
    if np.isclose(denominator, 0.0):
        return None
    return float((mean_rank_left - mean_rank_right) / denominator)


def _run_dunn_family(
    *,
    metric_name: str,
    labels: list[str],
    groups: list[np.ndarray],
    backend: GroupStatsBackend,
    config: AnalysisConfig,
) -> PostHocSummary:
    values = np.concatenate(groups)
    ranks = rankdata(values, method="average")
    tie_factor = float(tiecorrect(ranks))
    pairs = [(labels[left], labels[right]) for left, right in combinations(range(len(labels)), 2)]
    effect_cis = _pairwise_effect_ci_lookup(
        backend=backend,
        family="dunn",
        labels=labels,
        groups=groups,
        pairs=pairs,
        config=config,
    )

    raw_rows: list[tuple[str, str, float | None, float | None, float | None]] = []
    raw_p_values: list[float | None] = []
    offset = 0
    ranked_groups: list[np.ndarray] = []
    for group in groups:
        ranked_groups.append(ranks[offset: offset + group.size])
        offset += group.size

    for left, right in combinations(range(len(labels)), 2):
        statistic = _dunn_statistic(
            ranked_groups[left],
            ranked_groups[right],
            total_n=values.size,
            tie_factor=tie_factor,
        )
        raw_p = None if statistic is None else float(2.0 * norm.sf(abs(statistic)))
        raw_rows.append(
            (
                labels[left],
                labels[right],
                statistic,
                raw_p,
                float(np.mean(ranked_groups[left]) - np.mean(ranked_groups[right])),
            )
        )
        raw_p_values.append(raw_p)

    adjusted = adjust_pvalues(raw_p_values, config.correction_method)
    rows: list[PostHocComparisonResult] = []
    for (group_a, group_b, statistic, raw_p, mean_rank_diff), adjusted_p in zip(raw_rows, adjusted):
        left = labels.index(group_a)
        right = labels.index(group_b)
        rows.append(
            PostHocComparisonResult(
                metric=metric_name,
                group_a=group_a,
                group_b=group_b,
                family="dunn",
                method_name="Dunn",
                statistic=statistic,
                raw_p_value=raw_p,
                adjusted_p_value=adjusted_p,
                significant=bool(adjusted_p is not None and adjusted_p < config.alpha),
                effect_size=cliffs_delta(groups[left], groups[right]),
                effect_type="cliffs_delta",
                comparison_estimate=mean_rank_diff,
                comparison_estimate_label="mean_rank_difference",
                comparison_ci=None,
                effect_size_ci=effect_cis.get((group_a, group_b)),
                warnings=() if statistic is not None else ("dunn_unavailable",),
            )
        )

    return PostHocSummary(
        family="dunn",
        method_name="Dunn",
        correction_method=config.correction_method,
        selection_detail="Non-parametric multi-group path selected Dunn pairwise comparisons.",
        results=tuple(rows),
        warnings=(),
    )


def run_posthoc_analysis(
    *,
    metric_name: str,
    preprocessed: tuple[GroupPreprocessResult, ...],
    assumptions: AssumptionSummary,
    config: AnalysisConfig,
    backend: GroupStatsBackend,
) -> tuple[tuple[PairwiseResult, ...], PostHocSummary | None]:
    usable = [group for group in preprocessed if not group.is_empty]
    if len(usable) < 3:
        return compute_pairwise_results(
            metric_name=metric_name,
            preprocessed=preprocessed,
            assumptions=assumptions,
            config=config,
            backend=backend,
        ), None

    family = select_posthoc_family(
        assumptions=assumptions,
        group_count=len(usable),
        config=config,
    )
    if family is None:
        return compute_pairwise_results(
            metric_name=metric_name,
            preprocessed=preprocessed,
            assumptions=assumptions,
            config=config,
            backend=backend,
        ), None

    labels = [group.label for group in usable]
    groups = [group.values for group in usable]
    if family == "tukey":
        summary = _run_tukey_family(
            metric_name=metric_name,
            labels=labels,
            groups=groups,
            backend=backend,
            config=config,
            equal_var=True,
        )
    elif family == "games_howell":
        summary = _run_tukey_family(
            metric_name=metric_name,
            labels=labels,
            groups=groups,
            backend=backend,
            config=config,
            equal_var=False,
        )
    else:
        summary = _run_dunn_family(
            metric_name=metric_name,
            labels=labels,
            groups=groups,
            backend=backend,
            config=config,
        )

    if summary.family is None:
        legacy = compute_pairwise_results(
            metric_name=metric_name,
            preprocessed=preprocessed,
            assumptions=assumptions,
            config=config,
            backend=backend,
        )
        fallback = PostHocSummary(
            family="legacy_pairwise",
            method_name="Legacy pairwise fallback",
            correction_method=config.correction_method,
            selection_detail=summary.selection_detail,
            warnings=summary.warnings,
        )
        return legacy, fallback

    pairwise_rows = tuple(
        PairwiseResult(
            metric=row.metric,
            group_a=row.group_a,
            group_b=row.group_b,
            test_name=row.method_name,
            p_value=row.raw_p_value,
            adjusted_p_value=row.adjusted_p_value,
            significant=row.significant,
            effect_size=row.effect_size,
            effect_type=row.effect_type,
            method_family=row.family,
            comparison_estimate=row.comparison_estimate,
            comparison_estimate_label=row.comparison_estimate_label,
            comparison_ci=row.comparison_ci,
            effect_size_ci=row.effect_size_ci,
            warnings=row.warnings,
        )
        for row in summary.results
    )
    return pairwise_rows, summary


__all__ = [
    "describe_posthoc_strategy",
    "describe_pairwise_strategy",
    "run_posthoc_analysis",
    "select_posthoc_family",
]
