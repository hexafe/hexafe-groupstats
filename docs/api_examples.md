# API Examples

This file shows the current public API and the adapter surface.

## Method Reference

| Method name | When we should use it | Why we should use it | Example use case |
| --- | --- | --- | --- |
| `analyze_metric(...)` | Values are already grouped in Python for one metric. | Returns the full typed result for assumptions, tests, comparisons, capability, diagnostics, and insights. | Compare fill weight across packaging lines. |
| `compare_groups(...)` | A short grouped-sample comparison is enough. | Wraps `analyze_metric(...)` with a simpler call shape. | Compare two supplier batches from lists. |
| `analyze_dataframe(...)` | Input is tidy pandas or CSV-style data. | Groups by metric and group, coerces numeric values, and reads optional specs. | Analyze a CSV with metric, line, value, and spec columns. |
| `classify_spec_status(...)` | You need to inspect spec compatibility before or after analysis. | Distinguishes no specs, exact specs, mismatched specs, and invalid specs. | Detect that capability should be disabled. |
| `resolve_analysis_policy(...)` | UI or report code needs allowed-output rules. | Converts spec status into pairwise/capability policy. | Show “Pairwise yes; capability off.” |
| `format_correction_method(...)` | A correction key needs a report label. | Keeps labels consistent. | Render `holm` as `Holm`. |
| `describe_correction_policy(...)` | Users need to understand the correction choice. | Explains strict family-wise control versus FDR control. | Add a footnote for adjusted p-values. |
| `describe_pairwise_strategy(...)` | Reports need the selected pairwise strategy. | Combines pairwise test family and correction method. | Show `pairwise Welch t-tests + Holm`. |
| `metric_row(...)` | One result needs a summary dict. | Flattens metric metadata, diagnostics, insight, warnings, and simulation summary. | Build a dashboard metric row. |
| `descriptive_rows(...)` | Per-group summaries are needed. | Exposes n, mean, spread, quartiles, min/max, warnings, and capability values. | Create a descriptive report section. |
| `pairwise_rows(...)` | Pairwise comparison rows are needed. | Exposes p-values, adjusted p-values, effect sizes, estimates, and warnings. | Export pair differences to CSV. |
| `posthoc_rows(...)` | Dedicated multi-group post-hoc rows are needed. | Preserves Tukey, Games-Howell, or Dunn method details. | Show line-pair differences after Welch ANOVA. |
| `capability_rows(...)` | Capability output is needed for valid specs. | Exposes Cp/Cpk, component indexes, confidence intervals, and warnings. | Rank groups by weakest Cpk. |
| `distribution_rows(...)` | Distribution diagnostics are needed. | Exposes skewness, kurtosis, normality status, and warnings. | Flag high-skew groups in a report. |
| `results_to_metric_dataframe(...)` | Pandas consumers need one row per metric. | Converts result-level summaries into a DataFrame. | Create a metric summary table in a notebook. |
| `results_to_descriptive_dataframe(...)` | Pandas consumers need per-group summaries. | Converts descriptive rows into a DataFrame. | Sort groups by mean or Cpk. |
| `results_to_pairwise_dataframe(...)` | Pandas consumers need pairwise rows. | Converts comparison rows into a DataFrame. | Filter significant adjusted p-values. |
| `results_to_posthoc_dataframe(...)` | Pandas consumers need post-hoc rows. | Keeps multi-group post-hoc output tabular. | Review Dunn comparisons after Kruskal-Wallis. |
| `results_to_capability_dataframe(...)` | Pandas consumers need capability rows. | Converts capability results into a DataFrame. | Export Cp/Cpk to a workbook. |
| `results_to_distribution_dataframe(...)` | Pandas consumers need distribution diagnostics. | Converts distribution profiles into a DataFrame. | Audit rejected normality checks. |
| Student t-test | Two normal groups have similar variance. | Tests a mean difference under equal-variance assumptions. | Compare two balanced machine samples. |
| Welch t-test | Two normal groups have different variance. | Tests a mean difference without equal-variance assumptions. | Compare a stable sensor to a noisy sensor. |
| Mann-Whitney U | Two-group normality is failed or unresolved. | Provides a non-parametric comparison. | Compare skewed cycle-time groups. |
| ANOVA | Three or more normal groups have similar variance. | Tests whether any group mean differs. | Compare four material suppliers. |
| Welch ANOVA | Three or more normal groups have unequal variance. | Tests overall differences without equal-variance assumptions. | Compare lines with different spread. |
| Kruskal-Wallis | Three or more groups have failed or unresolved normality. | Provides a non-parametric overall test. | Compare skewed wait times across shifts. |
| Tukey HSD / Tukey-Kramer | ANOVA selects the equal-variance path. | Finds pair differences after a multi-group parametric test. | Identify which batches differ after ANOVA. |
| Games-Howell | Welch ANOVA selects the unequal-variance path. | Finds pair differences without assuming equal variance. | Compare line pairs with unequal spread. |
| Dunn | Kruskal-Wallis selects the non-parametric path. | Finds rank-based pair differences with correction. | Locate which skewed groups differ. |
| Holm correction | Decisions need strict multiple-comparison control. | Controls family-wise error. | Production action where false positives are costly. |
| Benjamini-Hochberg correction | Exploratory screening has many comparisons. | Controls false discovery rate with less conservatism than Holm. | Scan many metrics for follow-up. |
| Cp/Cpk capability | Valid lower, nominal, and upper specs are supplied. | Connects statistics to tolerance and centering risk. | Decide whether a shifted line is still capable. |
| Distribution diagnostics | Assumption and shape context matters. | Adds skew, kurtosis, normality status, and caution flags. | Qualify normal-theory conclusions. |
| Monte Carlo validation | Result stability is uncertain. | Resamples data and shows how often conclusions repeat. | Check a borderline pairwise result. |
| `backend="auto"` / `backend="python"` | Normal installs, notebooks, and CI. | Uses the always-available Python correctness baseline. | Run in Colab without native dependencies. |
| `backend="rust"` | Optional native extension is built and explicitly requested. | Runs native parametric pairwise kernels while preserving Python fallbacks for unsupported paths. | Compare many normal two-group pairs after `cargo build --release --manifest-path rust/Cargo.toml`. |

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
    results_to_metric_dataframe,
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_distribution_dataframe,
    results_to_pairwise_dataframe,
    results_to_posthoc_dataframe,
)

metric_df = results_to_metric_dataframe(results)
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

- `NO_SPEC` -> pairwise yes, capability no
- `EXACT_MATCH` -> pairwise yes, capability yes
- `LIMIT_MISMATCH` -> pairwise yes, capability no
- `NOM_MISMATCH` -> pairwise no, capability no
- `INVALID_SPEC` -> pairwise no, capability no
