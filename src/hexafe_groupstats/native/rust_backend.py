"""Optional Rust backend wrapper."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .protocols import GroupStatsBackend, PairwiseBackendRow
from .python_backend import PythonBackend


class RustExtensionUnavailable(RuntimeError):
    """Raised when the optional Rust extension cannot be imported."""


def _load_native_module():
    try:
        import _hexafe_groupstats_native as native_module  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment-dependent
        loaded = _load_native_module_from_checkout()
        if loaded is not None:
            return loaded
        raise RustExtensionUnavailable(
            "The optional Rust extension is not installed. "
            "Build it with `maturin build --manifest-path rust/Cargo.toml -i python` "
            "or run `cargo build --manifest-path rust/Cargo.toml` from a source checkout."
        ) from exc
    return native_module


def _load_native_module_from_checkout():
    root = Path(__file__).resolve().parents[3]
    candidates = [
        root / "rust" / "target" / "release" / "lib_hexafe_groupstats_native.so",
        root / "rust" / "target" / "maturin" / "lib_hexafe_groupstats_native.so",
        root / "rust" / "target" / "debug" / "lib_hexafe_groupstats_native.so",
    ]
    for path in candidates:
        if not path.exists():
            continue
        loader = importlib.machinery.ExtensionFileLoader("_hexafe_groupstats_native", str(path))
        spec = importlib.util.spec_from_file_location("_hexafe_groupstats_native", path, loader=loader)
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
    return None


def _as_native_groups(groups: list[NDArray[np.float64]]) -> list[list[float]]:
    return [np.asarray(group, dtype=np.float64).tolist() for group in groups]


class RustBackend(GroupStatsBackend):
    """Rust-accelerated backend with Python fallback for unsupported kernels."""

    name = "rust"

    def __init__(self) -> None:
        self._native = _load_native_module()
        self._python = PythonBackend()

    def coerce_numeric_sequence(self, values: Any) -> NDArray[np.float64]:
        return self._python.coerce_numeric_sequence(values)

    def compute_pairwise_batch(
        self,
        *,
        labels: list[str],
        groups: list[NDArray[np.float64]],
        alpha: float,
        correction_method: str,
        non_parametric: bool,
        equal_var: bool,
    ) -> list[PairwiseBackendRow]:
        if non_parametric:
            return self._python.compute_pairwise_batch(
                labels=labels,
                groups=groups,
                alpha=alpha,
                correction_method=correction_method,
                non_parametric=non_parametric,
                equal_var=equal_var,
            )

        rows = self._native.compute_pairwise_batch(
            labels,
            _as_native_groups(groups),
            alpha,
            correction_method,
            non_parametric,
            equal_var,
        )
        return [
            PairwiseBackendRow(
                group_a=row[0],
                group_b=row[1],
                test_name=row[2],
                p_value=row[3],
                effect_size=row[4],
                adjusted_p_value=row[5],
                significant=row[6],
            )
            for row in rows
        ]

    def bootstrap_percentile_ci(
        self,
        *,
        effect_kernel: str,
        groups: list[NDArray[np.float64]],
        level: float,
        iterations: int,
        seed: int,
    ) -> tuple[float, float] | None:
        return self._python.bootstrap_percentile_ci(
            effect_kernel=effect_kernel,
            groups=groups,
            level=level,
            iterations=iterations,
            seed=seed,
        )

    def bootstrap_percentile_ci_batch(
        self,
        *,
        effect_kernel: str,
        groups: list[NDArray[np.float64]],
        pairs: list[tuple[int, int]],
        level: float,
        iterations: int,
        seed: int,
    ) -> list[tuple[float, float] | None]:
        return self._python.bootstrap_percentile_ci_batch(
            effect_kernel=effect_kernel,
            groups=groups,
            pairs=pairs,
            level=level,
            iterations=iterations,
            seed=seed,
        )


__all__ = ["RustBackend", "RustExtensionUnavailable"]
