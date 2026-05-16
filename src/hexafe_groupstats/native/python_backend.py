"""Reference pure-Python backend."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.stats import mannwhitneyu, rankdata, ttest_ind_from_stats

from .protocols import GroupStatsBackend, PairwiseBackendRow


def _coerce_scalar_to_float64_or_nan(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _normalize_array(values: Any) -> NDArray[np.float64]:
    if isinstance(values, np.ndarray):
        if values.dtype == np.float64 and values.flags.c_contiguous and values.ndim == 1:
            return values
        if values.dtype != object:
            array = np.asarray(values, dtype=np.float64)
            if array.ndim != 1:
                array = array.reshape(-1)
            return np.ascontiguousarray(array, dtype=np.float64)
        iterable = values.reshape(-1)
    else:
        try:
            array = np.asarray(values, dtype=np.float64)
        except (TypeError, ValueError):
            iterable = values
        else:
            if array.ndim != 1:
                array = array.reshape(-1)
            return np.ascontiguousarray(array, dtype=np.float64)
    array = np.array([_coerce_scalar_to_float64_or_nan(value) for value in iterable], dtype=np.float64)
    return np.ascontiguousarray(array, dtype=np.float64)


def _cohen_d(sample_a: NDArray[np.float64], sample_b: NDArray[np.float64]) -> float | None:
    if sample_a.size < 2 or sample_b.size < 2:
        return None
    var_a = float(np.var(sample_a, ddof=1))
    var_b = float(np.var(sample_b, ddof=1))
    pooled_num = ((sample_a.size - 1) * var_a) + ((sample_b.size - 1) * var_b)
    pooled_den = sample_a.size + sample_b.size - 2
    if pooled_den <= 0:
        return None
    pooled = pooled_num / pooled_den
    if pooled <= 0:
        return None
    return float((np.mean(sample_a) - np.mean(sample_b)) / np.sqrt(pooled))


def _cohen_d_from_stats(
    mean_a: float,
    std_a: float,
    n_a: int,
    mean_b: float,
    std_b: float,
    n_b: int,
) -> float | None:
    if n_a < 2 or n_b < 2:
        return None
    pooled_num = ((n_a - 1) * (std_a**2)) + ((n_b - 1) * (std_b**2))
    pooled_den = n_a + n_b - 2
    if pooled_den <= 0:
        return None
    pooled = pooled_num / pooled_den
    if pooled <= 0:
        return None
    return float((mean_a - mean_b) / np.sqrt(pooled))


def _cliffs_delta(sample_a: NDArray[np.float64], sample_b: NDArray[np.float64]) -> float | None:
    if sample_a.size == 0 or sample_b.size == 0:
        return None
    n_a = sample_a.size
    n_b = sample_b.size
    pooled = np.concatenate((sample_a, sample_b))
    ranks = rankdata(pooled, method="average")
    rank_sum_a = float(np.sum(ranks[:n_a], dtype=np.float64))
    u_statistic = rank_sum_a - (n_a * (n_a + 1) / 2.0)
    return float((2.0 * u_statistic) / (n_a * n_b) - 1.0)


def _normalize_correction_method(method: str) -> str:
    normalized = method.strip().lower().replace("-", "_")
    aliases = {
        "holm_bonferroni": "holm",
        "benjamini_hochberg": "bh",
        "fdr_bh": "bh",
    }
    return aliases.get(normalized, normalized)


def _adjust_pvalues(p_values: list[float | None], method: str) -> list[float | None]:
    indexed = [(idx, p) for idx, p in enumerate(p_values) if p is not None and not np.isnan(p)]
    adjusted: list[float | None] = [None] * len(p_values)
    if not indexed:
        return adjusted

    sorted_pairs = sorted(indexed, key=lambda item: item[1])
    m = len(sorted_pairs)
    normalized = _normalize_correction_method(method)
    if normalized == "holm":
        running_max = 0.0
        for rank, (original_index, p_value) in enumerate(sorted_pairs):
            corrected = min(1.0, p_value * (m - rank))
            running_max = max(running_max, corrected)
            adjusted[original_index] = float(running_max)
        return adjusted
    if normalized == "bh":
        running_min = 1.0
        for reverse_rank, (original_index, p_value) in enumerate(reversed(sorted_pairs), start=1):
            rank = m - reverse_rank + 1
            corrected = min(1.0, p_value * m / rank)
            running_min = min(running_min, corrected)
            adjusted[original_index] = float(running_min)
        return adjusted
    raise ValueError(f"Unsupported correction method: {method}")


def _effect_from_kernel(effect_kernel: str, groups: list[NDArray[np.float64]]) -> float | None:
    if effect_kernel == "cohen_d":
        if len(groups) != 2:
            return None
        return _cohen_d(groups[0], groups[1])
    if effect_kernel == "cliffs_delta":
        if len(groups) != 2:
            return None
        return _cliffs_delta(groups[0], groups[1])
    if effect_kernel in {"eta_squared", "omega_squared"}:
        if len(groups) < 2:
            return None
        sizes = np.array([group.size for group in groups], dtype=np.float64)
        if np.any(sizes < 2):
            return None
        values = np.concatenate(groups)
        grand_mean = float(np.mean(values))
        ss_between = float(np.sum([group.size * (np.mean(group) - grand_mean) ** 2 for group in groups]))
        ss_within = float(np.sum([np.sum((group - np.mean(group)) ** 2) for group in groups]))
        ss_total = ss_between + ss_within
        if np.isclose(ss_total, 0.0):
            return None
        if effect_kernel == "eta_squared":
            return float(ss_between / ss_total)
        df_between = float(len(groups) - 1)
        df_within = float(values.size - len(groups))
        if df_within <= 0:
            return None
        ms_within = ss_within / df_within
        denom = ss_total + ms_within
        if np.isclose(denom, 0.0):
            return None
        return float(max(0.0, (ss_between - (df_between * ms_within)) / denom))
    raise ValueError(f"Unsupported effect kernel: {effect_kernel}")


def _bootstrap_cohen_d_ci(
    *,
    groups: list[NDArray[np.float64]],
    level: float,
    iterations: int,
    seed: int,
) -> tuple[float, float] | None:
    if len(groups) != 2:
        return None
    left, right = groups
    if left.size < 2 or right.size < 2:
        return None

    rng = np.random.default_rng(seed)
    resolved_iterations = max(1, int(iterations))
    left_samples = left[rng.integers(0, left.size, size=(resolved_iterations, left.size))]
    right_samples = right[rng.integers(0, right.size, size=(resolved_iterations, right.size))]
    left_var = np.var(left_samples, axis=1, ddof=1)
    right_var = np.var(right_samples, axis=1, ddof=1)
    pooled_den = left.size + right.size - 2
    if pooled_den <= 0:
        return None
    pooled = (((left.size - 1) * left_var) + ((right.size - 1) * right_var)) / pooled_den
    valid = pooled > 0.0
    if not np.any(valid):
        return None
    estimates = (np.mean(left_samples, axis=1) - np.mean(right_samples, axis=1)) / np.sqrt(pooled)
    estimates = estimates[valid & np.isfinite(estimates)]
    if estimates.size == 0:
        return None
    lower_q = ((1.0 - level) / 2.0) * 100.0
    upper_q = (1.0 - (1.0 - level) / 2.0) * 100.0
    return (
        float(np.percentile(estimates, lower_q)),
        float(np.percentile(estimates, upper_q)),
    )


def _pairwise_stats(
    sample_a: NDArray[np.float64],
    sample_b: NDArray[np.float64],
    *,
    mean_a: float,
    std_a: float,
    mean_b: float,
    std_b: float,
    non_parametric: bool,
    equal_var: bool,
) -> tuple[str, float | None, float | None]:
    if sample_a.size < 2 or sample_b.size < 2:
        return ("insufficient_n", None, None)
    if non_parametric:
        statistic, p_value = mannwhitneyu(sample_a, sample_b, alternative="two-sided")
        effect_size = float((2.0 * statistic) / (sample_a.size * sample_b.size) - 1.0)
        return ("Mann-Whitney U", None if np.isnan(p_value) else float(p_value), effect_size)
    _, p_value = ttest_ind_from_stats(
        mean1=mean_a,
        std1=std_a,
        nobs1=sample_a.size,
        mean2=mean_b,
        std2=std_b,
        nobs2=sample_b.size,
        equal_var=equal_var,
    )
    return (
        "Student t-test" if equal_var else "Welch t-test",
        None if np.isnan(p_value) else float(p_value),
        _cohen_d_from_stats(mean_a, std_a, sample_a.size, mean_b, std_b, sample_b.size),
    )


class PythonBackend(GroupStatsBackend):
    """Always-available backend implementation."""

    name = "python"

    def coerce_numeric_sequence(self, values: Any) -> NDArray[np.float64]:
        return _normalize_array(values)

    def compute_pairwise_batch(
        self,
        *,
        labels: list[str],
        groups: list[NDArray[np.float64]],
        alpha: float,
        correction_method: str,
        non_parametric: bool,
        equal_var: bool,
    ) -> list[PairwiseBackendRow]:
        raw_rows: list[PairwiseBackendRow] = []
        raw_p_values: list[float | None] = []
        means = [float(np.mean(group)) if group.size else np.nan for group in groups]
        stds = [float(np.std(group, ddof=1)) if group.size > 1 else np.nan for group in groups]
        for left_index, right_index in combinations(range(len(labels)), 2):
            sample_a = groups[left_index]
            sample_b = groups[right_index]
            test_name, p_value, effect_size = _pairwise_stats(
                sample_a,
                sample_b,
                mean_a=means[left_index],
                std_a=stds[left_index],
                mean_b=means[right_index],
                std_b=stds[right_index],
                non_parametric=non_parametric,
                equal_var=equal_var,
            )
            raw_p_values.append(p_value)
            raw_rows.append(
                PairwiseBackendRow(
                    group_a=labels[left_index],
                    group_b=labels[right_index],
                    test_name=test_name,
                    p_value=p_value,
                    effect_size=effect_size,
                    adjusted_p_value=None,
                    significant=False,
                )
            )
        adjusted = _adjust_pvalues(raw_p_values, correction_method)
        return [
            PairwiseBackendRow(
                group_a=row.group_a,
                group_b=row.group_b,
                test_name=row.test_name,
                p_value=row.p_value,
                effect_size=row.effect_size,
                adjusted_p_value=adjusted_p_value,
                significant=bool(adjusted_p_value is not None and adjusted_p_value < alpha),
            )
            for row, adjusted_p_value in zip(raw_rows, adjusted)
        ]

    def bootstrap_percentile_ci(
        self,
        *,
        effect_kernel: str,
        groups: list[NDArray[np.float64]],
        level: float,
        iterations: int,
        seed: int,
    ) -> tuple[float, float] | None:
        if effect_kernel == "cohen_d" and len(groups) == 2:
            return _bootstrap_cohen_d_ci(
                groups=groups,
                level=level,
                iterations=iterations,
                seed=seed,
            )

        rng = np.random.default_rng(seed)
        estimates: list[float] = []
        resolved_iterations = max(1, int(iterations))
        for _ in range(resolved_iterations):
            sampled_groups = [
                group[rng.integers(0, group.size, group.size)]
                for group in groups
                if group.size > 0
            ]
            if len(sampled_groups) != len(groups):
                return None
            estimate = _effect_from_kernel(effect_kernel, sampled_groups)
            if estimate is not None and not np.isnan(estimate):
                estimates.append(float(estimate))
        if not estimates:
            return None
        lower_q = ((1.0 - level) / 2.0) * 100.0
        upper_q = (1.0 - (1.0 - level) / 2.0) * 100.0
        return (
            float(np.percentile(estimates, lower_q)),
            float(np.percentile(estimates, upper_q)),
        )

    def bootstrap_percentile_ci_batch(
        self,
        *,
        effect_kernel: str,
        groups: list[NDArray[np.float64]],
        pairs: list[tuple[int, int]],
        level: float,
        iterations: int,
        seed: int,
    ) -> list[tuple[float, float] | None]:
        output: list[tuple[float, float] | None] = []
        for offset, (left_index, right_index) in enumerate(pairs):
            output.append(
                self.bootstrap_percentile_ci(
                    effect_kernel=effect_kernel,
                    groups=[groups[left_index], groups[right_index]],
                    level=level,
                    iterations=iterations,
                    seed=seed + offset,
                )
            )
        return output


__all__ = ["PythonBackend"]
