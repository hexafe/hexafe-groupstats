"""Internal backend protocols and payloads."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class PairwiseBackendRow:
    group_a: str
    group_b: str
    test_name: str
    p_value: float | None
    effect_size: float | None
    adjusted_p_value: float | None
    significant: bool


class GroupStatsBackend(Protocol):
    """Protocol for optional acceleration backends."""

    name: str

    def coerce_numeric_sequence(self, values: Sequence[Any] | NDArray[np.generic]) -> NDArray[np.float64]:
        """Return contiguous float64 values with NaN placeholders for failed coercions."""

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
        """Compute aligned pairwise comparisons for all group pairs."""

    def bootstrap_percentile_ci(
        self,
        *,
        effect_kernel: str,
        groups: list[NDArray[np.float64]],
        level: float,
        iterations: int,
        seed: int,
    ) -> tuple[float, float] | None:
        """Bootstrap a percentile confidence interval for one effect estimate."""

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
        """Bootstrap percentile confidence intervals for many pairwise effects."""

