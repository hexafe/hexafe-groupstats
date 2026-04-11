"""Placeholder for a future optional Rust backend."""

from __future__ import annotations

from numpy.typing import NDArray

from .protocols import GroupStatsBackend


class RustBackendStub(GroupStatsBackend):
    """Explicit stub for a future pluggable Rust implementation."""

    name = "rust"

    def _raise(self) -> None:
        raise NotImplementedError(
            "The Rust backend is not implemented in this package version. "
            "Use backend='python' or backend='auto'."
        )

    def coerce_numeric_sequence(self, values):  # type: ignore[override]
        self._raise()

    def compute_pairwise_batch(self, **kwargs):  # type: ignore[override]
        self._raise()

    def bootstrap_percentile_ci(self, **kwargs):  # type: ignore[override]
        self._raise()

    def bootstrap_percentile_ci_batch(self, **kwargs):  # type: ignore[override]
        self._raise()


__all__ = ["RustBackendStub"]

