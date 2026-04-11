# hexafe-groupstats

`hexafe-groupstats` is a standalone, importable Python package for group comparison and statistical analysis.
It is designed as a library first: it accepts grouped samples or pandas DataFrames, returns typed result models, and keeps workbook/export/UI concerns out of the engine.

Current engine coverage includes:

- preprocessing and assumption checks
- omnibus selection
- dedicated multi-group post-hoc procedures
- multiple-comparison correction
- effect sizes and confidence intervals
- per-group capability metrics
- diagnostic-only distribution profiles
- optional Monte Carlo stability validation

## Public API

Top-level exports:

- `analyze_metric(...)`
- `compare_groups(...)`
- `analyze_dataframe(...)`
- `classify_spec_status(...)`
- `resolve_analysis_policy(...)`
- `SpecLimits`
- `AnalysisConfig`
- `MetricAnalysisResult`
- `PairwiseResult`
- `DescriptiveStats`
- `AnalysisPolicy`
- `CapabilityResult`
- `DistributionProfile`

Install with pandas support if you want the DataFrame adapter:

```bash
pip install -e .[pandas]
```

## Example: `analyze_metric` with dict groups

```python
from hexafe_groupstats import analyze_metric, SpecLimits

result = analyze_metric(
    "diameter",
    {
        "Line A": [10.1, 10.3, 10.2, 10.4],
        "Line B": [10.0, 10.1, 10.1, 10.2],
    },
    spec_limits=SpecLimits(lsl=9.8, nominal=10.2, usl=10.6),
)

print(result.metric)
print(result.omnibus.test_name)
print(result.analysis_policy.analysis_restriction_label)
print(result.pairwise_results[0].test_name)
```

```text
diameter
Student t-test
Full analysis
Student t-test
```

## Example: `analyze_dataframe` with pandas

```python
import pandas as pd
from hexafe_groupstats import analyze_dataframe

df = pd.DataFrame(
    {
        "metric": ["diameter", "diameter", "diameter", "diameter"],
        "group": ["Line A", "Line A", "Line B", "Line B"],
        "value": [10.1, 10.3, 10.0, 10.2],
        "LSL": [9.8, 9.8, 9.8, 9.8],
        "NOMINAL": [10.2, 10.2, 10.2, 10.2],
        "USL": [10.6, 10.6, 10.6, 10.6],
    }
)

results = analyze_dataframe(df)
for result in results:
    print(result.metric, result.group_order, result.spec_status.value)
```

```text
diameter ('Line A', 'Line B') EXACT_MATCH
```

For CSV files from multiple sensors, the recommended shape is a tidy table:

```text
metric,group,value,LSL,NOMINAL,USL
temperature,sensor_A,21.4,20,22,24
temperature,sensor_B,22.1,20,22,24
pressure,sensor_A,1.02,0.9,1.0,1.1
pressure,sensor_B,1.05,0.9,1.0,1.1
```

Then:

```python
df = pd.read_csv("sensors.csv")
results = analyze_dataframe(df)
```

If your CSV is wide, reshape it first with `melt(...)` into `metric` / `group` / `value` columns.

## Example: convert results to DataFrames

```python
from hexafe_groupstats import analyze_dataframe
from hexafe_groupstats.adapters.pandas import (
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_distribution_dataframe,
    results_to_pairwise_dataframe,
    results_to_posthoc_dataframe,
)

results = analyze_dataframe(df)

capability_df = results_to_capability_dataframe(results)
descriptive_df = results_to_descriptive_dataframe(results)
distribution_df = results_to_distribution_dataframe(results)
pairwise_df = results_to_pairwise_dataframe(results)
posthoc_df = results_to_posthoc_dataframe(results)

print(capability_df.columns.tolist())
print(descriptive_df.columns.tolist())
print(distribution_df.columns.tolist())
print(pairwise_df.columns.tolist())
print(posthoc_df.columns.tolist())
```

```text
['metric', 'group', 'n', 'mean', 'sigma', 'lsl', 'nominal', 'usl', 'cp', 'cpl', 'cpu', 'cpk', 'cp_ci', 'cpl_ci', 'cpu_ci', 'cpk_ci', 'warnings']
['metric', 'group', 'n', 'mean', 'std', 'median', 'q1', 'q3', 'iqr', 'min', 'max', 'cp', 'cpl', 'cpu', 'cpk', 'cp_ci', 'cpk_ci', 'warnings']
['metric', 'group', 'n', 'skewness', 'excess_kurtosis', 'normality_test', 'normality_p_value', 'normality_status', 'warnings']
['metric', 'group_a', 'group_b', 'test_name', 'p_value', 'adjusted_p_value', 'significant', 'effect_size', 'effect_type', 'method_family', 'comparison_estimate', 'comparison_estimate_label', 'comparison_ci', 'effect_size_ci', 'warnings']
[]
```

If you want plain dict rows instead of pandas objects, use:

```python
from hexafe_groupstats.adapters.rows import (
    capability_rows,
    descriptive_rows,
    distribution_rows,
    metric_row,
    pairwise_rows,
    posthoc_rows,
)
```

## Example: Monte Carlo stability validation

```python
from hexafe_groupstats import AnalysisConfig, analyze_metric

result = analyze_metric(
    "temperature",
    {
        "sensor_A": [21.4, 21.5, 21.7, 21.6],
        "sensor_B": [22.0, 22.1, 21.9, 22.2],
        "sensor_C": [21.2, 21.3, 21.1, 21.4],
    },
    config=AnalysisConfig(
        simulation_validation_iterations=200,
        simulation_random_seed=42,
    ),
)

print(result.simulation_validation.omnibus_significant_rate)
print(result.simulation_validation.method_consistency_rate)
```

```text
1.0
0.69
```

This resamples each group with replacement, reruns the analysis, and reports how stable the omnibus and pairwise decisions are across the simulated runs.

## Minimal notebook / Colab usage

```python
# In a notebook or Colab cell:
!pip install -e .[pandas]

import pandas as pd
from hexafe_groupstats import analyze_dataframe

df = pd.DataFrame(
    {
        "metric": ["m1", "m1", "m1", "m1"],
        "group": ["A", "A", "B", "B"],
        "value": [1.0, 1.2, 1.4, 1.5],
    }
)

results = analyze_dataframe(df)
results[0].diagnostics.comment
```

```text
'Analyzed: pairwise comparison and capability policy are enabled.'
```

For hosted notebooks, use the same package source as your environment provides
for installs, such as a wheel file or a git URL instead of a local editable path.

## Notes

- `backend="auto"` currently resolves to the Python backend.
- `backend="rust"` is intentionally not available in v1 and fails in a controlled way.
- Multi-group paths now use dedicated post-hoc families:
  - `ANOVA` -> Tukey HSD / Tukey-Kramer
  - `Welch ANOVA` -> Games-Howell
  - `Kruskal-Wallis` -> Dunn
- Capability metrics are computed per group only when specs are valid and policy allows it.
- Monte Carlo validation is opt-in and disabled by default.
