# 0.1.0rc3 Release Testing

Use this note to validate the third release candidate before consuming it in Metroliza, notebooks, or downstream package pins.

## Scope

- Import the package in a clean Python environment and confirm `hexafe_groupstats.__version__ == "0.1.0rc3"`.
- Verify no-spec analyses keep pairwise and post-hoc output enabled while capability remains disabled.
- Verify `AnalysisConfig` rejects unsupported options with clear errors.
- Exercise tidy pandas DataFrame input, including categorical metric/group columns.
- Check row-dict and DataFrame adapters, especially `metric_row(...)` and `results_to_metric_dataframe(...)`.
- Run the benchmark script on quick and standard profiles before claiming performance changes.
- Build the optional Rust extension from a source checkout and confirm `backend="rust"` works when explicitly requested.

## Suggested checks

- Run the full Python test suite and Ruff.
- Build the source distribution and wheel with `python -m build`.
- Run `cargo fmt`, `cargo check`, and `cargo build --release --manifest-path rust/Cargo.toml` for native work.
- Run `python -m pytest tests/test_rust_backend_parity.py -q` after building the Rust artifact.
- Load a large tidy DataFrame with 5 metrics and confirm categorical columns are faster/lighter than object-string columns.

## Expected behavior

- `backend="auto"` remains Python by default.
- `backend="rust"` is opt-in and uses native parametric pairwise rows when the Rust extension is available.
- Non-parametric pairwise and bootstrap confidence intervals fall back to Python in the Rust backend.
- Source distributions include `AGENTS.md`, docs, scripts, and Rust source files.
- Release builds remain pure Python wheels unless a separate binary-wheel pipeline is added later.

## Do not claim yet

- Rust is not the global default backend.
- Rust is not a universal performance win.
- Binary Rust wheels are not part of this release candidate.
