"""Enum definitions used across the package."""

from __future__ import annotations

from enum import Enum


class StrValueEnum(str, Enum):
    """String enum with readable ``str()`` behavior."""

    def __str__(self) -> str:
        return self.value


class BackendName(StrValueEnum):
    AUTO = "auto"
    PYTHON = "python"
    RUST = "rust"


class CorrectionMethod(StrValueEnum):
    HOLM = "holm"
    BH = "bh"


class PostHocMethod(StrValueEnum):
    AUTO = "auto"
    LEGACY = "legacy"
    TUKEY = "tukey"
    GAMES_HOWELL = "games_howell"
    DUNN = "dunn"


class VarianceTest(StrValueEnum):
    BROWN_FORSYTHE = "brown_forsythe"
    LEVENE = "levene"


class MultiGroupEffect(StrValueEnum):
    ETA_SQUARED = "eta_squared"
    OMEGA_SQUARED = "omega_squared"


class SpecStatus(StrValueEnum):
    EXACT_MATCH = "EXACT_MATCH"
    LIMIT_MISMATCH = "LIMIT_MISMATCH"
    NOM_MISMATCH = "NOM_MISMATCH"
    INVALID_SPEC = "INVALID_SPEC"


class SelectionMode(StrValueEnum):
    PARAMETRIC_EQUAL_VARIANCE = "parametric_equal_variance"
    PARAMETRIC_UNEQUAL_VARIANCE = "parametric_unequal_variance"
    NON_PARAMETRIC = "non_parametric"
    UNAVAILABLE = "unavailable"


__all__ = [
    "BackendName",
    "CorrectionMethod",
    "MultiGroupEffect",
    "PostHocMethod",
    "SelectionMode",
    "SpecStatus",
    "VarianceTest",
]
