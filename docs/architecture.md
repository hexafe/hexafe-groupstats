# Architecture

`hexafe-groupstats` is split into layers so the statistical engine stays reusable outside Metroliza.

## Core vs policy vs adapters

`src/hexafe_groupstats/core/` contains the statistical workflow:

- preprocessing and numeric coercion
- assumption checks
- omnibus test selection
- legacy pairwise comparisons for 2-group compatibility
- dedicated multi-group post-hoc procedures
- capability calculations
- distribution diagnostics
- optional Monte Carlo stability validation
- multiple-comparison correction
- effect size calculations
- bootstrap confidence intervals
- descriptive statistics
- orchestration in `engine.py`

`src/hexafe_groupstats/policy/` contains decision and summary logic:

- spec comparability classification
- analysis-policy resolution
- diagnostics generation
- compact user-facing insights

`src/hexafe_groupstats/adapters/` contains input/output translation only:

- pandas DataFrame ingestion and DataFrame output helpers
- Metroliza payload conversion
- plain row-dict adapters for downstream export layers

`src/hexafe_groupstats/domain/` contains typed enums and result models shared across the stack.
`src/hexafe_groupstats/native/` contains the backend protocol and backend resolution.

## Why workbook/export/UI code is excluded

Workbook writing, report layout, charts, and UI orchestration are application concerns, not analysis concerns.
Keeping them out of the engine avoids:

- hard dependencies on Excel writers, PyQt, or GUI runtime state
- layout-specific row schemas leaking into statistical code
- local filesystem or project-path assumptions
- runtime coupling to Metroliza-specific export flows

The engine returns typed results. Adapters can flatten those results into dicts, DataFrames, or Metroliza-shaped payloads without changing the core.

## Input shape

The preferred external shape is a tidy table:

- one row per observation
- one metric column
- one group/sensor column
- one numeric value column
- optional `LSL`, `NOMINAL`, `USL`

This keeps CSV, notebook, and adapter workflows simple. Users who already have grouped values in memory can call `analyze_metric(...)` or `compare_groups(...)` with `dict[str, list]`.

## Backend abstraction

Performance-sensitive operations go through `native.protocols.GroupStatsBackend`.
The current package ships with:

- `PythonBackend` as the always-available default
- `RustBackendStub` as a placeholder for future acceleration
- `resolve_backend(...)` for internal backend selection and fallback control

This keeps the public API backend-agnostic and avoids spreading backend branching through the statistical modules.

## Future Rust acceleration

Rust can be added behind the protocol layer without changing public function signatures or result models.
The best candidates are the repeated numeric hotspots:

- numeric coercion and array normalization
- batched pairwise comparisons
- bootstrap confidence-interval sampling
- other batch-oriented statistical kernels if they become bottlenecks

The Python backend remains the reference implementation and the correctness baseline.
