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
    mean = float(np.mean(numeric_values)) if sample_size else None
    variance = float(np.var(numeric_values, ddof=1)) if sample_size > 1 else None
    std = float(np.sqrt(variance)) if variance is not None else (0.0 if sample_size == 1 else None)
    if sample_size:
        q1, median, q3 = np.percentile(numeric_values, [25, 50, 75])
        minimum = float(np.min(numeric_values))
        maximum = float(np.max(numeric_values))
        iqr = float(q3 - q1)
    else:
        q1 = median = q3 = minimum = maximum = iqr = None

    is_constant = bool(sample_size > 1 and std is not None and np.isclose(std, 0.0))
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
        mean=mean,
        variance=variance,
        std=std,
        median=None if median is None else float(median),
        q1=None if q1 is None else float(q1),
        q3=None if q3 is None else float(q3),
        iqr=iqr,
        minimum=minimum,
        maximum=maximum,
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
