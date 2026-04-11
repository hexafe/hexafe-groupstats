"""Assumption checks used by the omnibus selector."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.stats import levene, shapiro

from ..domain.enums import SelectionMode
from ..domain.result_models import (
    AssumptionSummary,
    GroupPreprocessResult,
    NormalityCheckResult,
    VarianceCheckResult,
)


def safe_shapiro(values: np.ndarray) -> tuple[float | None, str]:
    n = int(values.size)
    if n < 3:
        return None, "skipped_n_lt_3"
    if n > 5000:
        return None, "skipped_n_gt_5000"
    if n > 1 and np.isclose(np.std(values, ddof=1), 0.0):
        return None, "skipped_constant"
    stat, p_value = shapiro(values)
    if np.isnan(p_value):
        return None, "failed"
    return float(p_value), "ok"


def assess_assumptions(
    preprocessed: tuple[GroupPreprocessResult, ...],
    *,
    alpha: float,
    variance_test: str,
) -> AssumptionSummary:
    usable = [group for group in preprocessed if not group.is_empty]
    if len(usable) < 2:
        return AssumptionSummary(
            normality=tuple(),
            variance_homogeneity=VarianceCheckResult(test=None, p_value=None, status="not_checked"),
            normality_outcome="not_checked",
            variance_outcome="not_checked",
            selection_mode=SelectionMode.UNAVAILABLE,
            selection_detail="Assumption checks were not completed because fewer than two usable groups were available.",
        )

    normality_rows: list[NormalityCheckResult] = []
    normality_failures = 0
    any_normality_measured = False
    any_normality_skipped = False
    for group in usable:
        p_value, status = safe_shapiro(group.values)
        passed = None if p_value is None else bool(p_value >= alpha)
        if passed is False:
            normality_failures += 1
        if passed is not None:
            any_normality_measured = True
        if status != "ok":
            any_normality_skipped = True
        normality_rows.append(
            NormalityCheckResult(
                group=group.label,
                p_value=p_value,
                status=status,
                passed=passed,
            )
        )

    if normality_failures > 0:
        normality_outcome = "failed"
        normality_detail = (
            "At least one usable group failed Shapiro-Wilk, so the selection falls back to the non-parametric path."
        )
    elif any_normality_measured and not any_normality_skipped:
        normality_outcome = "passed"
        normality_detail = "All usable groups passed Shapiro-Wilk, so parametric paths remain eligible."
    elif any_normality_measured and any_normality_skipped:
        normality_outcome = "mixed"
        normality_detail = (
            "Some groups passed Shapiro-Wilk but at least one check was skipped, so selection treats normality as unresolved."
        )
    else:
        normality_outcome = "skipped"
        normality_detail = "All usable normality checks were skipped, so selection treats normality as unresolved."

    center = "median" if str(variance_test).strip().lower() == "brown_forsythe" else "mean"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        _, lev_p = levene(*(group.values for group in usable), center=center)
    variance_passed = bool(not np.isnan(lev_p) and lev_p >= alpha)
    variance_outcome = "passed" if variance_passed else "failed"
    variance_result = VarianceCheckResult(
        test="Brown-Forsythe" if center == "median" else "Levene",
        p_value=None if np.isnan(lev_p) else float(lev_p),
        status=variance_outcome,
    )

    if any(group.sample_size < 2 for group in usable):
        return AssumptionSummary(
            normality=tuple(normality_rows),
            variance_homogeneity=variance_result,
            normality_outcome=normality_outcome,
            variance_outcome=variance_outcome,
            selection_mode=SelectionMode.UNAVAILABLE,
            selection_detail="At least one usable group had fewer than 2 values, so no omnibus test was selected.",
        )

    normality_pass = normality_failures == 0 and any_normality_measured and not any_normality_skipped
    if normality_pass:
        selection_mode = (
            SelectionMode.PARAMETRIC_EQUAL_VARIANCE if variance_passed else SelectionMode.PARAMETRIC_UNEQUAL_VARIANCE
        )
        selection_detail = (
            "Shapiro-Wilk passed for all usable groups and the variance test passed, so the equal-variance parametric path was used."
            if variance_passed
            else "Shapiro-Wilk passed for all usable groups but the variance test failed, so the unequal-variance parametric path was used."
        )
    else:
        selection_mode = SelectionMode.NON_PARAMETRIC
        selection_detail = normality_detail

    return AssumptionSummary(
        normality=tuple(normality_rows),
        variance_homogeneity=variance_result,
        normality_outcome=normality_outcome,
        variance_outcome=variance_outcome,
        selection_mode=selection_mode,
        selection_detail=selection_detail,
    )


__all__ = ["assess_assumptions", "safe_shapiro"]

