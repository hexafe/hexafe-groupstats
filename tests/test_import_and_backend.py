from __future__ import annotations

import os
import subprocess
import sys

import pytest

from hexafe_groupstats import (
    AnalysisConfig,
    compare_groups,
    describe_correction_policy,
    describe_pairwise_strategy,
    format_correction_method,
)
from hexafe_groupstats.native.backends import BackendUnavailableError


def test_auto_backend_uses_python():
    result = compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="auto"))
    assert result.backend_used == "python"


def test_python_backend_explicitly_works():
    result = compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="python"))
    assert result.backend_used == "python"


def test_rust_backend_is_controlled_failure():
    try:
        result = compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="rust"))
    except BackendUnavailableError:
        return
    assert result.backend_used == "rust"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alpha", 0.0),
        ("alpha", 1.0),
        ("ci_level", 1.2),
        ("capability_alpha", 0.0),
        ("ci_bootstrap_iterations", 0),
        ("small_n_threshold", 0),
        ("simulation_validation_iterations", -1),
        ("simulation_random_seed", 1.5),
        ("capability_benchmark", 0.0),
        ("correction_method", "bonferroni"),
        ("posthoc_method", "scheffe"),
        ("variance_test", "bartlett"),
        ("multi_group_effect", "epsilon_squared"),
        ("backend", "fast"),
    ],
)
def test_invalid_analysis_config_fails_before_analysis(field, value):
    config = AnalysisConfig(**{field: value})

    with pytest.raises(ValueError):
        compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=config)


def test_public_policy_label_helpers_are_top_level_exports():
    assert format_correction_method("holm_bonferroni") == "Holm"
    assert describe_correction_policy("bh") == "Exploratory false-discovery-rate control (Benjamini-Hochberg/FDR)"
    assert describe_pairwise_strategy(non_parametric=False, equal_var=False, correction_method="bh") == (
        "pairwise Welch t-tests + Benjamini-Hochberg"
    )


def test_package_import_is_clean_and_does_not_eagerly_import_pandas():
    env = os.environ.copy()
    env["PYTHONPATH"] = str((__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import hexafe_groupstats; print('pandas' in sys.modules); print(hasattr(hexafe_groupstats, 'analyze_metric'))",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    lines = completed.stdout.strip().splitlines()
    assert lines == ["False", "True"]
