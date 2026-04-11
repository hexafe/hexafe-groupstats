# API Examples

This file shows the current public API and the adapter surface.

## `analyze_metric`

```python
from hexafe_groupstats import analyze_metric, AnalysisConfig, SpecLimits

result = analyze_metric(
    "thickness",
    {
        "A": [1.0, 1.1, 1.2, 1.1],
        "B": [1.3, 1.4, 1.5, 1.6],
    },
    spec_limits=SpecLimits(lsl=0.8, nominal=1.2, usl=1.8),
    config=AnalysisConfig(
        alpha=0.05,
        correction_method="holm",
        backend="auto",
    ),
)

print(result.metric)
print(result.backend_used)
print(result.assumptions.selection_mode.value)
print(result.omnibus.test_name)
print(result.diagnostics.pairwise_strategy)
```

## `compare_groups`

`compare_groups(...)` is a convenience wrapper for already grouped samples.

```python
from hexafe_groupstats import compare_groups

result = compare_groups(
    {
        "Group 1": [10, 11, 12],
        "Group 2": [9, 10, 10],
    },
    metric_name="pressure",
)
```

## `analyze_dataframe`

`analyze_dataframe(...)` reads a pandas DataFrame, groups by `metric` and `group`, coerces numeric values, and returns `list[MetricAnalysisResult]`.

```python
import pandas as pd
from hexafe_groupstats import analyze_dataframe

df = pd.DataFrame(
    {
        "metric": ["pressure", "pressure", "pressure", "pressure"],
        "group": ["A", "A", "B", "B"],
        "value": ["10.1", "10.2", "10.0", "10.3"],
    }
)

results = analyze_dataframe(df)
```

Optional spec columns are read if present:

- `LSL`
- `NOMINAL`
- `USL`

If pandas is not installed, the adapter raises a clear runtime error.

## Result models

`MetricAnalysisResult` contains the main outputs:

- `preprocess`
- `assumptions`
- `omnibus`
- `pairwise_results`
- `posthoc_summary`
- `posthoc_results`
- `capability_results`
- `distribution_profiles`
- `simulation_validation`
- `descriptive_stats`
- `diagnostics`
- `insights`

The row-level models are:

- `CapabilityResult`
- `PairwiseResult`
- `DescriptiveStats`
- `DistributionProfile`

## Dict rows and DataFrames

For plain Python rows:

```python
from hexafe_groupstats.adapters.rows import descriptive_rows, pairwise_rows, metric_row

metric_dict = metric_row(results[0])
descriptive_dicts = descriptive_rows(results[0])
pairwise_dicts = pairwise_rows(results[0])
```

Additional row helpers:

```python
from hexafe_groupstats.adapters.rows import capability_rows, distribution_rows, posthoc_rows
```

For pandas output:

```python
from hexafe_groupstats.adapters.pandas import (
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_distribution_dataframe,
    results_to_pairwise_dataframe,
    results_to_posthoc_dataframe,
)

capability_df = results_to_capability_dataframe(results)
descriptive_df = results_to_descriptive_dataframe(results)
distribution_df = results_to_distribution_dataframe(results)
pairwise_df = results_to_pairwise_dataframe(results)
posthoc_df = results_to_posthoc_dataframe(results)
```

## CSV / sensor input shape

The intended CSV-to-DataFrame shape is long/tidy:

```text
metric,group,value,LSL,NOMINAL,USL
temperature,sensor_A,21.4,20,22,24
temperature,sensor_B,22.1,20,22,24
```

If your source file is wide, reshape once with `pandas.melt`.

## Monte Carlo stability validation

```python
from hexafe_groupstats import AnalysisConfig, analyze_metric

result = analyze_metric(
    "pressure",
    {"A": [10, 11, 12], "B": [9, 10, 10], "C": [14, 15, 16]},
    config=AnalysisConfig(simulation_validation_iterations=200),
)

print(result.simulation_validation.omnibus_significant_rate)
print(result.simulation_validation.selected_test_counts)
```

## Spec policy helpers

```python
from hexafe_groupstats import classify_spec_status, resolve_analysis_policy, SpecLimits

status = classify_spec_status(SpecLimits(lsl=0, nominal=5, usl=10))
policy = resolve_analysis_policy(status)
```

The current rule semantics are:

- `EXACT_MATCH` -> pairwise yes, capability yes
- `LIMIT_MISMATCH` -> pairwise yes, capability no
- `NOM_MISMATCH` -> pairwise no, capability no
- `INVALID_SPEC` -> pairwise no, capability no
