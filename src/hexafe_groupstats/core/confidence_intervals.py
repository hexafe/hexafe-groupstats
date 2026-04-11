"""Confidence interval helpers."""

from __future__ import annotations

from .effect_sizes import omnibus_effect_type
from ..native.protocols import GroupStatsBackend


def bootstrap_effect_ci(
    *,
    backend: GroupStatsBackend,
    effect_kernel: str,
    groups,
    level: float,
    iterations: int,
    seed: int = 42,
) -> tuple[float, float] | None:
    return backend.bootstrap_percentile_ci(
        effect_kernel=effect_kernel,
        groups=list(groups),
        level=level,
        iterations=iterations,
        seed=seed,
    )


def bootstrap_pairwise_effect_cis(
    *,
    backend: GroupStatsBackend,
    effect_kernel: str,
    labels: list[str],
    groups: list,
    pairs: list[tuple[str, str]],
    level: float,
    iterations: int,
    seed: int = 42,
) -> dict[tuple[str, str], tuple[float, float] | None]:
    if not pairs:
        return {}
    label_to_index = {label: idx for idx, label in enumerate(labels)}
    pair_indexes = [(label_to_index[left], label_to_index[right]) for left, right in pairs]
    cis = backend.bootstrap_percentile_ci_batch(
        effect_kernel=effect_kernel,
        groups=groups,
        pairs=pair_indexes,
        level=level,
        iterations=iterations,
        seed=seed,
    )
    return {pair: ci for pair, ci in zip(pairs, cis)}


__all__ = ["bootstrap_effect_ci", "bootstrap_pairwise_effect_cis", "omnibus_effect_type"]

