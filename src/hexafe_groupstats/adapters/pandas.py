"""Pandas-friendly input and output adapters."""

from __future__ import annotations

from typing import Any

from ..config import AnalysisConfig
from ..core.engine import analyze_groups
from ..domain.models import SpecLimits
from ..domain.result_models import MetricAnalysisResult
from .rows import capability_rows, descriptive_rows, distribution_rows, metric_row, pairwise_rows, posthoc_rows


def _require_pandas():
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "pandas is required for dataframe adapters. Install hexafe-groupstats[pandas] or pandas directly."
        ) from exc
    return pd


def analyze_dataframe(
    dataframe: Any,
    *,
    metric_column: str,
    group_column: str,
    value_column: str,
    lsl_column: str | None = None,
    nominal_column: str | None = None,
    usl_column: str | None = None,
    config: AnalysisConfig | None = None,
) -> list[MetricAnalysisResult]:
    pd = _require_pandas()
    frame = dataframe.copy() if hasattr(dataframe, "copy") else pd.DataFrame(dataframe)
    required_columns = {metric_column, group_column, value_column}
    missing_required = sorted(column for column in required_columns if column not in frame.columns)
    if missing_required:
        raise ValueError(f"Missing required dataframe column(s): {', '.join(missing_required)}")

    configured_spec_columns = [
        column
        for column in (lsl_column, nominal_column, usl_column)
        if column is not None
    ]
    present_spec_columns = [column for column in configured_spec_columns if column in frame.columns]
    if present_spec_columns and len(present_spec_columns) != len(configured_spec_columns):
        missing_specs = sorted(set(configured_spec_columns) - set(present_spec_columns))
        raise ValueError(
            "Spec columns must be supplied as a complete LSL/NOMINAL/USL set; "
            f"missing: {', '.join(missing_specs)}"
        )

    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    frame = frame.dropna(subset=[value_column])
    if frame.empty:
        return []

    results: list[MetricAnalysisResult] = []
    for metric_name, metric_frame in frame.groupby(metric_column, sort=True, observed=True):
        groups = {
            str(group_name): group_frame[value_column].tolist()
            for group_name, group_frame in metric_frame.groupby(group_column, sort=True, observed=True)
        }
        spec_records = None
        spec_columns_present = bool(configured_spec_columns) and all(
            column in metric_frame.columns for column in configured_spec_columns
        )
        if spec_columns_present:
            spec_records = []
            for _, row in metric_frame.iterrows():
                spec_records.append(
                    SpecLimits(
                        lsl=None if lsl_column is None else _coerce_numeric(row.get(lsl_column)),
                        nominal=None if nominal_column is None else _coerce_numeric(row.get(nominal_column)),
                        usl=None if usl_column is None else _coerce_numeric(row.get(usl_column)),
                    )
                )
        results.append(
            analyze_groups(
                metric_name=str(metric_name),
                groups=groups,
                spec_limits=spec_records,
                config=config,
            )
        )
    return results


def results_to_descriptive_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([row for result in results for row in descriptive_rows(result)])


def results_to_pairwise_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([row for result in results for row in pairwise_rows(result)])


def results_to_posthoc_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([row for result in results for row in posthoc_rows(result)])


def results_to_capability_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([row for result in results for row in capability_rows(result)])


def results_to_distribution_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([row for result in results for row in distribution_rows(result)])


def results_to_metric_dataframe(results: list[MetricAnalysisResult]):
    pd = _require_pandas()
    return pd.DataFrame([metric_row(result) for result in results])


def _coerce_numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        import pandas as pd  # type: ignore
    except ImportError:  # pragma: no cover - handled by _require_pandas
        return float(value)
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return None
    return float(numeric)


__all__ = [
    "analyze_dataframe",
    "results_to_capability_dataframe",
    "results_to_descriptive_dataframe",
    "results_to_distribution_dataframe",
    "results_to_metric_dataframe",
    "results_to_pairwise_dataframe",
    "results_to_posthoc_dataframe",
]
