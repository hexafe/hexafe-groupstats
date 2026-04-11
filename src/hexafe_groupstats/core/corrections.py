"""Multiple-comparison correction helpers."""

from __future__ import annotations


def normalize_correction_method(method: str) -> str:
    normalized = str(method).strip().lower().replace("-", "_")
    aliases = {
        "holm_bonferroni": "holm",
        "benjamini_hochberg": "bh",
        "fdr_bh": "bh",
    }
    return aliases.get(normalized, normalized)


def format_correction_method(method: str) -> str:
    normalized = normalize_correction_method(method)
    labels = {
        "holm": "Holm",
        "bh": "Benjamini-Hochberg",
    }
    if normalized not in labels:
        raise ValueError(f"Unsupported correction method: {method}")
    return labels[normalized]


def describe_correction_policy(method: str) -> str:
    normalized = normalize_correction_method(method)
    labels = {
        "holm": "Strict family-wise error control (Holm)",
        "bh": "Exploratory false-discovery-rate control (Benjamini-Hochberg/FDR)",
    }
    if normalized not in labels:
        raise ValueError(f"Unsupported correction method: {method}")
    return labels[normalized]


def adjust_pvalues(p_values: list[float | None], method: str) -> list[float | None]:
    indexed = [(idx, p) for idx, p in enumerate(p_values) if p is not None]
    adjusted: list[float | None] = [None] * len(p_values)
    if not indexed:
        return adjusted

    m = len(indexed)
    sorted_pairs = sorted(indexed, key=lambda item: item[1])
    normalized = normalize_correction_method(method)
    if normalized == "holm":
        running_max = 0.0
        for rank, (original_index, p_value) in enumerate(sorted_pairs):
            corrected = min(1.0, p_value * (m - rank))
            running_max = max(running_max, corrected)
            adjusted[original_index] = float(running_max)
        return adjusted
    if normalized == "bh":
        running_min = 1.0
        for reverse_rank, (original_index, p_value) in enumerate(reversed(sorted_pairs), start=1):
            rank = m - reverse_rank + 1
            corrected = min(1.0, p_value * m / rank)
            running_min = min(running_min, corrected)
            adjusted[original_index] = float(running_min)
        return adjusted
    raise ValueError(f"Unsupported correction method: {method}")


__all__ = [
    "adjust_pvalues",
    "describe_correction_policy",
    "format_correction_method",
    "normalize_correction_method",
]

