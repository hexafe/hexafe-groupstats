"""Generic row adapters for dataframe-friendly consumption."""

from __future__ import annotations

from ..domain.result_models import MetricAnalysisResult


def capability_rows(result: MetricAnalysisResult) -> list[dict[str, object]]:
    return [
        {
            "metric": row.metric,
            "group": row.group,
            "n": row.n,
            "mean": row.mean,
            "sigma": row.sigma,
            "lsl": row.lsl,
            "nominal": row.nominal,
            "usl": row.usl,
            "cp": row.cp,
            "cpl": row.cpl,
            "cpu": row.cpu,
            "cpk": row.cpk,
            "cp_ci": row.cp_ci,
            "cpl_ci": row.cpl_ci,
            "cpu_ci": row.cpu_ci,
            "cpk_ci": row.cpk_ci,
            "warnings": list(row.warnings),
        }
        for row in result.capability_results
    ]


def descriptive_rows(result: MetricAnalysisResult) -> list[dict[str, object]]:
    capability_by_group = {row.group: row for row in result.capability_results}
    return [
        {
            "metric": result.metric,
            "group": row.group,
            "n": row.n,
            "mean": row.mean,
            "std": row.std,
            "median": row.median,
            "q1": row.q1,
            "q3": row.q3,
            "iqr": row.iqr,
            "min": row.minimum,
            "max": row.maximum,
            "cp": capability_by_group.get(row.group).cp if row.group in capability_by_group else None,
            "cpl": capability_by_group.get(row.group).cpl if row.group in capability_by_group else None,
            "cpu": capability_by_group.get(row.group).cpu if row.group in capability_by_group else None,
            "cpk": capability_by_group.get(row.group).cpk if row.group in capability_by_group else None,
            "cp_ci": capability_by_group.get(row.group).cp_ci if row.group in capability_by_group else None,
            "cpk_ci": capability_by_group.get(row.group).cpk_ci if row.group in capability_by_group else None,
            "warnings": list(row.warnings),
        }
        for row in result.descriptive_stats
    ]


def pairwise_rows(result: MetricAnalysisResult) -> list[dict[str, object]]:
    return [
        {
            "metric": row.metric,
            "group_a": row.group_a,
            "group_b": row.group_b,
            "test_name": row.test_name,
            "p_value": row.p_value,
            "adjusted_p_value": row.adjusted_p_value,
            "significant": row.significant,
            "effect_size": row.effect_size,
            "effect_type": row.effect_type,
            "method_family": row.method_family,
            "comparison_estimate": row.comparison_estimate,
            "comparison_estimate_label": row.comparison_estimate_label,
            "comparison_ci": row.comparison_ci,
            "effect_size_ci": row.effect_size_ci,
            "warnings": list(row.warnings),
        }
        for row in result.pairwise_results
    ]


def posthoc_rows(result: MetricAnalysisResult) -> list[dict[str, object]]:
    return [
        {
            "metric": row.metric,
            "group_a": row.group_a,
            "group_b": row.group_b,
            "family": row.family,
            "method_name": row.method_name,
            "statistic": row.statistic,
            "raw_p_value": row.raw_p_value,
            "adjusted_p_value": row.adjusted_p_value,
            "significant": row.significant,
            "effect_size": row.effect_size,
            "effect_type": row.effect_type,
            "comparison_estimate": row.comparison_estimate,
            "comparison_estimate_label": row.comparison_estimate_label,
            "comparison_ci": row.comparison_ci,
            "effect_size_ci": row.effect_size_ci,
            "warnings": list(row.warnings),
        }
        for row in result.posthoc_results
    ]


def distribution_rows(result: MetricAnalysisResult) -> list[dict[str, object]]:
    return [
        {
            "metric": row.metric,
            "group": row.group,
            "n": row.n,
            "skewness": row.skewness,
            "excess_kurtosis": row.excess_kurtosis,
            "normality_test": row.normality_test,
            "normality_p_value": row.normality_p_value,
            "normality_status": row.normality_status,
            "warnings": list(row.warnings),
        }
        for row in result.distribution_profiles
    ]


def metric_row(result: MetricAnalysisResult) -> dict[str, object]:
    return {
        "metric": result.metric,
        "backend_used": result.backend_used,
        "group_count": result.group_count,
        "group_order": list(result.group_order),
        "spec_status": result.spec_status.value,
        "analysis_restriction_label": result.analysis_policy.analysis_restriction_label,
        "pairwise_allowed": result.analysis_policy.allow_pairwise,
        "capability_allowed": result.analysis_policy.allow_capability,
        "omnibus_test_name": result.omnibus.test_name,
        "omnibus_p_value": result.omnibus.p_value,
        "omnibus_effect_size": result.omnibus.effect_size,
        "omnibus_effect_type": result.omnibus.effect_type,
        "omnibus_effect_size_ci": result.omnibus.effect_size_ci,
        "diagnostics_comment": result.diagnostics.comment,
        "selection_detail": result.assumptions.selection_detail,
        "posthoc_family": None if result.posthoc_summary is None else result.posthoc_summary.family,
        "posthoc_method_name": None if result.posthoc_summary is None else result.posthoc_summary.method_name,
        "posthoc_strategy": result.diagnostics.posthoc_strategy,
        "capability_strategy": result.diagnostics.capability_strategy,
        "distribution_flags": list(result.diagnostics.distribution_flags),
        "simulation_validation": None
        if result.simulation_validation is None
        else {
            "iterations": result.simulation_validation.iterations,
            "seed": result.simulation_validation.seed,
            "omnibus_significant_rate": result.simulation_validation.omnibus_significant_rate,
            "method_consistency_rate": result.simulation_validation.method_consistency_rate,
            "selected_test_counts": list(result.simulation_validation.selected_test_counts),
        },
        "warnings": list(result.warnings),
        "insights": list(result.insights),
    }


__all__ = [
    "capability_rows",
    "descriptive_rows",
    "distribution_rows",
    "metric_row",
    "pairwise_rows",
    "posthoc_rows",
]
