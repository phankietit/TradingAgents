"""Verification selection must be explicit before any database allocation."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("script,args", [
    ("verify-local.sh", ["local", "--focused"]),
    ("verify-local.sh", ["local", "tests/test_native_recorder_spawn.py"]),
    ("verify-postgres-local.sh", ["--focused"]),
    ("verify-postgres-local.sh", ["--unknown", "tests/test_native_recorder_spawn.py"]),
])
def test_invalid_selection_is_rejected_before_runtime_or_db(script, args):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "TA_ALLOW_TEST_DB_RESET": "1", "PATH": "/usr/bin:/bin"}
    result = subprocess.run(["/bin/bash", str(root / "scripts" / script), *args],
        cwd=root, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert not result.stdout
    assert "Focused verification requires" in result.stderr or "Usage:" in result.stderr
