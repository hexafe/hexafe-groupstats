from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from hexafe_groupstats import AnalysisConfig, SpecLimits, analyze_metric


def test_empty_group_is_safe_and_marks_insufficient_pairwise():
    result = analyze_metric("metric", {"A": [], "B": [1.0, 2.0, 3.0]})

    assert result.omnibus.test_name is None
    assert "empty_after_nan_drop" in result.preprocess[0].warnings
    assert len(result.pairwise_results) == 1
    assert result.pairwise_results[0].test_name == "insufficient_n"


def test_constant_group_is_flagged():
    result = analyze_metric("metric", {"A": [1.0, 1.0, 1.0], "B": [1.0, 2.0, 3.0]})

    assert result.preprocess[0].is_constant is True
    assert "constant_values" in result.preprocess[0].warnings
    assert "contains_constant_group" in result.omnibus.warnings


def test_group_with_n_lt_2_blocks_omnibus():
    result = analyze_metric("metric", {"A": [1.0], "B": [2.0, 3.0, 4.0]})

    assert result.omnibus.test_name is None
    assert "contains_group_with_n_lt_2" in result.omnibus.warnings
    assert result.pairwise_results[0].test_name == "insufficient_n"


def test_n_lt_3_skips_shapiro_and_uses_non_parametric_path():
    result = analyze_metric("metric", {"A": [1.0, 1.1], "B": [2.0, 2.2]})

    assert result.assumptions.normality_outcome == "skipped"
    assert all(check.status == "skipped_n_lt_3" for check in result.assumptions.normality)
    assert result.omnibus.test_name == "Mann-Whitney U"


def test_n_gt_5000_skips_shapiro_with_controlled_path():
    base = np.linspace(0.0, 1.0, 5001)
    result = analyze_metric("metric", {"A": base, "B": base + 0.1})

    assert all(check.status == "skipped_n_gt_5000" for check in result.assumptions.normality)
    assert result.omnibus.test_name == "Mann-Whitney U"


def test_unequal_variance_two_group_path_uses_welch():
    base = norm.ppf(np.linspace(0.1, 0.9, 12))
    result = analyze_metric("metric", {"A": base, "B": base * 5 + 1})

    assert result.assumptions.normality_outcome == "passed"
    assert result.assumptions.variance_outcome == "failed"
    assert result.omnibus.test_name == "Welch t-test"


def test_non_normal_two_group_path_uses_mann_whitney():
    skewed = np.array([0.1, 0.2, 0.2, 0.3, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4, 5.5, 8.9])
    result = analyze_metric("metric", {"A": skewed, "B": skewed * 1.1 + 0.5})

    assert result.assumptions.normality_outcome == "failed"
    assert result.omnibus.test_name == "Mann-Whitney U"
    assert result.pairwise_results[0].effect_type == "cliffs_delta"


def test_three_group_anova_path():
    base = norm.ppf(np.linspace(0.1, 0.9, 12))
    result = analyze_metric("metric", {"A": base, "B": base + 0.2, "C": base - 0.2})

    assert result.omnibus.test_name == "ANOVA"
    assert result.omnibus.effect_type == "eta_squared"
    assert result.posthoc_summary is not None
    assert result.posthoc_summary.family in {"tukey_hsd", "tukey_kramer"}
    assert len(result.posthoc_results) == 3


def test_three_group_welch_anova_path():
    base = norm.ppf(np.linspace(0.1, 0.9, 12))
    result = analyze_metric("metric", {"A": base, "B": base * 3 + 0.3, "C": base * 5 - 0.3})

    assert result.omnibus.test_name == "Welch ANOVA"
    assert result.posthoc_summary is not None
    assert result.posthoc_summary.family == "games_howell"


def test_three_group_kruskal_path():
    skewed = np.array([0.1, 0.2, 0.2, 0.3, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4, 5.5, 8.9])
    result = analyze_metric(
        "metric",
        {"A": skewed, "B": skewed * 1.1 + 0.5, "C": skewed * 0.9 + 0.2},
    )

    assert result.omnibus.test_name == "Kruskal-Wallis"
    assert result.posthoc_summary is not None
    assert result.posthoc_summary.family == "dunn"


def test_effect_size_ci_can_be_requested():
    base = norm.ppf(np.linspace(0.1, 0.9, 12))
    result = analyze_metric(
        "metric",
        {"A": base, "B": base * 3 + 0.3, "C": base * 5 - 0.3},
        config=AnalysisConfig(include_effect_size_ci=True, ci_bootstrap_iterations=64),
    )

    assert result.omnibus.effect_size_ci is not None
    assert all(
        row.effect_size_ci is not None
        for row in result.pairwise_results
        if row.effect_size is not None
    )


def test_pairwise_correction_methods_change_adjusted_values():
    groups = {
        "A": [0.1, 0.2, 0.2, 0.3, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4, 5.5, 8.9],
        "B": [0.2, 0.3, 0.3, 0.4, 0.4, 0.6, 0.9, 1.4, 2.2, 3.5, 5.6, 9.0],
        "C": [1.5, 1.8, 2.2, 2.5, 3.1, 4.0, 5.2, 6.8, 8.8, 11.4, 14.8, 19.2],
    }
    holm = analyze_metric("metric", groups, config=AnalysisConfig(correction_method="holm"))
    bh = analyze_metric("metric", groups, config=AnalysisConfig(correction_method="bh"))

    holm_values = [row.adjusted_p_value for row in holm.pairwise_results]
    bh_values = [row.adjusted_p_value for row in bh.pairwise_results]

    assert holm_values != bh_values


def test_invalid_spec_records_disable_pairwise():
    result = analyze_metric(
        "metric",
        {"A": [1.0, 2.0, 3.0], "B": [2.0, 3.0, 4.0]},
        spec_limits=[SpecLimits(lsl=0.0, nominal=2.0, usl=5.0), SpecLimits(lsl=None, nominal=2.0, usl=5.0)],
    )

    assert result.spec_status.value == "INVALID_SPEC"
    assert result.analysis_policy.allow_pairwise is False
    assert result.pairwise_results == ()


def test_capability_results_are_computed_for_exact_match_specs():
    base = norm.ppf(np.linspace(0.05, 0.95, 40))
    result = analyze_metric(
        "metric",
        {"A": base + 10.0, "B": base + 10.2},
        spec_limits=SpecLimits(lsl=8.0, nominal=10.0, usl=12.0),
    )

    assert len(result.capability_results) == 2
    assert all(row.cp is not None for row in result.capability_results)
    assert all(row.cpk is not None for row in result.capability_results)
    assert all(row.cp_ci is not None for row in result.capability_results)


def test_distribution_profiles_and_simulation_validation_are_optional():
    base = norm.ppf(np.linspace(0.1, 0.9, 12))
    result = analyze_metric(
        "metric",
        {"A": base, "B": base + 0.2, "C": base - 0.2},
        config=AnalysisConfig(simulation_validation_iterations=8, simulation_random_seed=7),
    )

    assert len(result.distribution_profiles) == 3
    assert result.simulation_validation is not None
    assert result.simulation_validation.iterations == 8
    assert result.simulation_validation.selected_test_counts
