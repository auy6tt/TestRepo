"""Every script the README runs prints its help with --help and changes nothing."""

import os
import subprocess
import sys

import pytest

from conftest import SCRIPTS_DIR

PY_SCRIPTS = ["clean_transcript.py", "build_minutes.py", "check_minutes.py", "make_template.py"]


@pytest.mark.parametrize("script", PY_SCRIPTS)
def test_python_script_help(script, tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPTS_DIR / script), "--help"],
                            capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert not any(tmp_path.iterdir())


def test_setup_help_installs_nothing(tmp_path):
    venv = tmp_path / "venv"
    env = dict(os.environ, BOARD_MINUTES_VENV=str(venv))
    result = subprocess.run(["bash", str(SCRIPTS_DIR / "setup.sh"), "--help"],
                            capture_output=True, text=True, env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
    assert not venv.exists()
