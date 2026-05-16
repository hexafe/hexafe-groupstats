"""Lightweight performance baseline for hexafe-groupstats.

Run from a checkout with the package installed, for example:

    python scripts/benchmark_groupstats.py --repeat 5
    python scripts/benchmark_groupstats.py --profile standard --repeat 5
"""

from __future__ import annotations

import argparse
import statistics
import time
from collections.abc import Callable

import numpy as np

from hexafe_groupstats import AnalysisConfig, SpecLimits, analyze_dataframe, analyze_metric


Benchmark = tuple[str, Callable[[], object]]


def _normal_groups(
    *,
    group_count: int,
    sample_size: int,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    return {
        f"G{index + 1:02d}": rng.normal(
            loc=index * 0.15,
            scale=1.0 + (index % 3) * 0.1,
            size=sample_size,
        )
        for index in range(group_count)
    }


def _profile_sizes(profile: str) -> dict[str, int]:
    if profile == "standard":
        return {
            "medium_groups": 6,
            "medium_n": 250,
            "many_groups": 20,
            "many_n": 80,
            "bootstrap_groups": 4,
            "bootstrap_n": 120,
            "simulation_groups": 5,
            "simulation_n": 50,
            "dataframe_metrics": 12,
            "dataframe_groups": 4,
            "dataframe_n": 80,
        }
    return {
        "medium_groups": 4,
        "medium_n": 60,
        "many_groups": 10,
        "many_n": 30,
        "bootstrap_groups": 3,
        "bootstrap_n": 40,
        "simulation_groups": 3,
        "simulation_n": 25,
        "dataframe_metrics": 3,
        "dataframe_groups": 3,
        "dataframe_n": 30,
    }


def _config(backend: str) -> AnalysisConfig:
    return AnalysisConfig(backend=backend)


def _build_benchmarks(
    *,
    backend: str,
    profile: str,
    bootstrap_iterations: int,
    simulation_iterations: int,
) -> list[Benchmark]:
    sizes = _profile_sizes(profile)
    small_groups = _normal_groups(group_count=2, sample_size=30, seed=10)
    medium_groups = _normal_groups(
        group_count=sizes["medium_groups"],
        sample_size=sizes["medium_n"],
        seed=20,
    )
    many_pairwise_groups = _normal_groups(
        group_count=sizes["many_groups"],
        sample_size=sizes["many_n"],
        seed=30,
    )
    bootstrap_groups = _normal_groups(
        group_count=sizes["bootstrap_groups"],
        sample_size=sizes["bootstrap_n"],
        seed=40,
    )
    simulation_groups = _normal_groups(
        group_count=sizes["simulation_groups"],
        sample_size=sizes["simulation_n"],
        seed=50,
    )

    benchmarks: list[Benchmark] = [
        (
            "small_two_group",
            lambda: analyze_metric("small", small_groups, config=_config(backend)),
        ),
        (
            "medium_multi_group",
            lambda: analyze_metric(
                "medium",
                medium_groups,
                spec_limits=SpecLimits(lsl=-5.0, nominal=0.0, usl=5.0),
                config=_config(backend),
            ),
        ),
        (
            "many_pairwise_groups",
            lambda: analyze_metric("many_pairwise", many_pairwise_groups, config=_config(backend)),
        ),
        (
            "bootstrap_effect_ci",
            lambda: analyze_metric(
                "bootstrap",
                bootstrap_groups,
                config=AnalysisConfig(
                    backend=backend,
                    include_effect_size_ci=True,
                    ci_bootstrap_iterations=bootstrap_iterations,
                ),
            ),
        ),
        (
            "monte_carlo_validation",
            lambda: analyze_metric(
                "simulation",
                simulation_groups,
                config=AnalysisConfig(
                    backend=backend,
                    simulation_validation_iterations=simulation_iterations,
                    simulation_random_seed=123,
                ),
            ),
        ),
    ]

    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return benchmarks

    rows = []
    for metric_index in range(sizes["dataframe_metrics"]):
        groups = _normal_groups(
            group_count=sizes["dataframe_groups"],
            sample_size=sizes["dataframe_n"],
            seed=100 + metric_index,
        )
        for group, values in groups.items():
            for value in values:
                rows.append(
                    {
                        "metric": f"m{metric_index:02d}",
                        "group": group,
                        "value": value,
                        "LSL": -5.0,
                        "NOMINAL": 0.0,
                        "USL": 5.0,
                    }
                )
    frame = pd.DataFrame(rows)
    benchmarks.append(("dataframe_metric_batch", lambda: analyze_dataframe(frame, config=_config(backend))))
    return benchmarks


def _time_call(callback: Callable[[], object], *, repeat: int, warmup: int) -> list[float]:
    for _ in range(warmup):
        callback()
    durations: list[float] = []
    for _ in range(repeat):
        start = time.perf_counter()
        callback()
        durations.append(time.perf_counter() - start)
    return durations


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the Python groupstats baseline.")
    parser.add_argument(
        "--profile",
        choices=("quick", "standard"),
        default="quick",
        help="Fixture size profile. Use standard for deeper local profiling.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "python", "rust"),
        default="python",
        help="Backend to benchmark.",
    )
    parser.add_argument("--repeat", type=int, default=5, help="Timed runs per scenario.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per scenario.")
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=32,
        help="Bootstrap iterations for the effect-size CI scenario.",
    )
    parser.add_argument(
        "--simulation-iterations",
        type=int,
        default=8,
        help="Monte Carlo iterations for the validation scenario.",
    )
    args = parser.parse_args()

    if args.repeat < 1 or args.warmup < 0:
        raise SystemExit("repeat must be >= 1 and warmup must be >= 0")

    print("scenario,median_ms,min_ms,max_ms,repeat")
    for name, callback in _build_benchmarks(
        backend=args.backend,
        profile=args.profile,
        bootstrap_iterations=args.bootstrap_iterations,
        simulation_iterations=args.simulation_iterations,
    ):
        durations = _time_call(callback, repeat=args.repeat, warmup=args.warmup)
        values_ms = [duration * 1000.0 for duration in durations]
        print(
            f"{name},"
            f"{statistics.median(values_ms):.3f},"
            f"{min(values_ms):.3f},"
            f"{max(values_ms):.3f},"
            f"{args.repeat}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
