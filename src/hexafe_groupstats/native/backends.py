"""Backend selection and safe fallback logic."""

from __future__ import annotations

from .protocols import GroupStatsBackend
from .python_backend import PythonBackend
from .rust_backend import RustBackend, RustExtensionUnavailable


class BackendUnavailableError(RuntimeError):
    """Raised when an explicitly requested backend is unavailable."""


_PYTHON_BACKEND = PythonBackend()
_RUST_BACKEND: GroupStatsBackend | None = None


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
        return _resolve_rust_backend()
    if enable_rust_in_auto:
        try:
            return _resolve_rust_backend()
        except BackendUnavailableError:
            return _PYTHON_BACKEND
    return _PYTHON_BACKEND


def _resolve_rust_backend() -> GroupStatsBackend:
    global _RUST_BACKEND
    if _RUST_BACKEND is None:
        try:
            _RUST_BACKEND = RustBackend()
        except RustExtensionUnavailable as exc:
            raise BackendUnavailableError(str(exc)) from exc
    return _RUST_BACKEND


__all__ = ["BackendUnavailableError", "resolve_backend"]
