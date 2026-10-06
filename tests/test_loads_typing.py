import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("python_version", ["3.9", "3.10"])
def test_loads_preserves_config_types(python_version):
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--pythonpath",
            sys.executable,
            "--pythonversion",
            python_version,
            str(project_root / "tests" / "typing" / "loads_config_types.py"),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
