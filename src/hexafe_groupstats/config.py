"""Configuration for the analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .domain.enums import BackendName, CorrectionMethod, MultiGroupEffect, PostHocMethod, VarianceTest


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """Configuration surface for backend selection and statistical behavior."""

    alpha: float = 0.05
    correction_method: str = CorrectionMethod.HOLM.value
    posthoc_method: str = PostHocMethod.AUTO.value
    include_effect_size_ci: bool = False
    ci_level: float = 0.95
    ci_bootstrap_iterations: int = 1000
    small_n_threshold: int = 3
    variance_test: str = VarianceTest.BROWN_FORSYTHE.value
    multi_group_effect: str = MultiGroupEffect.ETA_SQUARED.value
    distribution_diagnostics: bool = True
    capability_alpha: float = 0.05
    capability_benchmark: float = 1.33
    ordered_sequence_available: bool = False
    simulation_validation_iterations: int = 0
    simulation_random_seed: int = 42
    backend: str = BackendName.AUTO.value
    enable_rust_in_auto: bool = False


def _enum_values(enum_class: type[Enum]) -> set[str]:
    return {str(item.value) for item in enum_class}


def _normalize_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


def _require_probability(name: str, value: object) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number between 0 and 1.")
    if not 0.0 < float(value) < 1.0:
        raise ValueError(f"{name} must be greater than 0 and less than 1.")


def _require_positive_int(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def _require_non_negative_int(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")


def validate_analysis_config(config: AnalysisConfig) -> None:
    """Validate public configuration before statistical work starts."""

    _require_probability("alpha", config.alpha)
    _require_probability("ci_level", config.ci_level)
    _require_probability("capability_alpha", config.capability_alpha)
    _require_positive_int("ci_bootstrap_iterations", config.ci_bootstrap_iterations)
    _require_positive_int("small_n_threshold", config.small_n_threshold)
    _require_non_negative_int("simulation_validation_iterations", config.simulation_validation_iterations)
    if not isinstance(config.simulation_random_seed, int) or isinstance(config.simulation_random_seed, bool):
        raise ValueError("simulation_random_seed must be an integer.")
    if (
        not isinstance(config.capability_benchmark, int | float)
        or isinstance(config.capability_benchmark, bool)
        or not math.isfinite(float(config.capability_benchmark))
        or float(config.capability_benchmark) <= 0.0
    ):
        raise ValueError("capability_benchmark must be a positive finite number.")

    normalized_correction = _normalize_key(config.correction_method)
    correction_aliases = {
        "holm_bonferroni": CorrectionMethod.HOLM.value,
        "benjamini_hochberg": CorrectionMethod.BH.value,
        "fdr_bh": CorrectionMethod.BH.value,
    }
    if correction_aliases.get(normalized_correction, normalized_correction) not in _enum_values(CorrectionMethod):
        raise ValueError(f"Unsupported correction_method: {config.correction_method}")
    if _normalize_key(config.posthoc_method) not in _enum_values(PostHocMethod):
        raise ValueError(f"Unsupported posthoc_method: {config.posthoc_method}")
    if _normalize_key(config.variance_test) not in _enum_values(VarianceTest):
        raise ValueError(f"Unsupported variance_test: {config.variance_test}")
    if _normalize_key(config.multi_group_effect) not in _enum_values(MultiGroupEffect):
        raise ValueError(f"Unsupported multi_group_effect: {config.multi_group_effect}")
    if _normalize_key(config.backend) not in _enum_values(BackendName):
        raise ValueError(f"Unsupported backend: {config.backend}")


__all__ = ["AnalysisConfig", "validate_analysis_config"]
