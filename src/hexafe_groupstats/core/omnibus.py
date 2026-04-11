"""Omnibus test selection and execution."""

from __future__ import annotations

import numpy as np
from scipy.stats import f, f_oneway, kruskal, mannwhitneyu, ttest_ind

from ..config import AnalysisConfig
from ..domain.enums import SelectionMode
from ..domain.result_models import AssumptionSummary, GroupPreprocessResult, OmnibusTestResult
from .confidence_intervals import bootstrap_effect_ci
from .effect_sizes import eta_or_omega_squared, omnibus_effect_type
from ..native.protocols import GroupStatsBackend


def welch_anova_p_value(groups: list[np.ndarray]) -> float | None:
    sizes = np.array([len(group) for group in groups], dtype=float)
    variances = np.array([np.var(group, ddof=1) for group in groups], dtype=float)
    means = np.array([np.mean(group) for group in groups], dtype=float)

    if np.any(sizes < 2) or np.any(variances <= 0):
        return None
    weights = sizes / variances
    weight_sum = float(np.sum(weights))
    if weight_sum <= 0:
        return None

    weighted_mean = float(np.sum(weights * means) / weight_sum)
    k = float(len(groups))
    numerator = np.sum(weights * (means - weighted_mean) ** 2) / (k - 1.0)
    correction = 1.0 + (2.0 * (k - 2.0) / (k**2 - 1.0)) * np.sum(
        ((1.0 - (weights / weight_sum)) ** 2) / (sizes - 1.0)
    )
    if np.isclose(correction, 0.0):
        return None

    f_stat = numerator / correction
    df1 = k - 1.0
    df2_denom = 3.0 * np.sum(((1.0 - (weights / weight_sum)) ** 2) / (sizes - 1.0))
    if np.isclose(df2_denom, 0.0):
        return None
    df2 = (k**2 - 1.0) / df2_denom
    if df1 <= 0 or df2 <= 0:
        return None
    p_value = 1.0 - f.cdf(f_stat, df1, df2)
    return None if np.isnan(p_value) else float(p_value)


def run_omnibus_test(
    preprocessed: tuple[GroupPreprocessResult, ...],
    *,
    assumptions: AssumptionSummary,
    config: AnalysisConfig,
    backend: GroupStatsBackend,
) -> OmnibusTestResult:
    usable = [group for group in preprocessed if not group.is_empty]
    arrays = [group.values for group in usable]
    warnings: list[str] = []

    if len(usable) < 2:
        warnings.append("fewer_than_two_non_empty_groups")
        return OmnibusTestResult(test_name=None, p_value=None, warnings=tuple(warnings))

    if any(group.sample_size < 2 for group in usable):
        warnings.append("contains_group_with_n_lt_2")
        return OmnibusTestResult(test_name=None, p_value=None, warnings=tuple(warnings))

    p_value: float | None = None
    test_name: str | None = None

    try:
        if len(usable) == 2:
            if assumptions.selection_mode == SelectionMode.PARAMETRIC_EQUAL_VARIANCE:
                _, p_value = ttest_ind(arrays[0], arrays[1], equal_var=True, nan_policy="omit")
                test_name = "Student t-test"
            elif assumptions.selection_mode == SelectionMode.PARAMETRIC_UNEQUAL_VARIANCE:
                _, p_value = ttest_ind(arrays[0], arrays[1], equal_var=False, nan_policy="omit")
                test_name = "Welch t-test"
            else:
                _, p_value = mannwhitneyu(arrays[0], arrays[1], alternative="two-sided")
                test_name = "Mann-Whitney U"
        else:
            if assumptions.selection_mode == SelectionMode.PARAMETRIC_EQUAL_VARIANCE:
                _, p_value = f_oneway(*arrays)
                test_name = "ANOVA"
            elif assumptions.selection_mode == SelectionMode.PARAMETRIC_UNEQUAL_VARIANCE:
                p_value = welch_anova_p_value(arrays)
                test_name = "Welch ANOVA"
            else:
                _, p_value = kruskal(*arrays)
                test_name = "Kruskal-Wallis"
    except ValueError as exc:
        warnings.append(f"test_error:{exc}")

    if p_value is None:
        warnings.append("test_returned_nan")

    overall_effect = None
    overall_effect_type = None
    overall_ci = None
    if len(usable) > 2:
        overall_effect_type = omnibus_effect_type(config.multi_group_effect)
        overall_effect = eta_or_omega_squared(arrays, use_omega=overall_effect_type == "omega_squared")
        if config.include_effect_size_ci and overall_effect is not None:
            overall_ci = bootstrap_effect_ci(
                backend=backend,
                effect_kernel=overall_effect_type,
                groups=arrays,
                level=config.ci_level,
                iterations=config.ci_bootstrap_iterations,
            )

    if any(group.is_constant for group in usable):
        warnings.append("contains_constant_group")

    return OmnibusTestResult(
        test_name=test_name,
        p_value=None if p_value is None or np.isnan(p_value) else float(p_value),
        effect_size=overall_effect,
        effect_type=overall_effect_type,
        effect_size_ci=overall_ci,
        warnings=tuple(warnings),
    )


__all__ = ["run_omnibus_test", "welch_anova_p_value"]

