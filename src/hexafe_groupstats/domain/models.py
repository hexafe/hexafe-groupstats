"""Public domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import SpecStatus


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric


@dataclass(frozen=True, slots=True)
class SpecLimits:
    """Normalized specification limits."""

    lsl: float | None = None
    nominal: float | None = None
    usl: float | None = None

    @classmethod
    def from_any(cls, value: Any) -> "SpecLimits":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls()
        if isinstance(value, dict):
            return cls(
                lsl=_coerce_optional_float(value.get("lsl") if "lsl" in value else value.get("LSL")),
                nominal=_coerce_optional_float(
                    value.get("nominal") if "nominal" in value else value.get("NOMINAL")
                ),
                usl=_coerce_optional_float(value.get("usl") if "usl" in value else value.get("USL")),
            )
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return cls(
                lsl=_coerce_optional_float(value[0]),
                nominal=_coerce_optional_float(value[1]),
                usl=_coerce_optional_float(value[2]),
            )
        raise TypeError(f"Unsupported spec representation: {type(value)!r}")

    def rounded(self, precision: int = 3) -> "SpecLimits":
        return SpecLimits(
            lsl=None if self.lsl is None else round(self.lsl, precision),
            nominal=None if self.nominal is None else round(self.nominal, precision),
            usl=None if self.usl is None else round(self.usl, precision),
        )

    def as_tuple(self) -> tuple[float | None, float | None, float | None]:
        return (self.lsl, self.nominal, self.usl)

    def is_valid(self) -> bool:
        if self.lsl is None or self.nominal is None or self.usl is None:
            return False
        if self.lsl > self.usl:
            return False
        return self.lsl <= self.nominal <= self.usl


@dataclass(frozen=True, slots=True)
class AnalysisPolicy:
    """Spec-comparability policy resolved for one metric."""

    spec_status: SpecStatus
    include_metric: bool
    allow_pairwise: bool
    allow_capability: bool
    summary: str
    analysis_restriction_label: str


__all__ = ["AnalysisPolicy", "SpecLimits"]

