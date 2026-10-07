"""Shared test setup: make the scripts importable and give tests the sample files."""

import copy
import json
import sys
from pathlib import Path

import pytest

KIT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = KIT_DIR / "scripts"
SAMPLES_DIR = KIT_DIR / "samples"
TEMPLATES_DIR = KIT_DIR / "templates"
sys.path.insert(0, str(SCRIPTS_DIR))

SAMPLE_JSON = SAMPLES_DIR / "wrenfield-commons-2026-09-16-minutes.json"
SAMPLE_VTT = SAMPLES_DIR / "wrenfield-commons-2026-09-16-transcript.vtt"
SAMPLE_CLEAN = SAMPLES_DIR / "wrenfield-commons-2026-09-16-transcript-clean.txt"
SAMPLE_SPEAKERS = SAMPLES_DIR / "wrenfield-commons-speaker-map.txt"


@pytest.fixture
def sample():
    """A fresh copy of the sample minutes (safe to modify)."""
    return copy.deepcopy(json.loads(SAMPLE_JSON.read_text(encoding="utf-8")))


@pytest.fixture
def write_json(tmp_path):
    def _write(data, name="minutes.json"):
        path = tmp_path / name
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
    return _write
