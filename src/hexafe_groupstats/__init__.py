"""Reusable group-comparison and statistical analysis package."""

__version__ = "0.1.0rc3"

from .api import (
    analyze_dataframe,
    analyze_grouped_metrics,
    analyze_metric,
    classify_spec_status,
    compare_groups,
    resolve_analysis_policy,
)
from .config import AnalysisConfig
from .core.corrections import describe_correction_policy, format_correction_method
from .core.pairwise import describe_pairwise_strategy
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
    "analyze_grouped_metrics",
    "analyze_metric",
    "classify_spec_status",
    "compare_groups",
    "describe_correction_policy",
    "describe_pairwise_strategy",
    "format_correction_method",
    "resolve_analysis_policy",
]
