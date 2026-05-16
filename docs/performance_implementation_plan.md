# Performance Implementation Plan

This file tracks each performance/native phase. Update it after every phase with benchmark numbers, decisions, and validation results.

## Baseline

Command:

```bash
python scripts/benchmark_groupstats.py --repeat 1 --warmup 0 --bootstrap-iterations 4 --simulation-iterations 2
python scripts/benchmark_groupstats.py --profile standard --repeat 1 --warmup 0
```

Quick baseline:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 17.586 |
| medium_multi_group | 771.884 |
| many_pairwise_groups | 58.880 |
| bootstrap_effect_ci | 20.101 |
| monte_carlo_validation | 26.624 |
| dataframe_metric_batch | 1527.679 |

Standard baseline:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 17.639 |
| medium_multi_group | 20103.988 |
| many_pairwise_groups | 137.205 |
| bootstrap_effect_ci | 5963.850 |
| monte_carlo_validation | 1078.525 |
| dataframe_metric_batch | 23280.600 |

Initial hotspot read:

- Standard `medium_multi_group` and `dataframe_metric_batch` are dominated by SciPy post-hoc and per-metric repeated analysis.
- `bootstrap_effect_ci` is dominated by repeated bootstrap resampling and effect recomputation.
- `many_pairwise_groups` is comparatively small but still benefits from avoiding repeated lookup/stat recomputation.

## Phase Log

### Phase 1: Python Pairwise/Post-Hoc Optimizations

Status: complete.

Planned changes:

- Avoid repeated `labels.index(...)` lookups when converting backend pairwise rows.
- Precompute per-group means where pairwise conversion needs mean differences.
- Reuse generated index pairs in post-hoc paths instead of rebuilding equivalent pair lists.

Results: benchmarks recorded below.

Validation:

- `python -m ruff check .` passed.
- `python -m pytest -q` passed: 51 tests.

Quick benchmark after phase 1:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 15.122 |
| medium_multi_group | 710.751 |
| many_pairwise_groups | 58.649 |
| bootstrap_effect_ci | 27.542 |
| monte_carlo_validation | 30.135 |
| dataframe_metric_batch | 1428.545 |

Standard benchmark after phase 1:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 11.514 |
| medium_multi_group | 14802.227 |
| many_pairwise_groups | 156.949 |
| bootstrap_effect_ci | 6520.679 |
| monte_carlo_validation | 1212.038 |
| dataframe_metric_batch | 35869.368 |

Decision notes:

- Quick profile improved the main DataFrame and medium multi-group paths.
- Standard `medium_multi_group` improved substantially, which confirms post-hoc/pairwise lookup cleanup helped.
- Standard DataFrame timing was noisy and regressed in this single run; keep investigating through Phase 2 and avoid claiming improvement until repeated final benchmarks confirm it.

### Phase 2: Bootstrap and Monte Carlo Optimizations

Status: complete.

Planned changes:

- Vectorize two-group bootstrap effect CI where the kernel is `cohen_d`.
- Avoid repeated Python object conversion in simulation validation.
- Keep result semantics and warnings unchanged.

Results: benchmarks recorded below.

Validation:

- `python -m ruff check .` passed.
- `python -m pytest -q` passed: 51 tests.

Quick benchmark after phase 2:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 10.546 |
| medium_multi_group | 697.588 |
| many_pairwise_groups | 54.166 |
| bootstrap_effect_ci | 19.246 |
| monte_carlo_validation | 25.847 |
| dataframe_metric_batch | 1477.408 |

Standard benchmark after phase 2:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 10.803 |
| medium_multi_group | 13598.629 |
| many_pairwise_groups | 136.805 |
| bootstrap_effect_ci | 6006.045 |
| monte_carlo_validation | 1001.887 |
| dataframe_metric_batch | 21675.733 |

Decision notes:

- Vectorized Cohen's d bootstrap and numeric-array simulation resampling improved standard profile timings versus baseline.
- DataFrame standard timing recovered below baseline after the phase 1 noisy regression.
- Remaining biggest standard-profile costs are multi-group post-hoc and per-metric DataFrame batch orchestration.

### Phase 3: Optional Rust Backend Scaffold

Status: complete.

Planned changes:

- Add a PyO3 Rust extension module named `_hexafe_groupstats_native`.
- Keep pure-Python install and normal `python -m build` path intact.
- Let `backend="rust"` use the extension only when it can be imported; otherwise raise the existing controlled backend error.

Results: benchmarks recorded below.

Validation:

- `cargo check --manifest-path rust/Cargo.toml` passed.
- `cargo build --release --manifest-path rust/Cargo.toml` passed.
- `python -m ruff check .` passed.
- `python -m pytest -q` passed: 56 tests after parity tests were added.

Quick benchmark after phase 3:

| Scenario | Python ms | Rust ms |
| --- | ---: | ---: |
| small_two_group | 12.056 | 17.055 |
| medium_multi_group | 829.201 | 831.779 |
| many_pairwise_groups | 77.820 | 58.127 |
| bootstrap_effect_ci | 28.091 | 22.440 |
| monte_carlo_validation | 34.102 | 38.083 |
| dataframe_metric_batch | 1807.458 | 1589.762 |

Standard benchmark after phase 3:

| Scenario | Python ms | Rust ms |
| --- | ---: | ---: |
| small_two_group | 20.475 | 14.543 |
| medium_multi_group | 14616.109 | 15263.582 |
| many_pairwise_groups | 164.437 | 149.201 |
| bootstrap_effect_ci | 6862.110 | 6322.191 |
| monte_carlo_validation | 1135.267 | 1185.729 |
| dataframe_metric_batch | 24088.354 | 25387.093 |

Decision notes:

- Rust backend is implemented as an optional backend and can run from a source checkout after `cargo build`.
- Native pairwise can help many-pair scenarios, but conversion overhead makes it uneven.
- `backend="auto"` remains Python.

### Phase 4: Rust Kernel Policy and Parity

Status: complete.

Changes:

- Source-checkout loader now prefers release native builds.
- Rust backend keeps native parametric pairwise, but uses Python fallback for bootstrap because NumPy vectorization is faster than the current list-conversion Rust path.
- Non-parametric pairwise remains a deliberate Python fallback until zero-copy native parity is worth implementing.
- Added optional Rust parity tests that skip when the extension is unavailable.

Quick Rust benchmark after phase 4:

| Scenario | Median ms |
| --- | ---: |
| small_two_group | 17.417 |
| medium_multi_group | 999.222 |
| many_pairwise_groups | 60.326 |
| bootstrap_effect_ci | 20.768 |
| monte_carlo_validation | 39.299 |
| dataframe_metric_batch | 1685.262 |

Decision notes:

- Current Rust backend is functionally implemented but not globally faster.
- The next native performance improvement should be a zero-copy Rust/numpy bridge before enabling Rust in `backend="auto"`.

## Final Benchmarks

Quick benchmark, repeat 3:

| Scenario | Python median ms | Rust median ms |
| --- | ---: | ---: |
| small_two_group | 11.030 | 11.998 |
| medium_multi_group | 771.097 | 731.155 |
| many_pairwise_groups | 57.531 | 58.835 |
| bootstrap_effect_ci | 19.867 | 19.887 |
| monte_carlo_validation | 27.610 | 27.204 |
| dataframe_metric_batch | 1724.117 | 1655.700 |

Standard benchmark, repeat 1:

| Scenario | Python median ms | Rust median ms |
| --- | ---: | ---: |
| small_two_group | 11.618 | 11.794 |
| medium_multi_group | 13556.728 | 14147.228 |
| many_pairwise_groups | 138.872 | 150.163 |
| bootstrap_effect_ci | 5837.854 | 6061.587 |
| monte_carlo_validation | 1018.787 | 1085.301 |
| dataframe_metric_batch | 22420.343 | 23059.640 |

Final decision:

- Python remains the default backend.
- Rust remains opt-in and useful as a validated backend path, but not as the automatic performance default.
- Further native performance work should prioritize zero-copy ndarray access before adding more Rust kernels.

## Large DataFrame Benchmark

Command shape: one-off Python benchmark using `analyze_dataframe(...)` on a 1,000,000-row, 5-column long-format frame with 5 metrics, 4 groups, and no spec columns. Generation time is excluded. Timing table below uses `repeat=5`, one warmup, and no allocation tracing.

| Input shape | Frame memory MB | Backend | Median s | Min s | Max s | Results |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| categorical columns | 18.12 | python | 1.328 | 1.292 | 1.482 | 5 |
| categorical columns | 18.12 | rust | 1.373 | 1.321 | 1.955 | 5 |
| object/string columns | 161.53 | python | 1.949 | 1.891 | 2.168 | 5 |
| object/string columns | 161.53 | rust | 1.929 | 1.733 | 2.028 | 5 |

Interpretation:

- Categoricals are materially lighter and faster for large dataframe batches.
- Rust is effectively tied with Python here because pandas grouping and conversion dominate the workload.
- This reinforces the final native decision: zero-copy dataframe/ndarray handoff matters more than adding more Rust kernels.
