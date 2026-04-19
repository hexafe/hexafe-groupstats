"""Reusable group-comparison and statistical analysis package."""

__version__ = "0.1.0rc2"

from .api import analyze_dataframe, analyze_metric, classify_spec_status, compare_groups, resolve_analysis_policy
from .config import AnalysisConfig
from .domain.models import AnalysisPolicy, SpecLimits
from .domain.result_models import (
    CapabilityResult,
    DescriptiveStats,
    DistributionProfile,
    MetricAnalysisResult,
    MetricInsight,
    PairwiseResult,
)

__all__ = [
    "AnalysisConfig",
    "AnalysisPolicy",
    "CapabilityResult",
    "DescriptiveStats",
    "DistributionProfile",
    "MetricAnalysisResult",
    "MetricInsight",
    "PairwiseResult",
    "SpecLimits",
    "__version__",
    "analyze_dataframe",
    "analyze_metric",
    "classify_spec_status",
    "compare_groups",
    "resolve_analysis_policy",
]
