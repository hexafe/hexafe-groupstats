# Changelog

## 0.1.0rc1

Release candidate for the first standalone `hexafe-groupstats` package release.

### Added

- Standalone statistical engine for grouped comparison workflows.
- Typed public API for metric analysis, group comparison, spec policy, and pandas-friendly ingestion.
- Core preprocessing, assumption checks, omnibus selection, pairwise and multi-group comparisons, corrections, effect sizes, and confidence intervals.
- Per-group capability metrics with policy gating.
- Distribution diagnostics and optional Monte Carlo stability validation.
- Pure-Python backend as the default runtime path with optional backend abstraction for future acceleration.
- Adapters for pandas DataFrames, dict/list inputs, and Metroliza-shaped payloads.

### Notes

- Metroliza runtime coupling is intentionally excluded.
- Workbook, UI, export, and report layout code remain outside the package.
- Rust acceleration is scaffolded but not required for this release candidate.

