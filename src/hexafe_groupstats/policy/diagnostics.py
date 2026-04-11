"""Stable diagnostics and summary helpers."""

from __future__ import annotations

from ..domain.enums import SpecStatus
from ..domain.models import AnalysisPolicy, SpecLimits
from ..domain.result_models import (
    AnalysisDiagnostics,
    AssumptionSummary,
    CapabilityResult,
    DistributionProfile,
    GroupPreprocessResult,
    PairwiseResult,
    PostHocSummary,
)
from ..core.corrections import describe_correction_policy, format_correction_method
from ..core.pairwise import describe_pairwise_strategy
from ..core.posthoc import describe_posthoc_strategy

LOW_N = "LOW N"
IMBALANCED_N = "IMBALANCED N"
SEVERELY_IMBALANCED_N = "SEVERELY IMBALANCED N"
SPEC_QUESTION = "SPEC?"


def _metric_flags(preprocessed: tuple[GroupPreprocessResult, ...], spec_status: SpecStatus) -> tuple[str, ...]:
    flags: list[str] = []
    positive_counts = [group.sample_size for group in preprocessed if group.sample_size > 0]
    if len(positive_counts) >= 2:
        ratio = max(positive_counts) / min(positive_counts)
        if ratio >= 3.0:
            flags.append(SEVERELY_IMBALANCED_N)
        elif ratio >= 2.0:
            flags.append(IMBALANCED_N)
    if spec_status != SpecStatus.EXACT_MATCH:
        flags.append(SPEC_QUESTION)
    return tuple(flags)


def build_diagnostics_comment(
    *,
    policy: AnalysisPolicy,
    pairwise_count: int,
) -> str:
    if policy.spec_status == SpecStatus.LIMIT_MISMATCH:
        return "Analyzed with caution: limits differ across groups; pairwise comparison is enabled and capability is disabled."
    if policy.spec_status == SpecStatus.NOM_MISMATCH:
        return "Descriptive-only: nominal differs across groups; direct pairwise interpretation is disabled."
    if policy.spec_status == SpecStatus.INVALID_SPEC:
        return "Descriptive-only: specification data are missing or invalid; capability metrics are disabled."
    if pairwise_count == 0:
        return "Analyzed: pairwise comparison is enabled but no valid pairwise rows were produced."
    if not policy.allow_capability:
        return "Analyzed with caution: pairwise comparison is enabled and capability metrics are disabled."
    return "Analyzed: pairwise comparison and capability policy are enabled."


def build_diagnostics(
    *,
    preprocessed: tuple[GroupPreprocessResult, ...],
    policy: AnalysisPolicy,
    spec_limits: SpecLimits,
    assumptions: AssumptionSummary,
    pairwise_results: tuple[PairwiseResult, ...],
    posthoc_summary: PostHocSummary | None,
    capability_results: tuple[CapabilityResult, ...],
    distribution_profiles: tuple[DistributionProfile, ...],
    correction_method: str,
) -> AnalysisDiagnostics:
    non_parametric = assumptions.selection_mode.value == "non_parametric"
    equal_var = assumptions.variance_outcome == "passed"
    warnings = tuple(sorted({warning for group in preprocessed for warning in group.warnings}))
    distribution_flags = tuple(
        sorted(
            {
                warning
                for profile in distribution_profiles
                for warning in profile.warnings
            }
        )
    )
    capability_strategy = (
        "Per-group normal-theory capability"
        if capability_results
        else ("Capability disabled by policy" if not policy.allow_capability else "Capability unavailable")
    )
    posthoc_strategy = (
        describe_posthoc_strategy(
            family=posthoc_summary.family,
            correction_method=correction_method,
        )
        if posthoc_summary is not None
        else ""
    )
    return AnalysisDiagnostics(
        comment=build_diagnostics_comment(policy=policy, pairwise_count=len(pairwise_results)),
        warnings=warnings,
        metric_flags=_metric_flags(preprocessed, policy.spec_status),
        restriction_label=policy.analysis_restriction_label,
        pairwise_strategy=describe_pairwise_strategy(
            non_parametric=non_parametric,
            equal_var=equal_var,
            correction_method=correction_method,
        ),
        posthoc_strategy=posthoc_strategy,
        capability_strategy=capability_strategy,
        correction_method=format_correction_method(correction_method),
        correction_policy=describe_correction_policy(correction_method),
        selection_detail=assumptions.selection_detail,
        distribution_flags=distribution_flags,
    )


__all__ = ["build_diagnostics", "build_diagnostics_comment"]
