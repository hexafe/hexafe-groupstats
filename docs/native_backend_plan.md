# Native Backend Plan

`hexafe-groupstats` already has the backend abstraction needed for future native acceleration.

## Current state

The package ships with:

- `native.protocols.GroupStatsBackend`
- `native.backends.resolve_backend(...)`
- `native.python_backend.PythonBackend`
- `native.rust_backend_stub.RustBackendStub`

The Python backend is the reference implementation and the default runtime path.
The Rust backend is not required for installation, tests, or correctness.

## Why Rust is optional in v1

Rust is worth adding only where the workload is dominated by repeated numeric kernels.
That should not delay the library release because the Python implementation already works in clean environments, including notebooks and Colab.

Keeping Rust optional avoids:

- cargo/maturin build requirements
- platform-specific installation failures
- breaking users who only need the pure-Python path
- entangling statistical correctness with compile-time availability

## Candidate hotspots

The best future Rust candidates are the parts that repeat over many groups or bootstrap iterations:

- numeric coercion and normalization
- pairwise batch comparisons
- bootstrap percentile confidence intervals
- any future batched omnibus kernels

These are already isolated behind the backend protocol, so they can be replaced without changing the public API.

## Protocol plug-in points

Future backends should implement the existing protocol methods:

- `coerce_numeric_sequence(...)`
- `compute_pairwise_batch(...)`
- `bootstrap_percentile_ci(...)`
- `bootstrap_percentile_ci_batch(...)`

That is enough to accelerate the current engine without leaking backend-specific types into the domain models.

## Parity expectations

A future Rust backend should match the Python backend within normal floating-point tolerance.
Parity tests should cover:

- empty groups
- constant groups
- low-n and large-n edge cases
- two-group and multi-group flows
- correction methods
- effect-size calculations
- bootstrap CI behavior

The Python backend should remain available as the fallback and as the correctness oracle for tests.

