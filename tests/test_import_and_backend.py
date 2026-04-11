from __future__ import annotations

import os
import subprocess
import sys

import pytest

from hexafe_groupstats import AnalysisConfig, compare_groups
from hexafe_groupstats.native.backends import BackendUnavailableError


def test_auto_backend_uses_python():
    result = compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="auto"))
    assert result.backend_used == "python"


def test_python_backend_explicitly_works():
    result = compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="python"))
    assert result.backend_used == "python"


def test_rust_backend_is_controlled_failure():
    with pytest.raises(BackendUnavailableError):
        compare_groups({"A": [1, 2, 3], "B": [2, 3, 4]}, config=AnalysisConfig(backend="rust"))


def test_package_import_is_clean_and_does_not_eagerly_import_pandas():
    env = os.environ.copy()
    env["PYTHONPATH"] = str((__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import hexafe_groupstats; print('pandas' in sys.modules); print(hasattr(hexafe_groupstats, 'analyze_metric'))",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    lines = completed.stdout.strip().splitlines()
    assert lines == ["False", "True"]
