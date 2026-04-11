"""Effect-size helpers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.stats import rankdata


def cohen_d(sample_a: NDArray[np.float64], sample_b: NDArray[np.float64]) -> float | None:
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


def cliffs_delta(sample_a: NDArray[np.float64], sample_b: NDArray[np.float64]) -> float | None:
    if sample_a.size == 0 or sample_b.size == 0:
        return None
    n_a = sample_a.size
    n_b = sample_b.size
    pooled = np.concatenate((sample_a, sample_b))
    ranks = rankdata(pooled, method="average")
    rank_sum_a = float(np.sum(ranks[:n_a], dtype=np.float64))
    u_statistic = rank_sum_a - (n_a * (n_a + 1) / 2.0)
    return float((2.0 * u_statistic) / (n_a * n_b) - 1.0)


def eta_or_omega_squared(groups: list[NDArray[np.float64]], *, use_omega: bool) -> float | None:
    if len(groups) < 2:
        return None
    sizes = np.array([group.size for group in groups], dtype=float)
    if np.any(sizes < 2):
        return None
    values = np.concatenate(groups)
    grand_mean = float(np.mean(values))
    ss_between = float(np.sum([group.size * (np.mean(group) - grand_mean) ** 2 for group in groups]))
    ss_within = float(np.sum([np.sum((group - np.mean(group)) ** 2) for group in groups]))
    ss_total = ss_between + ss_within
    if np.isclose(ss_total, 0.0):
        return None
    if not use_omega:
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


def pairwise_effect_type(*, non_parametric: bool) -> str:
    return "cliffs_delta" if non_parametric else "cohen_d"


def omnibus_effect_type(multi_group_effect: str) -> str:
    normalized = str(multi_group_effect).strip().lower()
    return "omega_squared" if normalized == "omega_squared" else "eta_squared"


__all__ = [
    "cliffs_delta",
    "cohen_d",
    "eta_or_omega_squared",
    "omnibus_effect_type",
    "pairwise_effect_type",
]

