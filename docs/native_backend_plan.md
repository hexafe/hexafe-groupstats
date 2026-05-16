# Native Backend Plan

`hexafe-groupstats` has an optional Rust backend behind the existing backend abstraction.

## Current state

The package ships with:

- `native.protocols.GroupStatsBackend`
- `native.backends.resolve_backend(...)`
- `native.python_backend.PythonBackend`
- `native.rust_backend.RustBackend`
- `_hexafe_groupstats_native` PyO3 extension under `rust/`

The Python backend is the reference implementation and the default runtime path.
The Rust backend is not required for installation, tests, or correctness. It is opt-in via `backend="rust"` and source checkouts can load `cargo build --release --manifest-path rust/Cargo.toml` artifacts directly.

## Why Rust remains optional

Rust is worth adding only where the workload is dominated by repeated numeric kernels.
That should not block the library release because the Python implementation already works in clean environments, including notebooks and Colab.

Keeping Rust optional avoids:

- cargo/maturin build requirements
- platform-specific installation failures
- breaking users who only need the pure-Python path
- entangling statistical correctness with compile-time availability

## Current native policy

Current behavior:

- `backend="auto"` remains Python by default.
- `backend="rust"` uses native parametric pairwise rows when the extension is available.
- Non-parametric pairwise comparisons deliberately fall back to Python.
- Bootstrap confidence intervals deliberately fall back to Python because current NumPy vectorization is faster than list-conversion Rust calls.
- `enable_rust_in_auto=True` may use Rust when available, but should not be treated as a production default until local benchmark results justify it.

## Candidate hotspots

The best future Rust candidates are the parts that repeat over many groups or bootstrap iterations:

- numeric coercion and normalization
- pairwise batch comparisons
- bootstrap percentile confidence intervals
- any future batched omnibus kernels

These are already isolated behind the backend protocol, so they can be replaced without changing the public API.

## Benchmark gate

Do not implement or enable native acceleration without a measured baseline first.
Use the benchmark script from a checkout with the package installed:

```bash
python scripts/benchmark_groupstats.py --repeat 5
python scripts/benchmark_groupstats.py --profile standard --repeat 5
python scripts/benchmark_groupstats.py --backend rust --profile standard --repeat 5
```

The quick profile is useful for smoke checks. The standard profile should be captured before and after optimization work, especially for pairwise batches, post-hoc analysis, bootstrap confidence intervals, DataFrame metric batches, and Monte Carlo validation.

## Protocol plug-in points

Backends implement the existing protocol methods:

- `coerce_numeric_sequence(...)`
- `compute_pairwise_batch(...)`
- `bootstrap_percentile_ci(...)`
- `bootstrap_percentile_ci_batch(...)`

That is enough to accelerate the current engine without leaking backend-specific types into the domain models.

## Parity expectations

The Rust backend should match the Python backend within normal floating-point tolerance.
Parity tests should cover:

- empty groups
- constant groups
- low-n and large-n edge cases
- two-group and multi-group flows
- correction methods
- effect-size calculations
- bootstrap CI behavior

The Python backend should remain available as the fallback and as the correctness oracle for tests.
