"""User-facing high-level insight generation."""

from __future__ import annotations

from ..domain.models import AnalysisPolicy
from ..domain.result_models import AnalysisDiagnostics, DescriptiveStats, PairwiseResult


def _best_pair(pairwise_results: tuple[PairwiseResult, ...]) -> PairwiseResult | None:
    if not pairwise_results:
        return None
    return sorted(
        pairwise_results,
        key=lambda row: (
            row.adjusted_p_value is None,
            row.adjusted_p_value if row.adjusted_p_value is not None else float("inf"),
            -(abs(row.effect_size) if row.effect_size is not None else 0.0),
            row.group_a,
            row.group_b,
        ),
    )[0]


def build_metric_insights(
    *,
    metric_name: str,
    descriptive_stats: tuple[DescriptiveStats, ...],
    pairwise_results: tuple[PairwiseResult, ...],
    policy: AnalysisPolicy,
    diagnostics: AnalysisDiagnostics,
) -> tuple[str, ...]:
    lines = [f"Status: {policy.spec_status.value}; mode={policy.analysis_restriction_label}."]
    best = _best_pair(pairwise_results)
    if best is not None:
        detail_parts = []
        if best.adjusted_p_value is not None:
            detail_parts.append(f"adj p={best.adjusted_p_value:.4f}")
        if best.effect_size is not None:
            detail_parts.append(f"effect={best.effect_size:.3f}")
        suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
        lines.append(f"Primary signal: {best.group_a} vs {best.group_b} via {best.test_name}{suffix}.")
    elif policy.allow_pairwise:
        lines.append("Primary signal: pairwise comparison was enabled but yielded no valid rows.")
    else:
        lines.append("Primary signal: pairwise comparison is disabled by policy.")

    mean_rows = sorted(descriptive_stats, key=lambda row: row.mean)
    if mean_rows:
        low = mean_rows[0]
        high = mean_rows[-1]
        lines.append(f"Mean range: lowest={low.group} ({low.mean:.4g}), highest={high.group} ({high.mean:.4g}).")
    else:
        lines.append(diagnostics.comment)
    return tuple(lines[:3])


__all__ = ["build_metric_insights"]

