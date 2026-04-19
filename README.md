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
- structured decision-oriented metric insights
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
- `MetricInsight`
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
from pprint import pprint

from hexafe_groupstats import analyze_metric, SpecLimits

result = analyze_metric(
    "diameter",
    {
        "Line A": [10.02, 10.04, 10.01, 10.03, 10.05, 10.02],
        "Line B": [10.18, 10.21, 10.17, 10.19, 10.20, 10.22],
        "Line C": [9.91, 9.93, 9.95, 9.92, 9.94, 9.90],
    },
    spec_limits=SpecLimits(lsl=9.7, nominal=10.0, usl=10.3),
)

def fmt_p(value):
    return None if value is None else f"{value:.3g}"

summary = {
    "metric": result.metric,
    "groups": result.group_order,
    "omnibus": {
        "test": result.omnibus.test_name,
        "p_value": fmt_p(result.omnibus.p_value),
        "effect_size": round(result.omnibus.effect_size, 3),
    },
    "posthoc": [
        {
            "pair": f"{row.group_a} vs {row.group_b}",
            "p_adj": fmt_p(row.adjusted_p_value),
            "significant": row.significant,
            "effect": round(row.effect_size, 3),
        }
        for row in result.posthoc_results
    ],
    "descriptive": [
        {"group": row.group, "mean": round(row.mean, 3), "std": round(row.std, 3)}
        for row in result.descriptive_stats
    ],
    "capability": [
        {"group": row.group, "cpk": round(row.cpk, 3)}
        for row in result.capability_results
    ],
    "insight": {
        "headline": result.structured_insights[0].headline,
        "why": result.structured_insights[0].why,
        "first_action": result.structured_insights[0].first_action,
        "cautions": list(result.structured_insights[0].confidence_or_caution),
    },
}

pprint(summary, sort_dicts=False)
```

```text
{'metric': 'diameter',
 'groups': ('Line A', 'Line B', 'Line C'),
 'omnibus': {'test': 'ANOVA', 'p_value': '1.93e-13', 'effect_size': 0.98},
 'posthoc': [{'pair': 'Line A vs Line B',
              'p_adj': '1.43e-10',
              'significant': True,
              'effect': -9.901},
             {'pair': 'Line A vs Line C',
              'p_adj': '1.05e-07',
              'significant': True,
              'effect': 6.139},
             {'pair': 'Line B vs Line C',
              'p_adj': '1.28e-13',
              'significant': True,
              'effect': 14.432}],
 'descriptive': [{'group': 'Line A', 'mean': 10.028, 'std': 0.015},
                 {'group': 'Line B', 'mean': 10.195, 'std': 0.019},
                 {'group': 'Line C', 'mean': 9.925, 'std': 0.019}],
 'capability': [{'group': 'Line A', 'cpk': 6.152},
                {'group': 'Line B', 'cpk': 1.871},
                {'group': 'Line C', 'cpk': 4.009}],
 'insight': {'headline': 'meaningful group difference',
             'why': 'Line B vs Line C is significant after correction and the effect is large.',
             'first_action': 'Start with this pair and verify likely process drivers before changing settings.',
             'cautions': ['time_order_unavailable']}}
```

## Example: `analyze_dataframe` with pandas

```python
import pandas as pd
from hexafe_groupstats import analyze_dataframe

df = pd.DataFrame(
    {
        "metric": ["diameter"] * 9 + ["roughness"] * 9,
        "group": ["Line A"] * 3 + ["Line B"] * 3 + ["Line C"] * 3 + ["Line A"] * 3 + ["Line B"] * 3 + ["Line C"] * 3,
        "value": [
            10.01, 10.03, 10.02,
            10.18, 10.19, 10.21,
            9.92, 9.94, 9.93,
            1.20, 1.30, 1.25,
            1.55, 1.60, 1.58,
            1.10, 1.08, 1.12,
        ],
        "LSL": [9.7] * 9 + [0.8] * 9,
        "NOMINAL": [10.0] * 9 + [1.2] * 9,
        "USL": [10.3] * 9 + [1.8] * 9,
    }
)

results = analyze_dataframe(df)
summary = [
    {
        "metric": result.metric,
        "omnibus": result.omnibus.test_name,
        "p_value": f"{result.omnibus.p_value:.3g}",
        "spec_status": result.spec_status.value,
    }
    for result in results
]

print(summary)
```

```text
[{'metric': 'diameter',
  'omnibus': 'ANOVA',
  'p_value': '5.12e-07',
  'spec_status': 'EXACT_MATCH'},
 {'metric': 'roughness',
  'omnibus': 'ANOVA',
  'p_value': '7.35e-06',
  'spec_status': 'EXACT_MATCH'}]
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

print(descriptive_df[["metric", "group", "n", "mean", "std", "cpk"]].round(3).head(6).to_dict(orient="records"))
print(pairwise_df[["metric", "group_a", "group_b", "adjusted_p_value", "effect_size", "method_family"]].round(6).head(6).to_dict(orient="records"))
print(capability_df[["metric", "group", "cp", "cpk", "warnings"]].round(3).head(6).to_dict(orient="records"))
print(distribution_df[["metric", "group", "skewness", "normality_status", "warnings"]].round(3).head(6).to_dict(orient="records"))
print(posthoc_df[["metric", "group_a", "group_b", "method_name", "adjusted_p_value"]].round(6).head(6).to_dict(orient="records"))
```

```text
[{'metric': 'diameter', 'group': 'Line A', 'n': 3, 'mean': 10.02, 'std': 0.01, 'cpk': 9.333},
 {'metric': 'diameter', 'group': 'Line B', 'n': 3, 'mean': 10.193, 'std': 0.015, 'cpk': 2.328},
 {'metric': 'diameter', 'group': 'Line C', 'n': 3, 'mean': 9.93, 'std': 0.01, 'cpk': 7.667},
 {'metric': 'roughness', 'group': 'Line A', 'n': 3, 'mean': 1.25, 'std': 0.05, 'cpk': 3.0},
 {'metric': 'roughness', 'group': 'Line B', 'n': 3, 'mean': 1.577, 'std': 0.025, 'cpk': 2.958},
 {'metric': 'roughness', 'group': 'Line C', 'n': 3, 'mean': 1.1, 'std': 0.02, 'cpk': 5.0}]
[{'metric': 'diameter', 'group_a': 'Line A', 'group_b': 'Line B', 'adjusted_p_value': 5e-06, 'effect_size': -13.426342, 'method_family': 'tukey_hsd'},
 {'metric': 'diameter', 'group_a': 'Line A', 'group_b': 'Line C', 'adjusted_p_value': 0.000233, 'effect_size': 9.0, 'method_family': 'tukey_hsd'},
 {'metric': 'diameter', 'group_a': 'Line B', 'group_b': 'Line C', 'adjusted_p_value': 0.0, 'effect_size': 20.397712, 'method_family': 'tukey_hsd'},
 {'metric': 'roughness', 'group_a': 'Line A', 'group_b': 'Line B', 'adjusted_p_value': 5.9e-05, 'effect_size': -8.253089, 'method_family': 'tukey_hsd'},
 {'metric': 'roughness', 'group_a': 'Line A', 'group_b': 'Line C', 'adjusted_p_value': 0.004188, 'effect_size': 3.939193, 'method_family': 'tukey_hsd'},
 {'metric': 'roughness', 'group_a': 'Line B', 'group_b': 'Line C', 'adjusted_p_value': 7e-06, 'effect_size': 20.970537, 'method_family': 'tukey_hsd'}]
[{'metric': 'diameter', 'group': 'Line A', 'cp': 10.0, 'cpk': 9.333, 'warnings': ['ci_unavailable_n_lt_25']},
 {'metric': 'diameter', 'group': 'Line B', 'cp': 6.547, 'cpk': 2.328, 'warnings': ['ci_unavailable_n_lt_25']},
 {'metric': 'diameter', 'group': 'Line C', 'cp': 10.0, 'cpk': 7.667, 'warnings': ['ci_unavailable_n_lt_25']},
 {'metric': 'roughness', 'group': 'Line A', 'cp': 3.333, 'cpk': 3.0, 'warnings': ['ci_unavailable_n_lt_25']},
 {'metric': 'roughness', 'group': 'Line B', 'cp': 6.623, 'cpk': 2.958, 'warnings': ['ci_unavailable_n_lt_25']},
 {'metric': 'roughness', 'group': 'Line C', 'cp': 8.333, 'cpk': 5.0, 'warnings': ['ci_unavailable_n_lt_25']}]
[{'metric': 'diameter', 'group': 'Line A', 'skewness': 0.0, 'normality_status': 'skipped_n_lt_8', 'warnings': []},
 {'metric': 'diameter', 'group': 'Line B', 'skewness': 0.935, 'normality_status': 'skipped_n_lt_8', 'warnings': []},
 {'metric': 'diameter', 'group': 'Line C', 'skewness': 0.0, 'normality_status': 'skipped_n_lt_8', 'warnings': []},
 {'metric': 'roughness', 'group': 'Line A', 'skewness': 0.0, 'normality_status': 'skipped_n_lt_8', 'warnings': []},
 {'metric': 'roughness', 'group': 'Line B', 'skewness': -0.586, 'normality_status': 'skipped_n_lt_8', 'warnings': []},
 {'metric': 'roughness', 'group': 'Line C', 'skewness': 0.0, 'normality_status': 'skipped_n_lt_8', 'warnings': []}]
[{'metric': 'diameter', 'group_a': 'Line A', 'group_b': 'Line B', 'method_name': 'Tukey HSD', 'adjusted_p_value': 5e-06},
 {'metric': 'diameter', 'group_a': 'Line A', 'group_b': 'Line C', 'method_name': 'Tukey HSD', 'adjusted_p_value': 0.000233},
 {'metric': 'diameter', 'group_a': 'Line B', 'group_b': 'Line C', 'method_name': 'Tukey HSD', 'adjusted_p_value': 0.0},
 {'metric': 'roughness', 'group_a': 'Line A', 'group_b': 'Line B', 'method_name': 'Tukey HSD', 'adjusted_p_value': 5.9e-05},
 {'metric': 'roughness', 'group_a': 'Line A', 'group_b': 'Line C', 'method_name': 'Tukey HSD', 'adjusted_p_value': 0.004188},
 {'metric': 'roughness', 'group_a': 'Line B', 'group_b': 'Line C', 'method_name': 'Tukey HSD', 'adjusted_p_value': 7e-06}]
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

print(
    {
        "omnibus_significant_rate": round(result.simulation_validation.omnibus_significant_rate, 2),
        "method_consistency_rate": round(result.simulation_validation.method_consistency_rate, 2),
        "selected_test_counts": result.simulation_validation.selected_test_counts,
        "pairwise_stability": list(result.simulation_validation.pairwise_stability),
    }
)
```

```text
{'omnibus_significant_rate': 1.0,
 'method_consistency_rate': 0.69,
 'selected_test_counts': (('ANOVA', 62), ('Kruskal-Wallis', 138)),
 'pairwise_stability': []}
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
summary = {
    "test": results[0].omnibus.test_name,
    "p_value": round(results[0].omnibus.p_value, 4),
    "comment": results[0].diagnostics.comment,
}
summary
```

```text
{'test': 'Mann-Whitney U',
 'p_value': 0.3333,
 'comment': 'Analyzed: pairwise comparison and capability policy are enabled.'}
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
