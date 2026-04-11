"""Analysis policy resolution."""

from __future__ import annotations

from ..domain.enums import SpecStatus
from ..domain.models import AnalysisPolicy


def resolve_analysis_policy(spec_status: SpecStatus | str) -> AnalysisPolicy:
    normalized = SpecStatus(str(spec_status).strip().upper())
    policy_by_status = {
        SpecStatus.EXACT_MATCH: AnalysisPolicy(
            spec_status=SpecStatus.EXACT_MATCH,
            include_metric=True,
            allow_pairwise=True,
            allow_capability=True,
            summary="Specs are aligned across groups; direct pairwise interpretation is supported.",
            analysis_restriction_label="Full analysis",
        ),
        SpecStatus.LIMIT_MISMATCH: AnalysisPolicy(
            spec_status=SpecStatus.LIMIT_MISMATCH,
            include_metric=True,
            allow_pairwise=True,
            allow_capability=False,
            summary="Limits differ across groups; pairwise comparison is allowed, capability metrics are disabled.",
            analysis_restriction_label="Pairwise yes; capability off",
        ),
        SpecStatus.NOM_MISMATCH: AnalysisPolicy(
            spec_status=SpecStatus.NOM_MISMATCH,
            include_metric=True,
            allow_pairwise=False,
            allow_capability=False,
            summary="Nominal values differ across groups; descriptive-only interpretation is recommended.",
            analysis_restriction_label="Descriptive only",
        ),
        SpecStatus.INVALID_SPEC: AnalysisPolicy(
            spec_status=SpecStatus.INVALID_SPEC,
            include_metric=True,
            allow_pairwise=False,
            allow_capability=False,
            summary="Specification data are missing or invalid; descriptive-only interpretation is recommended.",
            analysis_restriction_label="Descriptive only",
        ),
    }
    return policy_by_status[normalized]


__all__ = ["resolve_analysis_policy"]

