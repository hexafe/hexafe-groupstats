from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from hexafe_groupstats import (
    AnalysisConfig,
    SpecLimits,
    analyze_dataframe,
    analyze_grouped_metrics,
    analyze_metric,
    classify_spec_status,
    resolve_analysis_policy,
)
from hexafe_groupstats.adapters.metroliza import analyze_metroliza_payload, to_metroliza_rows
from hexafe_groupstats.adapters.pandas import (
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_distribution_dataframe,
    results_to_metric_dataframe,
    results_to_pairwise_dataframe,
    results_to_posthoc_dataframe,
)
from hexafe_groupstats.adapters.rows import metric_row


def test_spec_classification_and_policy_resolution():
    assert classify_spec_status(None).value == "NO_SPEC"
    assert classify_spec_status(SpecLimits(lsl=0.0, nominal=1.0, usl=2.0)).value == "EXACT_MATCH"
    assert classify_spec_status(
        [SpecLimits(lsl=0.0, nominal=1.0, usl=2.0), SpecLimits(lsl=0.1, nominal=1.0, usl=2.1)]
    ).value == "LIMIT_MISMATCH"
    assert classify_spec_status(
        [SpecLimits(lsl=0.0, nominal=1.0, usl=2.0), SpecLimits(lsl=0.0, nominal=1.1, usl=2.0)]
    ).value == "NOM_MISMATCH"
    assert classify_spec_status([SpecLimits(lsl=2.0, nominal=1.0, usl=0.0)]).value == "INVALID_SPEC"

    policy = resolve_analysis_policy("LIMIT_MISMATCH")
    assert policy.allow_pairwise is True
    assert policy.allow_capability is False
    no_spec_policy = resolve_analysis_policy("NO_SPEC")
    assert no_spec_policy.allow_pairwise is True
    assert no_spec_policy.allow_capability is False


def test_public_api_compare_without_specs_keeps_pairwise_notebook_friendly():
    result = analyze_metric("metric", {"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig())

    assert result.spec_status.value == "NO_SPEC"
    assert result.analysis_policy.allow_pairwise is True
    assert result.analysis_policy.allow_capability is False
    assert result.diagnostics.comment.startswith("Analyzed without specs")
    assert result.diagnostics.capability_strategy == "Capability disabled because no specs were supplied"
    assert len(result.pairwise_results) == 1
    assert "no_specs" in result.structured_insights[0].confidence_or_caution
    assert "capability_ci_unavailable" not in result.structured_insights[0].confidence_or_caution


def test_pandas_adapter_returns_metric_results_and_dataframes():
    frame = pd.DataFrame(
        {
            "metric": ["m1", "m1", "m1", "m1", "m2", "m2", "m2", "m2"],
            "group": ["A", "A", "B", "B", "A", "A", "B", "B"],
            "value": [1.0, 1.1, 2.0, 2.1, 5.0, 5.1, 6.0, 6.1],
            "LSL": [0.0] * 8,
            "NOMINAL": [1.5] * 4 + [5.5] * 4,
            "USL": [3.0] * 4 + [7.0] * 4,
        }
    )

    results = analyze_dataframe(
        frame,
        metric_column="metric",
        group_column="group",
        value_column="value",
        lsl_column="LSL",
        nominal_column="NOMINAL",
        usl_column="USL",
    )

    assert [result.metric for result in results] == ["m1", "m2"]
    desc_df = results_to_descriptive_dataframe(results)
    pair_df = results_to_pairwise_dataframe(results)
    capability_df = results_to_capability_dataframe(results)
    distribution_df = results_to_distribution_dataframe(results)
    posthoc_df = results_to_posthoc_dataframe(results)
    metric_df = results_to_metric_dataframe(results)
    assert set(desc_df.columns) >= {"metric", "group", "mean"}
    assert set(pair_df.columns) >= {"metric", "group_a", "group_b", "adjusted_p_value"}
    assert set(capability_df.columns) >= {"metric", "group", "cpk"}
    assert set(distribution_df.columns) >= {"metric", "group", "normality_status"}
    assert set(metric_df.columns) >= {"metric", "backend_used", "spec_status", "structured_insights"}
    assert "family" in posthoc_df.columns or posthoc_df.empty


def test_pandas_adapter_handles_categorical_grouping_without_future_warning():
    frame = pd.DataFrame(
        {
            "metric": pd.Categorical(
                ["m1", "m1", "m1", "m1", "m2", "m2", "m2", "m2"],
                categories=["m1", "m2", "unused"],
            ),
            "group": pd.Categorical(
                ["A", "A", "B", "B", "A", "A", "B", "B"],
                categories=["A", "B", "unused"],
            ),
            "value": [1.0, 1.1, 2.0, 2.1, 5.0, 5.1, 6.0, 6.1],
        }
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        results = analyze_dataframe(frame)

    assert [result.metric for result in results] == ["m1", "m2"]


def test_pandas_adapter_preserves_numpy_group_arrays(monkeypatch):
    from hexafe_groupstats.adapters import pandas as pandas_adapter

    captured_groups = []
    captured_specs = []
    real_analyze_groups = pandas_adapter.analyze_groups

    def capture_analyze_groups(**kwargs):
        captured_groups.extend(kwargs["groups"].values())
        captured_specs.append(kwargs["spec_limits"])
        return real_analyze_groups(**kwargs)

    monkeypatch.setattr(pandas_adapter, "analyze_groups", capture_analyze_groups)
    frame = pd.DataFrame(
        {
            "metric": ["m1", "m1", "m1", "m1"],
            "group": ["A", "A", "B", "B"],
            "value": ["1.0", "1.1", "2.0", "2.1"],
            "LSL": [0.0] * 4,
            "NOMINAL": [1.5] * 4,
            "USL": [3.0] * 4,
        }
    )

    analyze_dataframe(
        frame,
        metric_column="metric",
        group_column="group",
        value_column="value",
        lsl_column="LSL",
        nominal_column="NOMINAL",
        usl_column="USL",
    )

    assert frame["value"].tolist() == ["1.0", "1.1", "2.0", "2.1"]
    assert captured_groups
    assert all(isinstance(values, np.ndarray) for values in captured_groups)
    assert all(values.dtype == np.float64 for values in captured_groups)
    assert len(captured_specs[0]) == 1


def test_analyze_grouped_metrics_uses_metric_specific_specs():
    results = analyze_grouped_metrics(
        {
            "m1": {"A": [1.0, 1.1], "B": [2.0, 2.1]},
            "m2": {"A": [5.0, 5.1], "B": [6.0, 6.1]},
        },
        spec_limits={
            "m1": SpecLimits(lsl=0.0, nominal=1.5, usl=3.0),
            "m2": SpecLimits(lsl=4.0, nominal=5.5, usl=7.0),
        },
    )

    assert [result.metric for result in results] == ["m1", "m2"]
    assert all(result.spec_status.value == "EXACT_MATCH" for result in results)


def test_pandas_adapter_detects_spec_mismatch():
    frame = pd.DataFrame(
        {
            "metric": ["m1", "m1", "m1", "m1"],
            "group": ["A", "A", "B", "B"],
            "value": [1.0, 1.1, 2.0, 2.1],
            "LSL": [0.0, 0.0, 0.2, 0.2],
            "NOMINAL": [1.5, 1.5, 1.5, 1.5],
            "USL": [3.0, 3.0, 3.2, 3.2],
        }
    )

    result = analyze_dataframe(
        frame,
        metric_column="metric",
        group_column="group",
        value_column="value",
        lsl_column="LSL",
        nominal_column="NOMINAL",
        usl_column="USL",
    )[0]

    assert result.spec_status.value == "LIMIT_MISMATCH"
    assert result.analysis_policy.allow_pairwise is True


def test_pandas_adapter_rejects_missing_required_columns():
    frame = pd.DataFrame({"metric": ["m1"], "value": [1.0]})

    with pytest.raises(ValueError, match="Missing required dataframe column"):
        analyze_dataframe(frame)


def test_pandas_adapter_rejects_partial_spec_columns():
    frame = pd.DataFrame(
        {
            "metric": ["m1", "m1"],
            "group": ["A", "B"],
            "value": [1.0, 2.0],
            "LSL": [0.0, 0.0],
            "USL": [3.0, 3.0],
        }
    )

    with pytest.raises(ValueError, match="complete LSL/NOMINAL/USL set"):
        analyze_dataframe(frame)


def test_pandas_adapter_returns_empty_when_no_numeric_values_remain():
    frame = pd.DataFrame(
        {
            "metric": ["m1"],
            "group": ["A"],
            "value": ["not numeric"],
        }
    )

    assert analyze_dataframe(frame) == []


def test_metric_row_includes_simulation_pairwise_stability():
    result = analyze_metric(
        "metric",
        {"A": [1, 2, 3, 4], "B": [2, 3, 4, 5], "C": [6, 7, 8, 9]},
        config=AnalysisConfig(simulation_validation_iterations=4, simulation_random_seed=11),
    )

    row = metric_row(result)

    assert row["simulation_validation"] is not None
    assert row["simulation_validation"]["pairwise_stability"]
    assert "warnings" in row["simulation_validation"]


def test_metroliza_adapter_accepts_payload_and_emits_rows():
    payload = {
        "metric": "diameter",
        "groups": [
            {"group": "A", "values": [1.0, 1.2, 1.1]},
            {"group": "B", "values": [2.0, 2.1, 2.2]},
        ],
        "LSL": 0.0,
        "NOMINAL": 1.5,
        "USL": 3.0,
    }

    result = analyze_metroliza_payload(payload)
    rows = to_metroliza_rows(result)

    assert result.metric == "diameter"
    assert set(rows) >= {
        "metric_row",
        "structured_insights",
        "insights",
        "descriptive_rows",
        "pairwise_rows",
        "posthoc_rows",
        "capability_rows",
        "distribution_rows",
    }
    assert rows["structured_insights"][0]["headline"]
    assert rows["pairwise_rows"][0]["test_used"] in {"Mann-Whitney U", "Student t-test", "Welch t-test"}
