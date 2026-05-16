# QA Audit

## Scope

Audit after no-spec policy hardening, Python performance optimization, benchmark scaffolding, optional Rust backend implementation, docs updates, and coverage setup.

## Correctness Checks

- No-spec analyses now use `NO_SPEC`, keep pairwise/post-hoc enabled, and disable capability explicitly.
- Invalid and mismatched specs still route through policy gates.
- DataFrame adapters now fail clearly for missing required columns and partial spec-column sets.
- Categorical DataFrame groupings use explicit observed groups, avoiding pandas `FutureWarning` noise and unobserved-category outputs.
- `results_to_metric_dataframe(...)` exposes result-level rows for pandas consumers.
- Simulation validation serializes pairwise stability details through `metric_row(...)`.

## Performance Checks

- Python optimizations reduced standard `medium_multi_group` and `dataframe_metric_batch` time versus baseline in single-run benchmarks.
- Rust backend is functional but not globally faster because current PyO3 calls copy NumPy arrays into Python lists before entering Rust.
- `backend="auto"` correctly remains Python by default.
- Next native performance work should add a zero-copy Rust/numpy bridge before expanding auto use.

## Native Backend Checks

- Rust extension builds with `cargo build --release --manifest-path rust/Cargo.toml`.
- Source checkouts can load release artifacts directly.
- Optional Rust parity tests skip when native artifacts are unavailable.
- Native parametric pairwise rows are parity-tested against Python.
- Non-parametric pairwise and bootstrap CI deliberately fall back to Python.

## Coverage And Release Checks

- Coverage command is documented in `AGENTS.md` and configured in `pyproject.toml`.
- `python -m coverage run -m pytest -q` passed with 57 tests.
- `python -m coverage report` reported 85% total coverage.
- Source distributions include `AGENTS.md`, docs, scripts, and Rust source through `MANIFEST.in`.
- `python -m build` passed after network access was allowed for the isolated build dependencies.
- Rust build artifacts are ignored through `.gitignore`.

## Final Validation Snapshot

- `python -m ruff check .` passed.
- `python -m pytest -q` passed with 57 tests.
- `python -m coverage run -m pytest -q` passed with 57 tests.
- `python -m coverage report` passed with 85% total coverage.
- `cargo fmt --manifest-path rust/Cargo.toml --check` passed.
- `cargo check --manifest-path rust/Cargo.toml` passed.
- `cargo build --release --manifest-path rust/Cargo.toml` passed.
- `git diff --check` passed.
- `python -m build` passed.

## Residual Risks

- Single-run benchmarks are noisy; final decisions should use repeated standard benchmarks before release notes claim a specific speedup.
- Rust backend is optional and functional, but not a universal performance win yet.
- Installing a maturin wheel from the root project can conflict with the Python package name; source-checkout `cargo build --release` is the recommended local validation path until packaging is redesigned.
