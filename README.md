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

- `analyze_metric(...)`: use when you already have Python lists grouped by line, machine, batch, supplier, or treatment.
- `analyze_dataframe(...)`: use when your data is in a pandas DataFrame or CSV.
- `SpecLimits`: pass lower, nominal, and upper specs so the engine can compute capability and centering signals.
- `MetricAnalysisResult`: typed result object containing assumptions, selected test, post-hoc comparisons, capability, diagnostics, and insights.
- `MetricInsight`: compact engine-owned decision summary with `headline`, `why`, `first_action`, and caution tags.

`hexafe-groupstats` accepts grouped numeric samples through `analyze_metric(...)` / `compare_groups(...)` as a mapping such as `{"Line A": [99.8, 100.1], "Line B": [100.9, 101.0]}`, or tidy DataFrame/CSV-style data through `analyze_dataframe(...)` with configurable `metric_column`, `group_column`, `value_column`, `lsl_column`, `nominal_column`, and `usl_column`; Metroliza-shaped payloads can use `hexafe_groupstats.adapters.metroliza.analyze_metroliza_payload(...)`. At minimum, provide a metric name and grouped measurement values; group-comparison output needs at least two usable non-empty groups after numeric coercion, while blank/non-numeric values are dropped. Spec limits are optional, but capability and centering output require valid lower, nominal, and upper specs, supplied as `SpecLimits(...)`, a dict with `lsl`/`nominal`/`usl` or `LSL`/`NOMINAL`/`USL`, a `(lsl, nominal, usl)` tuple/list, or DataFrame spec columns. Statistical behavior can be configured with `AnalysisConfig`, including alpha, multiple-comparison correction, post-hoc selection, confidence intervals, small-n threshold, variance test, multi-group effect size, distribution diagnostics, capability benchmark, ordered-sequence stability checks, Monte Carlo validation, and backend selection.

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

Short reasoning behind the result:

- Welch ANOVA was selected because the normality checks passed but the variance check failed.
- Games-Howell was selected because it is the matching post-hoc method for the unequal-variance multi-group path.
- The insight is not based on p-value alone; it combines corrected significance, effect size, capability, and caution tags.
- Line B is shifted high. Line C has the weakest capability confidence because its Cpk lower bound falls below the default 1.33 benchmark.
- `time_order_unavailable` means the input has no trustworthy run order, so the engine does not invent a drift/stability judgement.

## Analyze CSV or Pandas Data

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

If your CSV is wide, reshape it first with `melt(...)` into metric, group, and value columns.

## Convert Results To DataFrames

The pandas adapters flatten typed results into report-ready tables.

```python
from hexafe_groupstats.adapters.pandas import (
    results_to_capability_dataframe,
    results_to_descriptive_dataframe,
    results_to_posthoc_dataframe,
)

descriptive_df = results_to_descriptive_dataframe(results)
posthoc_df = results_to_posthoc_dataframe(results)
capability_df = results_to_capability_dataframe(results)

print(descriptive_df[["metric", "group", "n", "mean", "std", "cpk"]].round(3).to_dict(orient="records"))
print(posthoc_df[["metric", "group_a", "group_b", "method_name", "adjusted_p_value", "effect_size"]].round(6).to_dict(orient="records"))
print(capability_df[["metric", "group", "cp", "cpk", "cpk_ci", "warnings"]].round(3).to_dict(orient="records"))
```

Example output from the full fill-weight data:

```text
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

## Notes

- `backend="auto"` currently resolves to the Python backend.
- `backend="rust"` is intentionally not available in v1 and fails in a controlled way.
- Multi-group paths now use dedicated post-hoc families:
  - `ANOVA` -> Tukey HSD / Tukey-Kramer
  - `Welch ANOVA` -> Games-Howell
  - `Kruskal-Wallis` -> Dunn
- Capability metrics are computed per group only when specs are valid and policy allows it.
- Monte Carlo validation is opt-in and disabled by default.
