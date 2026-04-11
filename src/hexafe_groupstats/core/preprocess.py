"""Group preprocessing and numeric coercion."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from ..domain.result_models import GroupPreprocessResult
from ..native.protocols import GroupStatsBackend


def preprocess_group(
    label: Any,
    values: Sequence[Any],
    *,
    backend: GroupStatsBackend,
    small_n_threshold: int = 3,
) -> GroupPreprocessResult:
    numeric_values = backend.coerce_numeric_sequence(values)
    numeric_values = numeric_values[~np.isnan(numeric_values)]

    sample_size = int(numeric_values.size)
    is_empty = sample_size == 0
    is_constant = bool(sample_size > 1 and np.isclose(np.std(numeric_values, ddof=1), 0.0))
    is_small_n = sample_size < int(small_n_threshold)

    warnings: list[str] = []
    if is_empty:
        warnings.append("empty_after_nan_drop")
    if is_constant:
        warnings.append("constant_values")
    if is_small_n:
        warnings.append("small_n")

    return GroupPreprocessResult(
        label=str(label),
        values=numeric_values,
        sample_size=sample_size,
        is_empty=is_empty,
        is_constant=is_constant,
        is_small_n=is_small_n,
        warnings=tuple(warnings),
    )


def preprocess_groups(
    groups: Mapping[str, Sequence[Any]],
    *,
    backend: GroupStatsBackend,
    small_n_threshold: int = 3,
) -> tuple[GroupPreprocessResult, ...]:
    return tuple(
        preprocess_group(
            label,
            values,
            backend=backend,
            small_n_threshold=small_n_threshold,
        )
        for label, values in groups.items()
    )


__all__ = ["preprocess_group", "preprocess_groups"]

