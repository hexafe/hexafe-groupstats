"""Normal-theory process capability calculations."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import chi2, norm

from ..domain.models import AnalysisPolicy, SpecLimits
from ..domain.result_models import CapabilityResult, GroupPreprocessResult


def _valid(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _cp_interval(cp: float, *, sample_size: int, alpha: float) -> tuple[float, float] | None:
    dof = sample_size - 1
    if sample_size < 25 or cp < 0:
        return None
    chi2_low = float(chi2.ppf(alpha / 2.0, dof))
    chi2_high = float(chi2.ppf(1.0 - alpha / 2.0, dof))
    if chi2_low <= 0 or chi2_high <= 0:
        return None
    return (
        float(cp * math.sqrt(chi2_low / dof)),
        float(cp * math.sqrt(chi2_high / dof)),
    )


def _normal_index_interval(index_value: float, *, sample_size: int, alpha: float) -> tuple[float, float] | None:
    dof = sample_size - 1
    if sample_size < 25:
        return None
    z_value = float(norm.ppf(1.0 - alpha / 2.0))
    standard_error = math.sqrt((1.0 / (9.0 * sample_size)) + ((index_value**2) / (2.0 * dof)))
    margin = z_value * standard_error
    return (float(index_value - margin), float(index_value + margin))


def compute_group_capability(
    *,
    metric_name: str,
    group: GroupPreprocessResult,
    spec_limits: SpecLimits,
    alpha: float = 0.05,
) -> CapabilityResult:
    warnings: list[str] = []
    values = group.values
    n = int(values.size)
    mean = float(np.mean(values)) if n > 0 else None
    sigma = float(np.std(values, ddof=1)) if n > 1 else (0.0 if n == 1 else None)

    if n < 2:
        warnings.append("insufficient_n")
    if sigma is not None and np.isclose(sigma, 0.0):
        warnings.append("zero_variance")
    if n < 25:
        warnings.append("ci_unavailable_n_lt_25")
    elif n < 100:
        warnings.append("ci_approximate_n_lt_100")

    lsl, nominal, usl = spec_limits.as_tuple()
    two_sided = _valid(lsl) and _valid(usl)
    upper_only = not _valid(lsl) and _valid(usl)
    lower_only = _valid(lsl) and not _valid(usl)
    if upper_only or lower_only:
        warnings.append("one_sided_spec")

    if n < 2 or sigma is None or np.isclose(sigma, 0.0):
        return CapabilityResult(
            metric=metric_name,
            group=group.label,
            n=n,
            mean=mean,
            sigma=sigma,
            lsl=lsl,
            nominal=nominal,
            usl=usl,
            cp=None,
            cpl=None,
            cpu=None,
            cpk=None,
            ci_level=None if n < 25 else 1.0 - alpha,
            warnings=tuple(warnings),
        )

    cp = ((usl - lsl) / (6.0 * sigma)) if two_sided else None
    cpl = ((mean - lsl) / (3.0 * sigma)) if lower_only or two_sided else None
    cpu = ((usl - mean) / (3.0 * sigma)) if upper_only or two_sided else None
    cpk = min(value for value in (cpl, cpu) if value is not None) if two_sided else None

    return CapabilityResult(
        metric=metric_name,
        group=group.label,
        n=n,
        mean=mean,
        sigma=sigma,
        lsl=lsl,
        nominal=nominal,
        usl=usl,
        cp=None if cp is None or not math.isfinite(cp) else float(cp),
        cpl=None if cpl is None or not math.isfinite(cpl) else float(cpl),
        cpu=None if cpu is None or not math.isfinite(cpu) else float(cpu),
        cpk=None if cpk is None or not math.isfinite(cpk) else float(cpk),
        ci_level=None if n < 25 else 1.0 - alpha,
        cp_ci=None if cp is None else _cp_interval(float(cp), sample_size=n, alpha=alpha),
        cpl_ci=None if cpl is None else _normal_index_interval(float(cpl), sample_size=n, alpha=alpha),
        cpu_ci=None if cpu is None else _normal_index_interval(float(cpu), sample_size=n, alpha=alpha),
        cpk_ci=None if cpk is None else _normal_index_interval(float(cpk), sample_size=n, alpha=alpha),
        warnings=tuple(warnings),
    )


def compute_capability_results(
    *,
    metric_name: str,
    preprocessed: tuple[GroupPreprocessResult, ...],
    spec_limits: SpecLimits,
    policy: AnalysisPolicy,
    alpha: float = 0.05,
) -> tuple[CapabilityResult, ...]:
    if not policy.allow_capability or not spec_limits.is_valid():
        return tuple()
    return tuple(
        compute_group_capability(
            metric_name=metric_name,
            group=group,
            spec_limits=spec_limits,
            alpha=alpha,
        )
        for group in preprocessed
    )


__all__ = ["compute_capability_results", "compute_group_capability"]
