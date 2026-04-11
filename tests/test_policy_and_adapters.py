from __future__ import annotations

import pandas as pd

from hexafe_groupstats import (
    AnalysisConfig,
    SpecLimits,
    analyze_dataframe,
    analyze_metric,
    classify_spec_status,
    resolve_analysis_policy,
)
from hexafe_groupstats.adapters.metroliza import analyze_metroliza_payload, to_metroliza_rows
from hexafe_groupstats.adapters.pandas import (
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_distribution_dataframe,
    results_to_pairwise_dataframe,
    results_to_posthoc_dataframe,
)


def test_spec_classification_and_policy_resolution():
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


def test_public_api_compare_without_specs_keeps_pairwise_notebook_friendly():
    result = analyze_metric("metric", {"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig())

    assert result.spec_status.value == "EXACT_MATCH"
    assert result.analysis_policy.allow_pairwise is True
    assert len(result.pairwise_results) == 1


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
    assert set(desc_df.columns) >= {"metric", "group", "mean"}
    assert set(pair_df.columns) >= {"metric", "group_a", "group_b", "adjusted_p_value"}
    assert set(capability_df.columns) >= {"metric", "group", "cpk"}
    assert set(distribution_df.columns) >= {"metric", "group", "normality_status"}
    assert "family" in posthoc_df.columns or posthoc_df.empty


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
    assert set(rows) == {
        "metric_row",
        "descriptive_rows",
        "pairwise_rows",
        "posthoc_rows",
        "capability_rows",
        "distribution_rows",
    }
    assert rows["pairwise_rows"][0]["test_used"] in {"Mann-Whitney U", "Student t-test", "Welch t-test"}
