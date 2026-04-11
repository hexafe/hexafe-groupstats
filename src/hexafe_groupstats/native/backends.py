"""Backend selection and safe fallback logic."""

from __future__ import annotations

from .protocols import GroupStatsBackend
from .python_backend import PythonBackend
from .rust_backend_stub import RustBackendStub


class BackendUnavailableError(RuntimeError):
    """Raised when an explicitly requested backend is unavailable."""


_PYTHON_BACKEND = PythonBackend()
_RUST_BACKEND = RustBackendStub()


def _normalize_backend_name(backend: str | None) -> str:
    normalized = str(backend or "auto").strip().lower()
    if normalized not in {"auto", "python", "rust"}:
        return "auto"
    return normalized


def resolve_backend(backend: str | None = None, *, enable_rust_in_auto: bool = False) -> GroupStatsBackend:
    """Resolve an internal backend instance."""

    normalized = _normalize_backend_name(backend)
    if normalized == "python":
        return _PYTHON_BACKEND
    if normalized == "rust":
        raise BackendUnavailableError(
            "backend='rust' was requested, but the Rust backend is currently only a stub."
        )
    if enable_rust_in_auto:
        return _PYTHON_BACKEND
    return _PYTHON_BACKEND


__all__ = ["BackendUnavailableError", "resolve_backend"]
