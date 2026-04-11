"""Metroliza-specific integration adapter kept outside the engine core."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..config import AnalysisConfig
from ..core.engine import analyze_groups
from ..domain.models import SpecLimits
from ..domain.result_models import MetricAnalysisResult
from .rows import capability_rows, descriptive_rows, distribution_rows, metric_row, pairwise_rows, posthoc_rows


def analyze_metroliza_payload(
    payload: Mapping[str, Any],
    *,
    metric_name: str | None = None,
    config: AnalysisConfig | None = None,
) -> MetricAnalysisResult:
    metric = str(
        metric_name
        or payload.get("metric")
        or payload.get("HEADER - AX")
        or payload.get("HEADER")
        or "metric"
    )
    groups_payload = payload.get("groups") or payload.get("grouped_values")
    if groups_payload is None:
        raise ValueError("Metroliza payload must contain 'groups' or 'grouped_values'.")

    if isinstance(groups_payload, Mapping):
        grouped_values = {str(group): values for group, values in groups_payload.items()}
    else:
        grouped_values = {
            str(item.get("group") or item.get("GROUP")): item.get("values") or item.get("MEAS") or []
            for item in groups_payload
        }

    specs = payload.get("spec_limits")
    if specs is None:
        specs = SpecLimits(
            lsl=payload.get("LSL"),
            nominal=payload.get("NOMINAL"),
            usl=payload.get("USL"),
        )
    return analyze_groups(metric_name=metric, groups=grouped_values, spec_limits=specs, config=config)


def to_metroliza_rows(result: MetricAnalysisResult) -> dict[str, Any]:
    metric_summary = metric_row(result)
    metric_summary.update(
        {
            "spec_status_label": result.spec_status.value,
            "difference_index_status": "DIFFERENCE"
            if any(row.significant for row in result.pairwise_results)
            else ("USE CAUTION" if not result.analysis_policy.allow_pairwise else "NO DIFFERENCE"),
        }
    )
    output_pairwise = []
    for row in result.pairwise_results:
        output_pairwise.append(
            {
                "metric": row.metric,
                "group_a": row.group_a,
                "group_b": row.group_b,
                "p_value": row.p_value,
                "adjusted_p_value": row.adjusted_p_value,
                "effect_size": row.effect_size,
                "test_used": row.test_name,
                "difference": "YES" if row.significant and result.analysis_policy.allow_pairwise else "NO",
                "comment": "DIFFERENCE"
                if row.significant and result.analysis_policy.allow_pairwise
                else ("DESCRIPTIVE ONLY" if not result.analysis_policy.allow_pairwise else "NO DIFFERENCE"),
                "flags": "; ".join(result.diagnostics.metric_flags) if result.diagnostics.metric_flags else "none",
            }
        )
    return {
        "metric_row": metric_summary,
        "descriptive_rows": descriptive_rows(result),
        "pairwise_rows": output_pairwise,
        "posthoc_rows": posthoc_rows(result),
        "capability_rows": capability_rows(result),
        "distribution_rows": distribution_rows(result),
    }


__all__ = ["analyze_metroliza_payload", "to_metroliza_rows"]
