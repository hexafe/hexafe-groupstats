# hexafe-groupstats

`hexafe-groupstats` is a standalone, importable Python package for group comparison and statistical analysis.
It is designed as a library first: it accepts grouped samples or pandas DataFrames, returns typed result models, and keeps workbook/export/UI concerns out of the engine.

The engine answers three practical questions:

- Are any groups meaningfully different?
- Which pairs are driving the difference?
- Are groups capable against the supplied lower, nominal, and upper specs?

To do that, it cleans numeric input, checks assumptions, chooses an appropriate overall test, runs pairwise or post-hoc comparisons, corrects p-values for repeated comparisons, reports effect sizes and confidence intervals, computes capability metrics, and produces structured decision-oriented insights. Optional Monte Carlo validation can rerun the analysis on resampled data to show how stable the conclusions are.

## Public API

Top-level exports:

| Export | What it does |
| --- | --- |
| `analyze_metric(...)` | Main entry point for one metric when values are already grouped in Python. |
| `compare_groups(...)` | Convenience wrapper for grouped values when you do not need a custom metric-first call shape. |
| `analyze_dataframe(...)` | Reads tidy pandas/CSV-style data and returns one result per metric. |
| `classify_spec_status(...)` | Classifies whether supplied specs are valid, matching, or mismatched across records. |
| `resolve_analysis_policy(...)` | Converts spec status into what analysis is allowed, such as pairwise and capability output. |
| `format_correction_method(...)` | Formats a correction method key, such as `holm` or `bh`, for reports. |
| `describe_correction_policy(...)` | Returns a short report-ready description of the correction policy. |
| `describe_pairwise_strategy(...)` | Returns a report-ready label for the selected pairwise strategy. |
| `SpecLimits` | Holds lower, nominal, and upper specs. |
| `AnalysisConfig` | Configures statistical behavior, diagnostics, simulation, and backend selection. |
| `MetricAnalysisResult` | Full typed result for one metric. |
| `MetricInsight` | Compact decision summary for humans and reports. |
| `PairwiseResult` | One group-vs-group comparison row. |
| `DescriptiveStats` | Per-group descriptive statistics. |
| `AnalysisPolicy` | Policy object describing allowed output for the metric. |
| `CapabilityResult` | Per-group capability row, including Cp/Cpk. |
| `DistributionProfile` | Diagnostic-only distribution shape and normality information. |

## Installation

Use the pandas extra when you want CSV/DataFrame helpers. The core grouped-sample API only needs NumPy and SciPy.

### Local app or project

Install directly from GitHub into your application's environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install "hexafe-groupstats[pandas] @ git+https://github.com/hexafe/hexafe-groupstats.git@main"
```

For reproducible production installs, replace `main` with a tag or commit SHA.

If you are working from a local checkout:

```bash
git clone https://github.com/hexafe/hexafe-groupstats.git
cd hexafe-groupstats
python -m pip install -e ".[dev]"
```

Then any local app that uses the same virtual environment can import `hexafe_groupstats`.

### Google Colab

Install the package in the first notebook cell:

```python
!pip -q install "hexafe-groupstats[pandas] @ git+https://github.com/hexafe/hexafe-groupstats.git@main"
```

To analyze your own CSV in Colab:

```python
from google.colab import files
import pandas as pd

uploaded = files.upload()
df = pd.read_csv(next(iter(uploaded)))
```

The CSV should be tidy: one row per measurement, with columns for metric, group, value, and optional spec limits.

## Main Objects

| Object | Use it for |
| --- | --- |
| `analyze_metric(...)` / `compare_groups(...)` | Already-grouped samples, such as `{"Line A": [99.8, 100.1], "Line B": [100.9, 101.0]}`. |
| `analyze_dataframe(...)` | Tidy pandas or CSV-style data with metric, group, and value columns. |
| `SpecLimits(...)` | Optional lower, nominal, and upper specs for capability and centering signals. |
| `AnalysisConfig` | Statistical settings such as alpha, correction, post-hoc method, confidence intervals, diagnostics, simulation, and backend selection. |
| `MetricAnalysisResult` | Typed result object containing assumptions, selected tests, comparisons, capability, diagnostics, and insights. |
| `MetricInsight` | Compact decision summary with `headline`, `why`, `first_action`, and caution tags. |

`hexafe-groupstats` accepts already-grouped numeric samples through `analyze_metric(...)` / `compare_groups(...)`, or tidy DataFrame and CSV-style data through `analyze_dataframe(...)`; the grouped path needs a metric name plus a mapping of group labels to values, and the data-frame path needs metric, group, and value columns, with optional spec columns if your names differ from the defaults. Blank and non-numeric values are dropped during numeric coercion, and group-comparison output needs at least two usable non-empty groups. Spec limits are optional: when no specs are supplied, pairwise and post-hoc comparisons remain enabled and capability is disabled; capability and centering results require valid lower, nominal, and upper specs supplied as `SpecLimits(...)`, a dict with `lsl`/`nominal`/`usl` or `LSL`/`NOMINAL`/`USL`, a `(lsl, nominal, usl)` tuple or list, or a complete DataFrame spec-column set. `AnalysisConfig` controls statistical behavior such as alpha, multiple-comparison correction, post-hoc selection, confidence intervals, diagnostics, simulation, and backend selection.

## How To Read Results

| Term | Meaning |
| --- | --- |
| Metric | The measured characteristic, such as `fill_weight_g`, diameter, temperature, or strength. |
| Group | The population being compared, such as a line, machine, batch, supplier, sensor, or treatment. |
| Omnibus test | The overall test. It asks whether the data shows any group difference before focusing on specific pairs. With two groups, this is the direct two-group test; with three or more groups, it is ANOVA, Welch ANOVA, or Kruskal-Wallis. |
| Post-hoc / pairwise comparison | The follow-up group-vs-group comparisons. These answer which pairs differ after the overall test and assumption checks. |
| `p_adj` / adjusted p-value | A p-value corrected for multiple pair checks. Use this instead of the raw p-value when several pairs are compared. |
| Effect size | The size and direction of a difference. P-values say how strong the evidence is; effect sizes say how large the difference is. |
| Cp / Cpk | Capability metrics that need valid specs. Cp describes spread versus tolerance width; Cpk also accounts for off-center processes, so it is usually the first value to watch. |
| Confidence interval | A plausible range for a statistic. Wide intervals mean the data is not giving a precise estimate. |
| Diagnostics and cautions | Flags that explain limits of the result, such as small samples, constant groups, approximate intervals, or missing run order. |
| Structured insight | A short decision summary with `headline`, `why`, `first_action`, and caution tags. |

The usual reading order is: check the structured insight, inspect the selected omnibus and post-hoc methods, review adjusted pairwise p-values and effect sizes, then use Cpk and Cpk confidence intervals to decide whether a statistically different group also needs process action.

## Method Reference

This table covers the public API and the statistical methods users will see in results. Private helper functions are intentionally excluded.

| Method name | When we should use it | Why we should use it | Example use case |
| --- | --- | --- | --- |
| `analyze_metric(...)` | Use when values are already grouped in Python for one metric. | It returns the full typed result with assumptions, tests, post-hoc rows, capability, diagnostics, and insights. | Compare fill-weight samples from three packaging lines. |
| `compare_groups(...)` | Use for the simplest grouped-sample comparison. | It is a concise wrapper around `analyze_metric(...)` when the metric name can be supplied as an option. | Compare two supplier batches from lists in a notebook. |
| `analyze_dataframe(...)` | Use for tidy pandas or CSV-style data. | It groups rows by metric and group, coerces numeric values, reads optional specs, and returns one result per metric. | Analyze a CSV with `metric`, `line`, `value`, `LSL`, `NOMINAL`, and `USL` columns. |
| `classify_spec_status(...)` | Use before analysis when you need to know whether specs are absent, aligned, mismatched, or invalid. | It explains whether pairwise and capability interpretations are safe. | Detect that two groups use different nominal targets before comparing them directly. |
| `resolve_analysis_policy(...)` | Use when report or UI code needs the policy implied by a spec status. | It converts spec status into allowed output: pairwise yes/no and capability yes/no. | Show “Pairwise yes; capability off” for a limit mismatch. |
| `format_correction_method(...)` | Use when rendering a correction key for users. | It keeps report labels consistent. | Render `bh` as `Benjamini-Hochberg`. |
| `describe_correction_policy(...)` | Use when reports need a short explanation of the p-value correction. | It tells users whether the correction is strict or exploratory. | Explain why Holm was used for production decision control. |
| `describe_pairwise_strategy(...)` | Use when reports need the selected pairwise strategy label. | It combines the test family and correction method into one readable label. | Show `pairwise Welch t-tests + Holm`. |
| `metric_row(...)` | Use when one typed result needs a single summary dict. | It flattens the main result, diagnostics, insights, warnings, and simulation summary. | Build a JSON payload for a dashboard metric card. |
| `descriptive_rows(...)` | Use when you need per-group descriptive output. | It exposes n, mean, spread, quartiles, min/max, warnings, and capability values when available. | Export group summary rows to a report table. |
| `pairwise_rows(...)` | Use when you need legacy pairwise-compatible comparison rows. | It preserves group pairs, test names, adjusted p-values, effect sizes, estimates, and warnings. | Feed pairwise rows into an existing export workflow. |
| `posthoc_rows(...)` | Use when you need dedicated multi-group post-hoc results. | It reports Tukey, Games-Howell, or Dunn rows with method family and comparison estimates. | List which line pairs differ after Welch ANOVA. |
| `capability_rows(...)` | Use when specs are valid and per-group capability should be exported. | It exposes Cp, Cpk, component indexes, confidence intervals, and capability warnings. | Rank process lines by weakest Cpk lower bound. |
| `distribution_rows(...)` | Use when diagnostic distribution output should be exported. | It exposes skewness, kurtosis, normality test status, and distribution warnings. | Flag metrics where normal-theory conclusions need caution. |
| `results_to_metric_dataframe(...)` | Use when pandas consumers need one summary row per metric. | It turns result-level metadata into a DataFrame without hand-flattening typed objects. | Create a metric summary tab in a notebook. |
| `results_to_descriptive_dataframe(...)` | Use when pandas consumers need per-group summary rows. | It converts `descriptive_rows(...)` into a DataFrame. | Build a sortable table of means and Cpk values. |
| `results_to_pairwise_dataframe(...)` | Use when pandas consumers need pairwise comparison rows. | It converts pairwise output into report-ready tabular data. | Filter significant adjusted p-values in a notebook. |
| `results_to_posthoc_dataframe(...)` | Use when pandas consumers need dedicated post-hoc rows. | It keeps multi-group method details separate from simple two-group comparisons. | Review Dunn comparisons after Kruskal-Wallis. |
| `results_to_capability_dataframe(...)` | Use when pandas consumers need capability rows. | It converts capability output into a DataFrame with confidence intervals and warnings. | Export Cp/Cpk rows for process capability review. |
| `results_to_distribution_dataframe(...)` | Use when pandas consumers need distribution diagnostics. | It converts diagnostic profiles into a DataFrame. | Audit which groups have high skew or rejected normality. |
| Student t-test | Use automatically for two groups when normality and equal variance assumptions pass. | It is the standard parametric test for two independent groups with similar variance. | Compare two machines with balanced, normal, similar-spread samples. |
| Welch t-test | Use automatically for two groups when normality passes but variance differs. | It avoids assuming equal group variance. | Compare two sensors where one group is much noisier. |
| Mann-Whitney U | Use automatically for two groups when normality is failed or unresolved. | It gives a non-parametric two-group comparison. | Compare two skewed cycle-time distributions. |
| ANOVA | Use automatically for three or more groups when normality and equal variance assumptions pass. | It tests whether any group mean differs before post-hoc comparisons. | Compare average strength across four materials. |
| Welch ANOVA | Use automatically for three or more groups when normality passes but variance differs. | It handles unequal variance better than standard ANOVA. | Compare production lines with different spread. |
| Kruskal-Wallis | Use automatically for three or more groups when normality is failed or unresolved. | It provides a non-parametric overall multi-group test. | Compare skewed wait-time data across shifts. |
| Tukey HSD / Tukey-Kramer | Use after ANOVA on the equal-variance parametric path. | It performs corrected pairwise mean comparisons for multiple groups. | Find which batches differ after a significant ANOVA. |
| Games-Howell | Use after Welch ANOVA on the unequal-variance parametric path. | It compares pairs without assuming equal variance. | Find which line pairs differ when spreads are not equal. |
| Dunn | Use after Kruskal-Wallis on the non-parametric multi-group path. | It gives rank-based pairwise comparisons with p-value correction. | Identify which skewed groups differ after Kruskal-Wallis. |
| Holm correction | Use for stricter decision control across multiple pair comparisons. | It controls family-wise error more conservatively than false-discovery methods. | Production action where false positives are costly. |
| Benjamini-Hochberg correction | Use for exploratory analysis with many comparisons. | It controls false discovery rate and is less conservative than Holm. | Screening many process metrics for follow-up. |
| Cp/Cpk capability | Use only with valid lower, nominal, and upper specs. | It connects statistical differences to tolerance and centering risk. | Decide whether a shifted line is still capable against customer specs. |
| Distribution diagnostics | Use when assumption and shape context matters. | It reports skew, kurtosis, normality status, and warnings that qualify interpretation. | Add caution tags for heavily skewed data. |
| Monte Carlo validation | Use when you need robustness checks for small, close, or fragile results. | It resamples data and reports how often conclusions repeat. | Check whether a borderline pairwise result is stable. |
| `backend="auto"` / `backend="python"` | Use for normal installs, notebooks, CI, and release builds. | The Python backend is always available and is the correctness baseline. | Run groupstats in Colab without native dependencies. |
| `backend="rust"` | Use when the optional Rust extension is built and explicitly requested. | It runs native parametric pairwise kernels while preserving Python fallbacks for unsupported paths. | Compare many normal two-group pairs after `cargo build --release --manifest-path rust/Cargo.toml`. |

## Real-Life Example: Packaging Fill Weight

A plant fills nominal 100 g retail packs on three packaging lines. The acceptable range is 98.5 g to 101.5 g. The question is not only "are the lines different?", but also "which line needs action and why?"

```python
from pprint import pprint

from hexafe_groupstats import SpecLimits, analyze_metric

line_samples = {
    "Line A": [
        99.84, 99.91, 99.94, 99.96, 99.98, 100.00, 100.02, 100.04,
        100.05, 100.07, 100.09, 100.11, 99.88, 99.93, 99.95, 99.97,
        99.99, 100.01, 100.03, 100.06, 100.08, 100.10, 100.12, 100.15,
        99.90, 99.96, 99.99, 100.02, 100.05, 100.09,
    ],
    "Line B": [
        100.92, 100.98, 101.01, 101.03, 101.05, 101.07, 101.09, 101.11,
        101.13, 101.16, 101.18, 101.21, 100.95, 101.00, 101.02, 101.04,
        101.06, 101.08, 101.10, 101.12, 101.15, 101.17, 101.20, 101.24,
        100.97, 101.04, 101.07, 101.10, 101.14, 101.19,
    ],
    "Line C": [
        99.38, 99.54, 99.61, 99.69, 99.73, 99.82, 99.91, 100.04,
        100.11, 100.23, 100.34, 100.49, 99.44, 99.57, 99.66, 99.75,
        99.86, 99.97, 100.08, 100.19, 100.31, 100.43, 100.55, 100.66,
        99.50, 99.70, 99.89, 100.06, 100.27, 100.45,
    ],
}


def fmt_p(value):
    if value is None:
        return None
    return "<0.0001" if value < 0.0001 else f"{value:.4f}"


# Specs are supplied once because all three lines make the same product.
result = analyze_metric(
    "fill_weight_g",
    line_samples,
    spec_limits=SpecLimits(lsl=98.5, nominal=100.0, usl=101.5),
)

insight = result.structured_insights[0]

summary = {
    "metric": result.metric,
    "groups": list(result.group_order),
    "method_usage": {
        "omnibus": result.omnibus.test_name,
        "why_omnibus": result.assumptions.selection_detail,
        "posthoc": result.posthoc_summary.method_name if result.posthoc_summary else None,
        "why_posthoc": result.posthoc_summary.selection_detail if result.posthoc_summary else None,
    },
    "omnibus_p": fmt_p(result.omnibus.p_value),
    "insight": {
        "headline": insight.headline,
        "why": insight.why,
        "first_action": insight.first_action,
        "cautions": list(insight.confidence_or_caution),
    },
    "capability_watch": [
        {
            "group": row.group,
            "cp": round(row.cp, 2) if row.cp is not None else None,
            "cpk": round(row.cpk, 2) if row.cpk is not None else None,
            "cpk_ci": None if row.cpk_ci is None else tuple(round(v, 2) for v in row.cpk_ci),
        }
        for row in sorted(
            result.capability_results,
            key=lambda row: float("inf") if row.cpk is None else row.cpk,
        )[:2]
    ],
    "top_differences": [
        {
            "pair": f"{row.group_a} vs {row.group_b}",
            "p_adj": fmt_p(row.adjusted_p_value),
            "effect": round(row.effect_size, 2) if row.effect_size is not None else None,
            "effect_type": row.effect_type,
        }
        for row in result.posthoc_results
    ],
}

pprint(summary, sort_dicts=False)
```

```text
{'metric': 'fill_weight_g',
 'groups': ['Line A', 'Line B', 'Line C'],
 'method_usage': {'omnibus': 'Welch ANOVA',
                  'why_omnibus': 'Shapiro-Wilk passed for all usable groups but the variance test failed, so the unequal-variance parametric path was used.',
                  'posthoc': 'Games-Howell',
                  'why_posthoc': 'Unequal-variance parametric multi-group path selected Games-Howell.'},
 'omnibus_p': '<0.0001',
 'insight': {'headline': 'meaningful group difference',
             'why': 'Line B vs Line C is significant after correction and the effect is large (cohen_d=4.26). Possibly capable, confidence weak also applies.',
             'first_action': 'Start with this pair and verify likely process drivers before changing settings.',
             'cautions': ['time_order_unavailable']},
 'capability_watch': [{'group': 'Line C',
                       'cp': 1.39,
                       'cpk': 1.37,
                       'cpk_ci': (1.0, 1.74)},
                      {'group': 'Line B',
                       'cp': 6.12,
                       'cpk': 1.69,
                       'cpk_ci': (1.24, 2.14)}],
 'top_differences': [{'pair': 'Line A vs Line B',
                      'p_adj': '<0.0001',
                      'effect': -13.6,
                      'effect_type': 'cohen_d'},
                     {'pair': 'Line A vs Line C',
                      'p_adj': '0.8590',
                      'effect': 0.14,
                      'effect_type': 'cohen_d'},
                     {'pair': 'Line B vs Line C',
                      'p_adj': '<0.0001',
                      'effect': 4.26,
                      'effect_type': 'cohen_d'}]}
```

What this result says:

- `omnibus_p` is the overall-test p-value. Here it is below 0.0001, so the engine finds evidence that at least one line behaves differently.
- Welch ANOVA was selected because the normality checks passed but the variance check failed; this avoids assuming equal group variance.
- Games-Howell was selected because it is the matching post-hoc method for unequal-variance multi-group comparisons.
- `p_adj` is the corrected p-value for each pair. Line A vs Line C is not significant after correction, while pairs involving Line B are.
- The effect size gives direction and magnitude. Negative `cohen_d` for Line A vs Line B means Line A is lower than Line B, and the large absolute value means the shift is large.
- Line B is shifted high. Line C has the weakest capability confidence because its Cpk lower bound falls below the default 1.33 benchmark.
- The insight is not based on p-value alone; it combines corrected significance, effect size, capability, and caution tags.
- `time_order_unavailable` means the input has no trustworthy run order, so the engine does not invent a drift/stability judgement.

## Analyze CSV or Pandas Data

Use this path when measurements come from a file or notebook DataFrame. The expected shape is tidy data: one row per measurement, one column naming the metric, one column naming the group, and one numeric value column. Optional spec columns let the same call compute capability.

For files, use a tidy table:

```text
metric,line,value,LSL,NOMINAL,USL
fill_weight_g,Line A,99.84,98.5,100.0,101.5
fill_weight_g,Line A,99.91,98.5,100.0,101.5
fill_weight_g,Line B,100.92,98.5,100.0,101.5
fill_weight_g,Line B,100.98,98.5,100.0,101.5
fill_weight_g,Line C,99.38,98.5,100.0,101.5
fill_weight_g,Line C,99.54,98.5,100.0,101.5
```

Then:

```python
import pandas as pd

from hexafe_groupstats import analyze_dataframe

df = pd.read_csv("fill_weights.csv")

# Use group_column="line" because this CSV names the group column "line".
results = analyze_dataframe(df, group_column="line")

for result in results:
    insight = result.structured_insights[0]
    print(
        {
            "metric": result.metric,
            "test": result.omnibus.test_name,
            "headline": insight.headline,
            "first_action": insight.first_action,
        }
    )
```

If your CSV is wide, reshape it first with `melt(...)` into metric, group, and value columns. The adapter drops blank or non-numeric values after coercion, then analyzes each metric separately.

## Convert Results To DataFrames

Use these helpers when the typed result object needs to become report, dashboard, or export data. The pandas adapters flatten typed results into report-ready tables while keeping the statistical engine independent from workbook or UI code.

```python
from hexafe_groupstats.adapters.pandas import (
    results_to_metric_dataframe,
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_posthoc_dataframe,
)

metric_df = results_to_metric_dataframe(results)
descriptive_df = results_to_descriptive_dataframe(results)
posthoc_df = results_to_posthoc_dataframe(results)
capability_df = results_to_capability_dataframe(results)

print(metric_df[["metric", "spec_status", "omnibus_test_name", "posthoc_method_name"]].to_dict(orient="records"))
print(descriptive_df[["metric", "group", "n", "mean", "std", "cpk"]].round(3).to_dict(orient="records"))
print(posthoc_df[["metric", "group_a", "group_b", "method_name", "adjusted_p_value", "effect_size"]].round(6).to_dict(orient="records"))
print(capability_df[["metric", "group", "cp", "cpk", "cpk_ci", "warnings"]].round(3).to_dict(orient="records"))
```

Example output from the full fill-weight data:

```text
[{'metric': 'fill_weight_g', 'spec_status': 'EXACT_MATCH', 'omnibus_test_name': 'Welch ANOVA', 'posthoc_method_name': 'Games-Howell'}]
[{'metric': 'fill_weight_g', 'group': 'Line A', 'n': 30, 'mean': 100.01, 'std': 0.076, 'cpk': 6.498},
 {'metric': 'fill_weight_g', 'group': 'Line B', 'n': 30, 'mean': 101.086, 'std': 0.082, 'cpk': 1.689},
 {'metric': 'fill_weight_g', 'group': 'Line C', 'n': 30, 'mean': 99.974, 'std': 0.36, 'cpk': 1.367}]
[{'metric': 'fill_weight_g', 'group_a': 'Line A', 'group_b': 'Line B', 'method_name': 'Games-Howell', 'adjusted_p_value': 0.0, 'effect_size': -13.604967},
 {'metric': 'fill_weight_g', 'group_a': 'Line A', 'group_b': 'Line C', 'method_name': 'Games-Howell', 'adjusted_p_value': 0.859025, 'effect_size': 0.135921},
 {'metric': 'fill_weight_g', 'group_a': 'Line B', 'group_b': 'Line C', 'method_name': 'Games-Howell', 'adjusted_p_value': 0.0, 'effect_size': 4.263341}]
[{'metric': 'fill_weight_g', 'group': 'Line A', 'cp': 6.54, 'cpk': 6.498, 'cpk_ci': (4.821462671744837, 8.174563407109503), 'warnings': ['ci_approximate_n_lt_100']},
 {'metric': 'fill_weight_g', 'group': 'Line B', 'cp': 6.121, 'cpk': 1.689, 'cpk_ci': (1.2385071173933808, 2.1401580414345562), 'warnings': ['ci_approximate_n_lt_100']},
 {'metric': 'fill_weight_g', 'group': 'Line C', 'cp': 1.39, 'cpk': 1.367, 'cpk_ci': (0.9952687824617008, 1.7380573786844276), 'warnings': ['ci_approximate_n_lt_100']}]
```

Column guide:

- `mean`, `std`, `median`, quartiles, and min/max describe each group before testing.
- `adjusted_p_value` is the corrected evidence for a pairwise/post-hoc difference; lower values mean stronger evidence after accounting for multiple pair checks.
- `effect_size` describes the size and direction of the pair difference. Its scale depends on `effect_type`, such as `cohen_d` or `cliffs_delta`.
- `cp` measures tolerance width versus process spread. `cpk` also accounts for centering, so a shifted process can have high `cp` but lower `cpk`.
- `cpk_ci` is the uncertainty range around Cpk. A lower bound below the benchmark means capability confidence is weak even when the point estimate looks acceptable.
- `warnings` explain limits in the row, such as approximate intervals for smaller samples.

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

Monte Carlo validation is an opt-in robustness check. It resamples each group with replacement, reruns the same analysis many times, and reports how often the main conclusions repeat. Use it when samples are small, results are close to the threshold, or you want to know whether a selected test or pairwise decision is fragile.

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
        "pairwise_stability": [
            {
                "pair": f"{row.group_a} vs {row.group_b}",
                "significant_rate": round(row.significant_rate, 2),
                "median_p_adj": None
                if row.median_adjusted_p_value is None
                else round(row.median_adjusted_p_value, 4),
            }
            for row in result.simulation_validation.pairwise_stability
        ],
    }
)
```

```text
{'omnibus_significant_rate': 1.0,
 'method_consistency_rate': 0.69,
 'selected_test_counts': (('ANOVA', 62), ('Kruskal-Wallis', 138)),
 'pairwise_stability': [{'pair': 'sensor_A vs sensor_B',
                         'significant_rate': 0.31,
                         'median_p_adj': 0.1817},
                        {'pair': 'sensor_A vs sensor_C',
                         'significant_rate': 0.25,
                         'median_p_adj': 0.1936},
                        {'pair': 'sensor_B vs sensor_C',
                         'significant_rate': 1.0,
                         'median_p_adj': 0.0046}]}
```

How to read this output:

- `omnibus_significant_rate` is the share of resampled runs where the overall test was significant at `AnalysisConfig.alpha`. A value of `1.0` means every resample still found an overall group difference.
- `method_consistency_rate` is the share of runs that used the most common overall test. It can be below 1.0 when assumption checks vary across resamples.
- `selected_test_counts` shows which overall tests were selected during resampling. In this example, some runs use ANOVA and others use Kruskal-Wallis because the resampled normality checks are not identical every time.
- `pairwise_stability` summarizes each pair after the selected post-hoc or pairwise procedure. `significant_rate` is the share of runs where that pair stayed significant after correction.
- `median_p_adj` is the median adjusted p-value across runs. The median is used instead of the mean because p-values are bounded and often skewed; one unusual resample should not dominate the typical evidence summary.

Use `significant_rate` to judge decision stability and `median_p_adj` to judge typical corrected evidence. In the example, `sensor_B vs sensor_C` is stable across all resamples, while the other two pairs are much less stable even though the overall test is always significant.

## Performance Benchmarking

The Python backend is the correctness baseline. Use the lightweight benchmark script before changing statistical kernels or enabling native acceleration:

```bash
python scripts/benchmark_groupstats.py --repeat 5
python scripts/benchmark_groupstats.py --profile standard --repeat 5
python scripts/benchmark_groupstats.py --backend rust --repeat 5
```

The quick profile is intended for smoke checks. The standard profile is slower and is the better baseline before optimizing pairwise, post-hoc, bootstrap, DataFrame batch, or Monte Carlo paths.

## Notes

Backend behavior:

- `backend="auto"` resolves to the Python backend by default.
- `backend="rust"` uses the optional native extension when it has been built locally.
- `AnalysisConfig(backend="auto", enable_rust_in_auto=True)` may use Rust when the extension is available, but production defaults should remain Python until local benchmarks prove a win.
- Build the optional Rust extension for local validation with `cargo build --release --manifest-path rust/Cargo.toml`; source checkouts can load the release artifact directly.

Multi-group method selection:

- ANOVA uses Tukey HSD or Tukey-Kramer for post-hoc comparisons.
- Welch ANOVA uses Games-Howell because it does not assume equal variances.
- Kruskal-Wallis uses Dunn comparisons because it is the non-parametric multi-group path.

Capability and validation:

- No-spec analyses keep pairwise and post-hoc comparisons enabled but disable capability metrics.
- Capability metrics are computed per group only when specs are valid and policy allows it.
- Monte Carlo validation is opt-in and disabled by default.
