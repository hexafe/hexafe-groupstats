"""Internal backend selection for performance-sensitive operations."""

from .backends import BackendUnavailableError, resolve_backend

__all__ = ["BackendUnavailableError", "resolve_backend"]

