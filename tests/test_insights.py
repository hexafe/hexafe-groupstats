from __future__ import annotations

import numpy as np
from scipy.stats import norm

from hexafe_groupstats import AnalysisConfig, SpecLimits, analyze_metric


def _normal_grid(n: int, *, sigma: float = 1.0, mean: float = 0.0) -> np.ndarray:
    return norm.ppf(np.linspace(0.05, 0.95, n)) * sigma + mean


def _primary(result):
    assert result.structured_insights
    return result.structured_insights[0]


def test_capability_can_be_confirmed_by_lower_bound():
    values = _normal_grid(40, sigma=0.12, mean=10.0)
    result = analyze_metric(
        "diameter",
        {"A": values, "B": values + 0.01},
        spec_limits=SpecLimits(lsl=8.0, nominal=10.0, usl=12.0),
    )

    insight = _primary(result)
    assert insight.status_class == "capable_confident"
    assert "capable with confidence" == insight.headline
    assert "capability_ci_unavailable" not in insight.confidence_or_caution


def test_capability_point_estimate_can_be_ok_with_weak_confidence():
    values = _normal_grid(25, sigma=0.47, mean=10.0)
    result = analyze_metric(
        "diameter",
        {"A": values, "B": values + 0.01},
        spec_limits=SpecLimits(lsl=8.0, nominal=10.0, usl=12.0),
    )

    insight = _primary(result)
    assert insight.status_class == "capability_confidence_weak"
    assert insight.headline == "possibly capable, confidence weak"


def test_capability_distinguishes_centering_issue_from_spread_issue():
    centered_too_wide = _normal_grid(40, sigma=0.8, mean=10.0)
    shifted_tight = _normal_grid(40, sigma=0.12, mean=11.75)

    spread = analyze_metric(
        "diameter",
        {"A": centered_too_wide, "B": centered_too_wide + 0.01},
        spec_limits=SpecLimits(lsl=8.0, nominal=10.0, usl=12.0),
    )
    centering = analyze_metric(
        "diameter",
        {"A": shifted_tight, "B": shifted_tight + 0.01},
        spec_limits=SpecLimits(lsl=8.0, nominal=10.0, usl=12.0),
    )

    assert _primary(spread).status_class == "capability_spread_issue"
    assert _primary(centering).status_class == "capability_centering_issue"


def test_significant_tiny_effect_is_operationally_minor():
    base = _normal_grid(2000, sigma=1.0, mean=0.0)
    result = analyze_metric("offset", {"A": base, "B": base + 0.1})

    insight = _primary(result)
    assert insight.status_class == "statistical_minor"
    assert insight.headline == "statistical difference, operational impact limited"


def test_low_n_and_spec_mismatch_are_caution_tags():
    result = analyze_metric(
        "diameter",
        {"A": [1.0, 1.1], "B": [1.2, 1.3]},
        spec_limits=[
            SpecLimits(lsl=0.0, nominal=1.0, usl=2.0),
            SpecLimits(lsl=0.0, nominal=1.1, usl=2.0),
        ],
    )

    insight = _primary(result)
    assert insight.status_class == "descriptive_only"
    assert "low_n" in insight.confidence_or_caution
    assert "spec_mismatch" in insight.confidence_or_caution


def test_stability_caution_requires_trustworthy_order():
    unordered = analyze_metric("drift", {"A": np.linspace(0.0, 1.0, 12), "B": np.linspace(0.1, 1.1, 12)})
    ordered = analyze_metric(
        "drift",
        {"A": np.linspace(0.0, 1.0, 12), "B": np.linspace(0.1, 1.1, 12)},
        config=AnalysisConfig(ordered_sequence_available=True),
    )

    assert "time_order_unavailable" in _primary(unordered).confidence_or_caution
    assert "time_order_unavailable" not in _primary(ordered).confidence_or_caution
    assert "stability_drift_signal" in _primary(ordered).confidence_or_caution
