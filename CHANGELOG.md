# Changelog

## Unreleased

## 0.1.0rc2

### Added

- Structured metric insights with engine-owned `headline`, `why`, `first_action`, caution tags, priority, and status class.
- Capability confidence classification using a single benchmark, lower confidence bounds when available, and explicit CI-unavailable cautions.
- Deterministic distinction between capability spread issues, centering issues, practical group differences, statistically minor effects, and order-gated drift cautions.

### Changed

- Expanded README examples to explain input formats, result objects, statistical terminology, capability output, and Monte Carlo stability fields.
- Improved README usage examples for grouped samples, tidy CSV/DataFrame input, row adapters, and report-ready DataFrame exports.

### Fixed

- Monte Carlo validation now preserves the original no-spec input semantics during resampled reruns, so `pairwise_stability` is populated for no-spec analyses when pairwise/post-hoc output is allowed.

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
