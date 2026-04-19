# 0.1.0rc2 Release Testing

Use this note to validate the second release candidate before consuming it in Metroliza or notebooks.

## Scope

- Import the package in a clean Python environment and confirm `hexafe_groupstats.__version__ == "0.1.0rc2"`.
- Verify `analyze_metric(...)`, `compare_groups(...)`, `analyze_dataframe(...)`, and spec-policy helpers.
- Check pandas input/output adapters and row-dict adapters.
- Exercise structured insights, capability results, post-hoc results, and Monte Carlo validation with small synthetic data.
- Confirm `backend="auto"` and `backend="python"` work without native dependencies.

## Suggested checks

- Run the package test suite.
- Build the source distribution and wheel with `python -m build`.
- Load a small CSV into a tidy DataFrame with `metric`, `group`, and `value` columns.
- Confirm Metroliza can consume adapter output without importing package internals at runtime.
- Confirm Monte Carlo `pairwise_stability` is populated for no-spec multi-group analyses when pairwise/post-hoc output is allowed.

## Expected behavior

- Pure Python analysis should work everywhere, including notebooks and Colab.
- Empty, constant, low-`n`, and non-normal groups should fail safely with diagnostics.
- Multi-group results should use the dedicated post-hoc families.
- Capability should appear only when the spec policy allows it.
- README terminology should explain omnibus, post-hoc/pairwise, adjusted p-values, effect size, capability metrics, and Monte Carlo stability fields clearly enough for a first-time user.

## Do not test here

- Rust backend execution.
- Workbook rendering.
- UI, charts, or report-generation flows.
