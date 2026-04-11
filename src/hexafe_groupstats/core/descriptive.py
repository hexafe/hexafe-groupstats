"""Descriptive statistics."""

from __future__ import annotations

import numpy as np

from ..domain.result_models import DescriptiveStats, GroupPreprocessResult


def compute_descriptive_stats(preprocessed: tuple[GroupPreprocessResult, ...]) -> tuple[DescriptiveStats, ...]:
    rows: list[DescriptiveStats] = []
    for group in preprocessed:
        values = group.values
        if values.size == 0:
            continue
        q1, median, q3 = np.percentile(values, [25, 50, 75])
        rows.append(
            DescriptiveStats(
                group=group.label,
                n=group.sample_size,
                mean=float(np.mean(values)),
                std=float(np.std(values, ddof=1)) if values.size > 1 else None,
                median=float(median),
                q1=float(q1),
                q3=float(q3),
                iqr=float(q3 - q1),
                minimum=float(np.min(values)),
                maximum=float(np.max(values)),
                warnings=group.warnings,
            )
        )
    return tuple(rows)


__all__ = ["compute_descriptive_stats"]

