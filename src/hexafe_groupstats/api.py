"""Public library-first API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .config import AnalysisConfig
from .core.engine import analyze_groups
from .domain.models import AnalysisPolicy, SpecLimits
from .domain.result_models import MetricAnalysisResult
from .policy.analysis_policy import resolve_analysis_policy
from .policy.spec_comparability import classify_spec_status


def compare_groups(
    groups: Mapping[str, Sequence[Any]],
    *,
    metric_name: str = "metric",
    spec_limits: Any = None,
    config: AnalysisConfig | None = None,
) -> MetricAnalysisResult:
    """Analyze already-grouped samples for one metric."""

    return analyze_metric(metric_name, groups, spec_limits=spec_limits, config=config)


def analyze_metric(
    metric_name: str,
    groups: Mapping[str, Sequence[Any]],
    *,
    spec_limits: Any = None,
    config: AnalysisConfig | None = None,
) -> MetricAnalysisResult:
    """Analyze one metric from grouped samples."""

    return analyze_groups(metric_name=metric_name, groups=groups, spec_limits=spec_limits, config=config)


def analyze_dataframe(
    dataframe: Any,
    *,
    metric_column: str = "metric",
    group_column: str = "group",
    value_column: str = "value",
    lsl_column: str | None = "LSL",
    nominal_column: str | None = "NOMINAL",
    usl_column: str | None = "USL",
    config: AnalysisConfig | None = None,
) -> list[MetricAnalysisResult]:
    """Analyze a dataframe-like object without importing pandas at package import time."""

    from .adapters.pandas import analyze_dataframe as _analyze_dataframe

    return _analyze_dataframe(
        dataframe,
        metric_column=metric_column,
        group_column=group_column,
        value_column=value_column,
        lsl_column=lsl_column,
        nominal_column=nominal_column,
        usl_column=usl_column,
        config=config,
    )


__all__ = [
    "AnalysisConfig",
    "AnalysisPolicy",
    "MetricAnalysisResult",
    "SpecLimits",
    "analyze_dataframe",
    "analyze_metric",
    "classify_spec_status",
    "compare_groups",
    "resolve_analysis_policy",
]

