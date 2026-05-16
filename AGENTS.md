# Repository Guidelines

## Project Shape

`hexafe-groupstats` is a standalone Python package under `src/hexafe_groupstats`.
The Python backend is the correctness baseline and must remain available for notebooks, Colab, CI, and pure-Python installs.
The optional Rust backend lives under `rust/` and must stay opt-in unless benchmark and parity results justify changing that policy.

## Core Commands

Use these before handing work back:

```bash
python -m ruff check .
python -m pytest -q
python -m coverage run -m pytest -q
python -m coverage report
python -m build
```

Use this for native work:

```bash
cargo fmt --manifest-path rust/Cargo.toml
cargo check --manifest-path rust/Cargo.toml
cargo build --release --manifest-path rust/Cargo.toml
python -m pytest tests/test_rust_backend_parity.py -q
```

Use these for performance checks:

```bash
python scripts/benchmark_groupstats.py --repeat 1 --warmup 0 --bootstrap-iterations 4 --simulation-iterations 2
python scripts/benchmark_groupstats.py --profile standard --repeat 1 --warmup 0
python scripts/benchmark_groupstats.py --backend rust --repeat 1 --warmup 0 --bootstrap-iterations 4 --simulation-iterations 2
```

## Native Backend Rules

- Keep `backend="auto"` on Python by default.
- `backend="rust"` may use the optional native extension only when it is importable.
- If Rust is unavailable, raise the controlled backend error; do not silently claim Rust ran.
- Do not route a statistical method to Rust unless parity tests cover it.
- Do not enable Rust for auto mode unless benchmarks show a clear win for the intended workload.
- Current Rust backend intentionally falls back to Python for non-parametric pairwise and bootstrap CI paths.

## Documentation And QA

- Update `docs/performance_implementation_plan.md` after every performance phase.
- Update `README.md`, `docs/api_examples.md`, `docs/native_backend_plan.md`, and `CHANGELOG.md` when public behavior, backend behavior, or commands change.
- Keep Metroliza runtime imports out of this package.
- Keep source distributions complete: `AGENTS.md`, docs, scripts, and Rust source should remain included through `MANIFEST.in`.
