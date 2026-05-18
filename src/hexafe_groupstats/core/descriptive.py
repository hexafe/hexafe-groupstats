"""Descriptive statistics."""

from __future__ import annotations

import numpy as np

from ..domain.result_models import DescriptiveStats, GroupPreprocessResult


def compute_descriptive_stats(preprocessed: tuple[GroupPreprocessResult, ...]) -> tuple[DescriptiveStats, ...]:
    rows: list[DescriptiveStats] = []
    for group in preprocessed:
        values = group.values
        if group.sample_size == 0:
            continue
        q1, median, q3 = (
            (group.q1, group.median, group.q3)
            if group.q1 is not None and group.median is not None and group.q3 is not None
            else tuple(float(value) for value in np.percentile(values, [25, 50, 75]))
        )
        rows.append(
            DescriptiveStats(
                group=group.label,
                n=group.sample_size,
                mean=group.mean if group.mean is not None else float(np.mean(values)),
                std=group.std if group.sample_size > 1 else None,
                median=float(median),
                q1=float(q1),
                q3=float(q3),
                iqr=group.iqr if group.iqr is not None else float(q3 - q1),
                minimum=group.minimum if group.minimum is not None else float(np.min(values)),
                maximum=group.maximum if group.maximum is not None else float(np.max(values)),
                warnings=group.warnings,
            )
        )
    return tuple(rows)


__all__ = ["compute_descriptive_stats"]
