"""Configuration for the analysis engine."""

from __future__ import annotations

from dataclasses import dataclass

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


__all__ = ["AnalysisConfig"]
