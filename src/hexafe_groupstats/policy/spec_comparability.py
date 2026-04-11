"""Spec comparability policy helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..domain.enums import SpecStatus
from ..domain.models import SpecLimits


def _looks_like_single_spec_mapping(value: Mapping[str, Any]) -> bool:
    keys = {str(key).strip().lower() for key in value}
    return bool(keys & {"lsl", "nominal", "usl"})


def _coerce_specs(specs: Any) -> list[SpecLimits]:
    if specs is None:
        return []
    if isinstance(specs, SpecLimits):
        return [specs.rounded()]
    if isinstance(specs, Mapping):
        if _looks_like_single_spec_mapping(specs):
            return [SpecLimits.from_any(specs).rounded()]
        return [SpecLimits.from_any(value).rounded() for value in specs.values()]
    if isinstance(specs, Sequence) and not isinstance(specs, (str, bytes, bytearray)):
        return [SpecLimits.from_any(value).rounded() for value in specs]
    return [SpecLimits.from_any(specs).rounded()]


def classify_spec_status(specs: Any) -> SpecStatus:
    normalized = _coerce_specs(specs)
    if not normalized:
        return SpecStatus.INVALID_SPEC
    if any(not spec.is_valid() for spec in normalized):
        return SpecStatus.INVALID_SPEC
    nominals = {spec.nominal for spec in normalized}
    if len(nominals) > 1:
        return SpecStatus.NOM_MISMATCH
    limit_pairs = {(spec.lsl, spec.usl) for spec in normalized}
    if len(limit_pairs) > 1:
        return SpecStatus.LIMIT_MISMATCH
    return SpecStatus.EXACT_MATCH


def resolve_spec_context(specs: Any, *, missing_means_exact_match: bool = False) -> tuple[SpecLimits, SpecStatus]:
    normalized = _coerce_specs(specs)
    if not normalized:
        if missing_means_exact_match:
            return SpecLimits(), SpecStatus.EXACT_MATCH
        return SpecLimits(), SpecStatus.INVALID_SPEC
    return normalized[0], classify_spec_status(normalized)


__all__ = ["classify_spec_status", "resolve_spec_context"]

