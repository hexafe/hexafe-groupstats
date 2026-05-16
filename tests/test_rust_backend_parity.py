from __future__ import annotations

import math

import pytest

from hexafe_groupstats import AnalysisConfig, analyze_metric, compare_groups
from hexafe_groupstats.native.backends import BackendUnavailableError


def _rust_result(groups, **config_kwargs):
    try:
        return compare_groups(groups, config=AnalysisConfig(backend="rust", **config_kwargs))
    except BackendUnavailableError as exc:
        pytest.skip(f"Rust backend unavailable: {exc}")


def test_rust_parametric_pairwise_matches_python_backend():
    groups = {
        "A": [1.0, 1.1, 1.2, 1.3, 1.4],
        "B": [1.4, 1.5, 1.6, 1.7, 1.8],
    }

    python = compare_groups(groups, config=AnalysisConfig(backend="python"))
    rust = _rust_result(groups)

    assert rust.backend_used == "rust"
    assert rust.omnibus.test_name == python.omnibus.test_name
    assert rust.pairwise_results[0].test_name == python.pairwise_results[0].test_name
    assert rust.pairwise_results[0].adjusted_p_value == pytest.approx(
        python.pairwise_results[0].adjusted_p_value,
        rel=1e-12,
        abs=1e-12,
    )
    assert rust.pairwise_results[0].effect_size == pytest.approx(
        python.pairwise_results[0].effect_size,
        rel=1e-12,
        abs=1e-12,
    )


def test_rust_non_parametric_path_uses_python_fallback_with_same_result():
    groups = {
        "A": [0.1, 0.2, 0.2, 0.3, 0.8, 2.1, 5.5],
        "B": [0.2, 0.3, 0.4, 0.6, 1.4, 3.5, 9.0],
    }

    python = compare_groups(groups, config=AnalysisConfig(backend="python"))
    rust = _rust_result(groups)

    assert rust.backend_used == "rust"
    assert rust.omnibus.test_name == python.omnibus.test_name
    assert rust.pairwise_results[0].test_name == "Mann-Whitney U"
    assert rust.pairwise_results[0].adjusted_p_value == python.pairwise_results[0].adjusted_p_value
    assert rust.pairwise_results[0].effect_size == python.pairwise_results[0].effect_size


def test_rust_backend_uses_python_bootstrap_fallback_for_ci_parity():
    groups = {
        "A": [1.0, 1.1, 1.2, 1.3, 1.4],
        "B": [1.4, 1.5, 1.6, 1.7, 1.8],
    }
    config = {
        "include_effect_size_ci": True,
        "ci_bootstrap_iterations": 16,
    }

    python = compare_groups(groups, config=AnalysisConfig(backend="python", **config))
    rust = _rust_result(groups, **config)

    assert rust.pairwise_results[0].effect_size_ci == python.pairwise_results[0].effect_size_ci


def test_auto_backend_remains_python_even_when_rust_is_available():
    auto = analyze_metric("metric", {"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="auto"))

    assert auto.backend_used == "python"


def test_rust_can_be_enabled_for_auto_when_available():
    try:
        result = analyze_metric(
            "metric",
            {"A": [1, 2, 3], "B": [2, 3, 4]},
            config=AnalysisConfig(backend="auto", enable_rust_in_auto=True),
        )
    except BackendUnavailableError:
        pytest.skip("Rust backend unavailable")

    assert result.backend_used in {"python", "rust"}
    if result.backend_used == "rust":
        assert math.isfinite(result.pairwise_results[0].adjusted_p_value)
