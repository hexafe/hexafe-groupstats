"""Typed result models returned by the engine."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .enums import SelectionMode, SpecStatus
from .models import AnalysisPolicy, SpecLimits


@dataclass(frozen=True, slots=True)
class GroupPreprocessResult:
    label: str
    values: NDArray[np.float64]
    sample_size: int
    is_empty: bool
    is_constant: bool
    is_small_n: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NormalityCheckResult:
    group: str
    p_value: float | None
    status: str
    passed: bool | None


@dataclass(frozen=True, slots=True)
class VarianceCheckResult:
    test: str | None
    p_value: float | None
    status: str


@dataclass(frozen=True, slots=True)
class AssumptionSummary:
    normality: tuple[NormalityCheckResult, ...]
    variance_homogeneity: VarianceCheckResult
    normality_outcome: str
    variance_outcome: str
    selection_mode: SelectionMode
    selection_detail: str


@dataclass(frozen=True, slots=True)
class OmnibusTestResult:
    test_name: str | None
    p_value: float | None
    effect_size: float | None = None
    effect_type: str | None = None
    effect_size_ci: tuple[float, float] | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PairwiseResult:
    metric: str
    group_a: str
    group_b: str
    test_name: str
    p_value: float | None
    adjusted_p_value: float | None
    significant: bool
    effect_size: float | None
    effect_type: str
    method_family: str = ""
    comparison_estimate: float | None = None
    comparison_estimate_label: str | None = None
    comparison_ci: tuple[float, float] | None = None
    effect_size_ci: tuple[float, float] | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DescriptiveStats:
    group: str
    n: int
    mean: float
    std: float | None
    median: float
    q1: float
    q3: float
    iqr: float
    minimum: float
    maximum: float
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PostHocComparisonResult:
    metric: str
    group_a: str
    group_b: str
    family: str
    method_name: str
    statistic: float | None
    raw_p_value: float | None
    adjusted_p_value: float | None
    significant: bool
    effect_size: float | None
    effect_type: str
    comparison_estimate: float | None = None
    comparison_estimate_label: str | None = None
    comparison_ci: tuple[float, float] | None = None
    effect_size_ci: tuple[float, float] | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PostHocSummary:
    family: str | None
    method_name: str | None
    correction_method: str | None
    selection_detail: str
    results: tuple[PostHocComparisonResult, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    metric: str
    group: str
    n: int
    mean: float | None
    sigma: float | None
    lsl: float | None
    nominal: float | None
    usl: float | None
    cp: float | None
    cpl: float | None
    cpu: float | None
    cpk: float | None
    ci_level: float | None = None
    cp_ci: tuple[float, float] | None = None
    cpl_ci: tuple[float, float] | None = None
    cpu_ci: tuple[float, float] | None = None
    cpk_ci: tuple[float, float] | None = None
    capability_method: str = "normal_theory"
    sigma_method: str = "sample_stddev"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DistributionProfile:
    metric: str
    group: str
    n: int
    skewness: float | None
    excess_kurtosis: float | None
    normality_test: str | None
    normality_p_value: float | None
    normality_status: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SimulationPairStability:
    group_a: str
    group_b: str
    significant_rate: float
    median_adjusted_p_value: float | None


@dataclass(frozen=True, slots=True)
class SimulationValidationResult:
    iterations: int
    seed: int
    omnibus_significant_rate: float | None
    method_consistency_rate: float | None
    selected_test_counts: tuple[tuple[str, int], ...] = ()
    pairwise_stability: tuple[SimulationPairStability, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetricInsight:
    headline: str
    why: str
    first_action: str
    confidence_or_caution: tuple[str, ...] = ()
    priority_score: float | None = None
    status_class: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisDiagnostics:
    comment: str
    warnings: tuple[str, ...] = ()
    metric_flags: tuple[str, ...] = ()
    restriction_label: str = ""
    pairwise_strategy: str = ""
    posthoc_strategy: str = ""
    capability_strategy: str = ""
    correction_method: str = ""
    correction_policy: str = ""
    selection_detail: str = ""
    distribution_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetricAnalysisResult:
    metric: str
    backend_used: str
    group_count: int
    group_order: tuple[str, ...]
    spec_limits: SpecLimits
    spec_status: SpecStatus
    analysis_policy: AnalysisPolicy
    preprocess: tuple[GroupPreprocessResult, ...]
    assumptions: AssumptionSummary
    omnibus: OmnibusTestResult
    pairwise_results: tuple[PairwiseResult, ...]
    descriptive_stats: tuple[DescriptiveStats, ...]
    diagnostics: AnalysisDiagnostics
    posthoc_summary: PostHocSummary | None = None
    posthoc_results: tuple[PostHocComparisonResult, ...] = ()
    capability_results: tuple[CapabilityResult, ...] = ()
    distribution_profiles: tuple[DistributionProfile, ...] = ()
    simulation_validation: SimulationValidationResult | None = None
    structured_insights: tuple[MetricInsight, ...] = ()
    insights: tuple[str, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)


__all__ = [
    "AnalysisDiagnostics",
    "AssumptionSummary",
    "CapabilityResult",
    "DescriptiveStats",
    "DistributionProfile",
    "GroupPreprocessResult",
    "MetricAnalysisResult",
    "MetricInsight",
    "NormalityCheckResult",
    "OmnibusTestResult",
    "PairwiseResult",
    "PostHocComparisonResult",
    "PostHocSummary",
    "SimulationPairStability",
    "SimulationValidationResult",
    "VarianceCheckResult",
]
