"""Main analysis orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from ..config import AnalysisConfig
from ..domain.result_models import AnalysisDiagnostics, MetricAnalysisResult
from ..native.backends import resolve_backend
from ..policy.analysis_policy import resolve_analysis_policy
from ..policy.diagnostics import build_diagnostics
from ..policy.insights import build_metric_insights
from ..policy.spec_comparability import resolve_spec_context
from .assumptions import assess_assumptions
from .capability import compute_capability_results
from .descriptive import compute_descriptive_stats
from .distribution import compute_distribution_profiles
from .omnibus import run_omnibus_test
from .posthoc import run_posthoc_analysis
from .preprocess import preprocess_groups
from .simulation import run_simulation_validation


def analyze_groups(
    *,
    metric_name: str,
    groups: Mapping[str, Sequence[Any]],
    spec_limits: Any = None,
    config: AnalysisConfig | None = None,
) -> MetricAnalysisResult:
    config = config or AnalysisConfig()
    backend = resolve_backend(config.backend, enable_rust_in_auto=config.enable_rust_in_auto)

    normalized_groups = {str(label): values for label, values in groups.items()}
    preprocessed = preprocess_groups(
        normalized_groups,
        backend=backend,
        small_n_threshold=config.small_n_threshold,
    )
    descriptive_stats = compute_descriptive_stats(preprocessed)
    canonical_spec_limits, spec_status = resolve_spec_context(
        spec_limits,
        missing_means_exact_match=True,
    )
    policy = resolve_analysis_policy(spec_status)
    assumptions = assess_assumptions(
        preprocessed,
        alpha=config.alpha,
        variance_test=config.variance_test,
    )
    omnibus = run_omnibus_test(
        preprocessed,
        assumptions=assumptions,
        config=config,
        backend=backend,
    )
    pairwise_results, posthoc_summary = (
        run_posthoc_analysis(
            metric_name=metric_name,
            preprocessed=preprocessed,
            assumptions=assumptions,
            config=config,
            backend=backend,
        )
        if policy.allow_pairwise
        else (tuple(), None)
    )
    posthoc_results = tuple() if posthoc_summary is None else posthoc_summary.results
    capability_results = compute_capability_results(
        metric_name=metric_name,
        preprocessed=preprocessed,
        spec_limits=canonical_spec_limits,
        policy=policy,
        alpha=config.capability_alpha,
    )
    distribution_profiles = (
        compute_distribution_profiles(
            metric_name=metric_name,
            preprocessed=preprocessed,
            alpha=config.alpha,
        )
        if config.distribution_diagnostics
        else tuple()
    )
    diagnostics = build_diagnostics(
        preprocessed=preprocessed,
        policy=policy,
        spec_limits=canonical_spec_limits,
        assumptions=assumptions,
        pairwise_results=pairwise_results,
        posthoc_summary=posthoc_summary,
        capability_results=capability_results,
        distribution_profiles=distribution_profiles,
        correction_method=config.correction_method,
    )
    insights = build_metric_insights(
        metric_name=metric_name,
        descriptive_stats=descriptive_stats,
        pairwise_results=pairwise_results,
        policy=policy,
        diagnostics=diagnostics,
    )
    simulation_validation = (
        run_simulation_validation(
            metric_name=metric_name,
            groups=normalized_groups,
            spec_limits=canonical_spec_limits,
            config=replace(
                config,
                include_effect_size_ci=False,
                distribution_diagnostics=False,
                simulation_validation_iterations=0,
            ),
            iterations=config.simulation_validation_iterations,
            seed=config.simulation_random_seed,
        )
        if config.simulation_validation_iterations > 0
        else None
    )
    warnings = tuple(
        sorted(
            {
                warning
                for group in preprocessed
                for warning in group.warnings
            }
            | set(omnibus.warnings)
            | set(() if posthoc_summary is None else posthoc_summary.warnings)
            | {
                warning
                for capability in capability_results
                for warning in capability.warnings
            }
            | {
                warning
                for profile in distribution_profiles
                for warning in profile.warnings
            }
            | set(() if simulation_validation is None else simulation_validation.warnings)
        )
    )
    return MetricAnalysisResult(
        metric=metric_name,
        backend_used=backend.name,
        group_count=len(preprocessed),
        group_order=tuple(group.label for group in preprocessed),
        spec_limits=canonical_spec_limits,
        spec_status=spec_status,
        analysis_policy=policy,
        preprocess=preprocessed,
        assumptions=assumptions,
        omnibus=omnibus,
        pairwise_results=pairwise_results,
        descriptive_stats=descriptive_stats,
        diagnostics=diagnostics,
        posthoc_summary=posthoc_summary,
        posthoc_results=posthoc_results,
        capability_results=capability_results,
        distribution_profiles=distribution_profiles,
        simulation_validation=simulation_validation,
        insights=insights,
        warnings=warnings,
    )


__all__ = ["analyze_groups"]
