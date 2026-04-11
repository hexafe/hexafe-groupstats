"""Diagnostic-only distribution summaries."""

from __future__ import annotations

import numpy as np
from scipy.stats import kurtosis, normaltest, skew

from ..domain.result_models import DistributionProfile, GroupPreprocessResult


def compute_distribution_profiles(
    *,
    metric_name: str,
    preprocessed: tuple[GroupPreprocessResult, ...],
    alpha: float,
) -> tuple[DistributionProfile, ...]:
    rows: list[DistributionProfile] = []
    for group in preprocessed:
        values = group.values
        warnings: list[str] = []
        if values.size == 0:
            rows.append(
                DistributionProfile(
                    metric=metric_name,
                    group=group.label,
                    n=0,
                    skewness=None,
                    excess_kurtosis=None,
                    normality_test="D'Agostino-Pearson",
                    normality_p_value=None,
                    normality_status="empty",
                    warnings=("empty_after_nan_drop",),
                )
            )
            continue

        if group.is_constant:
            skewness = None
            excess_kurtosis = None
            warnings.append("constant_distribution")
        else:
            skewness = float(skew(values, bias=False)) if values.size > 2 else None
            excess_kurtosis = float(kurtosis(values, fisher=True, bias=False)) if values.size > 3 else None
        if skewness is not None and np.isfinite(skewness) and abs(skewness) >= 1.0:
            warnings.append("high_skew")
        if excess_kurtosis is not None and np.isfinite(excess_kurtosis) and abs(excess_kurtosis) >= 2.0:
            warnings.append("high_kurtosis")

        if values.size < 8:
            status = "skipped_n_lt_8"
            p_value = None
        else:
            _, p_value = normaltest(values, nan_policy="omit")
            p_value = None if np.isnan(p_value) else float(p_value)
            status = "failed" if p_value is None else ("rejected" if p_value < alpha else "passed")
            if status == "rejected":
                warnings.append("normaltest_rejected")

        rows.append(
            DistributionProfile(
                metric=metric_name,
                group=group.label,
                n=group.sample_size,
                skewness=skewness,
                excess_kurtosis=excess_kurtosis,
                normality_test="D'Agostino-Pearson",
                normality_p_value=p_value,
                normality_status=status,
                warnings=tuple(warnings),
            )
        )
    return tuple(rows)


__all__ = ["compute_distribution_profiles"]
