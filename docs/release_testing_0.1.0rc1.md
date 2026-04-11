# 0.1.0rc1 Release Testing

Use this note to validate the release candidate before consuming it in Metroliza.

## Scope

- Import the package in a clean Python environment.
- Verify `analyze_metric(...)`, `compare_groups(...)`, `analyze_dataframe(...)`, and spec-policy helpers.
- Check pandas input/output adapters and row-dict adapters.
- Exercise capability results, post-hoc results, and Monte Carlo validation with small synthetic data.
- Confirm `backend="auto"` and `backend="python"` work without native dependencies.

## Suggested checks

- Run the package test suite.
- Load a small CSV into a tidy DataFrame with `metric`, `group`, and `value` columns.
- Confirm Metroliza can consume adapter output without importing package internals at runtime.

## Expected behavior

- Pure Python analysis should work everywhere, including notebooks and Colab.
- Empty, constant, low-`n`, and non-normal groups should fail safely with diagnostics.
- Multi-group results should use the dedicated post-hoc families.
- Capability should appear only when the spec policy allows it.

## Do not test here

- Rust backend execution.
- Workbook rendering.
- UI, charts, or report-generation flows.
