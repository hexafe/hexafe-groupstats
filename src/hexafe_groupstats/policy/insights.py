"""Deterministic high-level insight generation owned by the engine."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..domain.models import AnalysisPolicy
from ..domain.result_models import (
    AnalysisDiagnostics,
    CapabilityResult,
    DescriptiveStats,
    DistributionProfile,
    GroupPreprocessResult,
    MetricInsight,
    OmnibusTestResult,
    PairwiseResult,
)

DEFAULT_CAPABILITY_BENCHMARK = 1.33


@dataclass(frozen=True, slots=True)
class _CapabilitySummary:
    headline: str
    why: str
    action: str
    status_class: str
    priority_score: float
    cautions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _DifferenceSummary:
    headline: str
    why: str
    action: str
    status_class: str
    priority_score: float
    cautions: tuple[str, ...] = ()


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


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _format_number(value: float | None, *, digits: int = 3) -> str:
    if not _finite(value):
        return "n/a"
    return f"{float(value):.{digits}g}"


def _capability_actual_value(row: CapabilityResult) -> tuple[float | None, tuple[float, float] | None, str]:
    if row.cpk is not None:
        return row.cpk, row.cpk_ci, "Cpk"
    if row.cpu is not None:
        return row.cpu, row.cpu_ci, "Cpu"
    if row.cpl is not None:
        return row.cpl, row.cpl_ci, "Cpl"
    return None, None, "capability"


def _worst_capability_row(
    capability_results: tuple[CapabilityResult, ...],
) -> tuple[CapabilityResult, float | None, tuple[float, float] | None, str] | None:
    candidates: list[tuple[float, str, CapabilityResult, float | None, tuple[float, float] | None, str]] = []
    for row in capability_results:
        actual, actual_ci, label = _capability_actual_value(row)
        if actual is None:
            continue
        candidates.append((float(actual), row.group, row, actual, actual_ci, label))
    if not candidates:
        return None
    _, _, row, actual, actual_ci, label = sorted(candidates, key=lambda item: (item[0], item[1]))[0]
    return row, actual, actual_ci, label


def _capability_summary(
    *,
    policy: AnalysisPolicy,
    capability_results: tuple[CapabilityResult, ...],
    benchmark: float,
) -> _CapabilitySummary:
    if not policy.allow_capability:
        return _CapabilitySummary(
            headline="capability unavailable",
            why="Capability is disabled because specification comparability does not support it.",
            action="Align or confirm specification limits before making capability claims.",
            status_class="descriptive_only",
            priority_score=55.0,
            cautions=("spec_mismatch",),
        )

    selected = _worst_capability_row(capability_results)
    if selected is None:
        return _CapabilitySummary(
            headline="capability unavailable",
            why="Capability could not be estimated from the available specification and sample data.",
            action="Review specification inputs and sample size before acting on capability.",
            status_class="capability_unavailable",
            priority_score=45.0,
            cautions=("capability_ci_unavailable",),
        )

    row, actual, actual_ci, actual_label = selected
    cp = row.cp
    lower_bound = actual_ci[0] if actual_ci is not None else None
    cautions = []
    if actual_ci is None:
        cautions.append("capability_ci_unavailable")
    for warning in row.warnings:
        if warning.startswith("ci_unavailable"):
            if "capability_ci_unavailable" not in cautions:
                cautions.append("capability_ci_unavailable")
        elif warning == "one_sided_spec":
            cautions.append("one_sided_spec")

    if _finite(cp) and float(cp) >= benchmark and _finite(actual) and float(actual) < benchmark:
        return _CapabilitySummary(
            headline="capability limited by centering",
            why=(
                f"{row.group} has acceptable spread potential "
                f"(Cp={_format_number(cp)}), but actual position is weak "
                f"({actual_label}={_format_number(actual)})."
            ),
            action="Check setup bias, target alignment, and mean shift before widening tolerances.",
            status_class="capability_centering_issue",
            priority_score=92.0,
            cautions=tuple(dict.fromkeys(cautions)),
        )

    if _finite(cp) and float(cp) < benchmark and _finite(actual) and float(actual) < benchmark:
        return _CapabilitySummary(
            headline="capability limited by spread",
            why=(
                f"{row.group} is below the {benchmark:.2f} benchmark for both spread potential "
                f"(Cp={_format_number(cp)}) and actual capability ({actual_label}={_format_number(actual)})."
            ),
            action="Reduce process variation before relying on centering adjustments.",
            status_class="capability_spread_issue",
            priority_score=95.0,
            cautions=tuple(dict.fromkeys(cautions)),
        )

    if _finite(actual) and float(actual) >= benchmark:
        if _finite(lower_bound) and float(lower_bound) > benchmark:
            return _CapabilitySummary(
                headline="capable with confidence",
                why=(
                    f"{row.group} meets the {benchmark:.2f} benchmark and the lower confidence bound "
                    f"also clears it ({actual_label} lower={_format_number(lower_bound)})."
                ),
                action="Keep monitoring the process and preserve the current controls.",
                status_class="capable_confident",
                priority_score=20.0,
                cautions=tuple(dict.fromkeys(cautions)),
            )
        if _finite(lower_bound) and float(lower_bound) <= benchmark:
            return _CapabilitySummary(
                headline="possibly capable, confidence weak",
                why=(
                    f"{row.group} point capability meets {benchmark:.2f} "
                    f"({actual_label}={_format_number(actual)}), but the lower bound does not "
                    f"({_format_number(lower_bound)})."
                ),
                action="Collect more data or reduce uncertainty before treating capability as confirmed.",
                status_class="capability_confidence_weak",
                priority_score=68.0,
                cautions=tuple(dict.fromkeys(cautions)),
            )
        return _CapabilitySummary(
            headline="possibly capable, confidence unavailable",
            why=(
                f"{row.group} point capability meets {benchmark:.2f} "
                f"({actual_label}={_format_number(actual)}), but confidence bounds are unavailable."
            ),
            action="Increase sample size before treating capability as confirmed.",
            status_class="capability_confidence_unavailable",
            priority_score=62.0,
            cautions=tuple(dict.fromkeys(cautions + ["capability_ci_unavailable"])),
        )

    if _finite(actual):
        return _CapabilitySummary(
            headline="capability below benchmark",
            why=f"{row.group} is below the {benchmark:.2f} benchmark ({actual_label}={_format_number(actual)}).",
            action="Investigate variation and centering before relaxing acceptance criteria.",
            status_class="capability_below_benchmark",
            priority_score=88.0,
            cautions=tuple(dict.fromkeys(cautions)),
        )

    return _CapabilitySummary(
        headline="capability unavailable",
        why="Capability could not be classified from the available estimates.",
        action="Review sample size and specification inputs before acting on capability.",
        status_class="capability_unavailable",
        priority_score=45.0,
        cautions=tuple(dict.fromkeys(cautions + ["capability_ci_unavailable"])),
    )


def _effect_magnitude(effect_size: float | None, effect_type: str | None) -> str:
    if not _finite(effect_size):
        return "unknown"
    value = abs(float(effect_size))
    normalized_type = str(effect_type or "").strip().lower()
    if normalized_type == "cliffs_delta":
        if value < 0.147:
            return "tiny"
        if value < 0.33:
            return "small"
        if value < 0.474:
            return "moderate"
        return "large"
    if normalized_type in {"eta_squared", "omega_squared"}:
        if value < 0.01:
            return "tiny"
        if value < 0.06:
            return "small"
        if value < 0.14:
            return "moderate"
        return "large"
    if value < 0.2:
        return "tiny"
    if value < 0.5:
        return "small"
    if value < 0.8:
        return "moderate"
    return "large"


def _pair_label(row: PairwiseResult) -> str:
    return f"{row.group_a} vs {row.group_b}"


def _difference_summary(
    *,
    pairwise_results: tuple[PairwiseResult, ...],
    omnibus: OmnibusTestResult,
    low_power_caution: bool,
    alpha: float,
) -> _DifferenceSummary:
    best = _best_pair(pairwise_results)
    if best is not None:
        p_value = best.adjusted_p_value
        magnitude = _effect_magnitude(best.effect_size, best.effect_type)
        pair = _pair_label(best)
        effect_text = f"{best.effect_type}={_format_number(best.effect_size)}" if best.effect_type else "effect unavailable"
        if best.significant and magnitude in {"moderate", "large"}:
            return _DifferenceSummary(
                headline="meaningful group difference",
                why=f"{pair} is significant after correction and the effect is {magnitude} ({effect_text}).",
                action="Start with this pair and verify likely process drivers before changing settings.",
                status_class="meaningful_difference",
                priority_score=82.0 if magnitude == "moderate" else 90.0,
            )
        if best.significant and magnitude in {"tiny", "small"}:
            return _DifferenceSummary(
                headline="statistical difference, operational impact limited",
                why=f"{pair} is statistically significant, but the effect is {magnitude} ({effect_text}).",
                action="Confirm the gap matters operationally before changing process settings.",
                status_class="statistical_minor",
                priority_score=48.0,
            )
        if not best.significant and magnitude in {"moderate", "large"} and low_power_caution:
            return _DifferenceSummary(
                headline="possible group difference, confidence limited",
                why=f"{pair} has a {magnitude} observed effect, but corrected evidence is not conclusive.",
                action="Collect more balanced data before deciding there is no actionable difference.",
                status_class="possible_difference_low_power",
                priority_score=64.0,
                cautions=("low_power",),
            )
        if not best.significant and magnitude in {"moderate", "large"}:
            return _DifferenceSummary(
                headline="possible group difference",
                why=f"{pair} has a {magnitude} observed effect, but corrected evidence is not conclusive.",
                action="Review the practical gap and continue monitoring before changing settings.",
                status_class="possible_difference",
                priority_score=54.0,
            )
        return _DifferenceSummary(
            headline="no actionable group difference",
            why=f"No corrected pairwise comparison shows both statistical and practical evidence of a meaningful gap.",
            action="No immediate group-difference action; continue routine monitoring.",
            status_class="no_actionable_difference",
            priority_score=25.0,
        )

    if omnibus.p_value is not None and omnibus.effect_size is not None:
        magnitude = _effect_magnitude(omnibus.effect_size, omnibus.effect_type)
        if omnibus.p_value < alpha and magnitude in {"moderate", "large"}:
            return _DifferenceSummary(
                headline="meaningful overall group difference",
                why=f"The overall test is significant and the effect is {magnitude}.",
                action="Review post-hoc comparisons or group summaries to locate the driver.",
                status_class="meaningful_omnibus_difference",
                priority_score=76.0,
            )
        if omnibus.p_value < alpha:
            return _DifferenceSummary(
                headline="statistical overall difference, operational impact limited",
                why=f"The overall test is significant, but the effect is {magnitude}.",
                action="Confirm the overall gap matters operationally before changing settings.",
                status_class="statistical_minor",
                priority_score=44.0,
            )

    return _DifferenceSummary(
        headline="no actionable group difference",
        why="No valid pairwise signal is available for a practical group-difference decision.",
        action="Use descriptive statistics and collect more data if a practical gap is still suspected.",
        status_class="no_actionable_difference",
        priority_score=25.0,
    )


def _mean_range_text(descriptive_stats: tuple[DescriptiveStats, ...]) -> str:
    mean_rows = sorted(descriptive_stats, key=lambda row: row.mean)
    if not mean_rows:
        return ""
    low = mean_rows[0]
    high = mean_rows[-1]
    return f"Mean range: lowest={low.group} ({low.mean:.4g}), highest={high.group} ({high.mean:.4g})."


def _base_cautions(
    *,
    preprocessed: tuple[GroupPreprocessResult, ...],
    diagnostics: AnalysisDiagnostics,
    distribution_profiles: tuple[DistributionProfile, ...],
    policy: AnalysisPolicy,
) -> tuple[str, ...]:
    cautions: list[str] = []
    if any(group.is_small_n or group.sample_size < 5 for group in preprocessed):
        cautions.append("low_n")
    flags = set(diagnostics.metric_flags)
    if "IMBALANCED N" in flags:
        cautions.append("imbalanced_groups")
    if "SEVERELY IMBALANCED N" in flags:
        cautions.append("severely_imbalanced_groups")
    if policy.spec_status.value != "EXACT_MATCH":
        cautions.append("spec_mismatch")
    unreliable_distribution_flags = {
        "high_skew",
        "high_kurtosis",
        "normaltest_rejected",
        "constant_distribution",
    }
    if any(set(profile.warnings) & unreliable_distribution_flags for profile in distribution_profiles):
        cautions.append("distribution_fit_unreliable")
    return tuple(dict.fromkeys(cautions))


def _stability_cautions(
    preprocessed: tuple[GroupPreprocessResult, ...],
    *,
    ordered_sequence_available: bool,
) -> tuple[str, ...]:
    if not ordered_sequence_available:
        return ("time_order_unavailable",)

    for group in preprocessed:
        values = np.asarray(group.values, dtype=float)
        values = values[np.isfinite(values)]
        if values.size < 8:
            continue
        sigma = float(np.std(values, ddof=1))
        if sigma <= 0 or not math.isfinite(sigma):
            continue
        midpoint = values.size // 2
        first_mean = float(np.mean(values[:midpoint]))
        second_mean = float(np.mean(values[midpoint:]))
        slope = float(np.polyfit(np.arange(values.size, dtype=float), values, 1)[0])
        if abs(second_mean - first_mean) >= 0.5 * sigma or abs(slope) * values.size >= sigma:
            return ("stability_drift_signal",)
    return tuple()


def flatten_metric_insights(insights: tuple[MetricInsight, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    for insight in insights:
        for value in (insight.headline, insight.why, insight.first_action):
            text = str(value or "").strip()
            if text:
                lines.append(text)
        if insight.confidence_or_caution:
            lines.append("Caution: " + "; ".join(insight.confidence_or_caution))
    return tuple(lines)


def build_structured_metric_insights(
    *,
    metric_name: str,
    preprocessed: tuple[GroupPreprocessResult, ...],
    descriptive_stats: tuple[DescriptiveStats, ...],
    pairwise_results: tuple[PairwiseResult, ...],
    omnibus: OmnibusTestResult,
    capability_results: tuple[CapabilityResult, ...],
    distribution_profiles: tuple[DistributionProfile, ...],
    policy: AnalysisPolicy,
    diagnostics: AnalysisDiagnostics,
    alpha: float = 0.05,
    capability_benchmark: float = DEFAULT_CAPABILITY_BENCHMARK,
    ordered_sequence_available: bool = False,
) -> tuple[MetricInsight, ...]:
    capability = _capability_summary(
        policy=policy,
        capability_results=capability_results,
        benchmark=capability_benchmark,
    )
    base_cautions = _base_cautions(
        preprocessed=preprocessed,
        diagnostics=diagnostics,
        distribution_profiles=distribution_profiles,
        policy=policy,
    )
    low_power_caution = any(
        caution in base_cautions
        for caution in ("low_n", "imbalanced_groups", "severely_imbalanced_groups")
    )
    difference = _difference_summary(
        pairwise_results=pairwise_results,
        omnibus=omnibus,
        low_power_caution=low_power_caution,
        alpha=alpha,
    )
    stability = _stability_cautions(
        preprocessed,
        ordered_sequence_available=ordered_sequence_available,
    )

    if difference.status_class == "no_actionable_difference" and capability.status_class not in {
        "capability_unavailable",
        "descriptive_only",
    }:
        primary = capability
    elif capability.status_class == "descriptive_only":
        primary = capability
    else:
        primary = capability if capability.priority_score >= difference.priority_score else difference
    secondary = difference if primary is capability else capability
    cautions = tuple(
        dict.fromkeys(
            base_cautions
            + capability.cautions
            + difference.cautions
            + stability
        )
    )
    secondary_text = ""
    if secondary.status_class not in {
        "capable_confident",
        "no_actionable_difference",
        "capability_unavailable",
    }:
        secondary_text = f" {secondary.headline.capitalize()} also applies."
    mean_range = _mean_range_text(descriptive_stats)
    why = primary.why + secondary_text
    if mean_range and primary.status_class in {"no_actionable_difference", "descriptive_only"}:
        why = f"{why} {mean_range}"

    return (
        MetricInsight(
            headline=primary.headline,
            why=why,
            first_action=primary.action,
            confidence_or_caution=cautions,
            priority_score=primary.priority_score,
            status_class=primary.status_class,
        ),
    )


def build_metric_insights(**kwargs) -> tuple[str, ...]:
    return flatten_metric_insights(build_structured_metric_insights(**kwargs))


__all__ = [
    "DEFAULT_CAPABILITY_BENCHMARK",
    "build_metric_insights",
    "build_structured_metric_insights",
    "flatten_metric_insights",
]
