import subprocess
import sys
from pathlib import Path

import pytest


def check_types(checker, python_version, fixture):
    project_root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", checker]
    if checker == "pyright":
        command += ["--pythonpath", sys.executable, "--pythonversion", python_version]
    else:
        command += ["check", "--python", sys.executable, "--python-version", python_version]
    return subprocess.run(
        [*command, str(project_root / "tests" / "typing" / fixture)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.parametrize("python_version", ["3.9", "3.10"])
@pytest.mark.parametrize(
    ("checker", "fixture"),
    [("pyright", "loads_config_types.py"), ("pyright", "load_return_types.py"), ("ty", "load_return_types.py")],
)
def test_loads_preserves_config_types(checker, python_version, fixture):
    result = check_types(checker, python_version, fixture)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("checker", "diagnostic"),
    [("pyright", "reportIncompatibleMethodOverride"), ("ty", "invalid-method-override")],
)
def test_load_override_must_match_return_type(checker, diagnostic):
    result = check_types(checker, "3.10", "invalid_load_override.py")
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr
