# Changelog

## Unreleased

### Changed

- Documented public report-label helpers and tightened README input-format guidance.
- Added Ruff to the development dependency set and CI test matrix.
- Separated no-spec analyses from invalid specs: pairwise/post-hoc output remains enabled without specs, while capability is explicitly disabled.
- Added explicit method-reference documentation for public APIs, adapters, selected statistical methods, corrections, capability, diagnostics, validation, and backend selection.
- Added a lightweight benchmark script for Python baseline and future native-backend acceptance checks.
- Included docs and scripts in source distributions.
- Added an optional PyO3 Rust backend scaffold and native parametric pairwise kernel, while keeping Python as the default backend.
- Added Rust/native source files to source distributions and documented benchmark-first native usage.

### Fixed

- Cleaned minor Ruff findings in imports and insight text helpers.
- Added stricter `AnalysisConfig` and DataFrame input validation with clear errors for unsupported options, missing required columns, and partial spec-column sets.
- Added metric-level pandas export rows and fuller simulation stability serialization.
- Optimized Python numeric coercion, pairwise conversion, bootstrap CI, and Monte Carlo resampling paths.
- Made pandas categorical grouping explicit to avoid future pandas warning noise and unobserved-category outputs.

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
