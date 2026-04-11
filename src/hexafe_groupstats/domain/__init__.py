"""Domain enums and typed models."""

from .enums import BackendName, CorrectionMethod, MultiGroupEffect, PostHocMethod, SelectionMode, SpecStatus, VarianceTest
from .models import AnalysisPolicy, SpecLimits
from .result_models import CapabilityResult, DescriptiveStats, DistributionProfile, MetricAnalysisResult, PairwiseResult

__all__ = [
    "AnalysisPolicy",
    "BackendName",
    "CapabilityResult",
    "CorrectionMethod",
    "DescriptiveStats",
    "DistributionProfile",
    "MetricAnalysisResult",
    "MultiGroupEffect",
    "PairwiseResult",
    "PostHocMethod",
    "SelectionMode",
    "SpecLimits",
    "SpecStatus",
    "VarianceTest",
]
