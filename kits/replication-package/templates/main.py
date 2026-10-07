"""Master script: runs the whole replication package from start to finish.

Usage (from any folder):
    python main.py

What it does:
    1. Finds the package folder (the folder this file is in), so no paths need editing.
    2. Creates the folders the programs write to.
    3. Runs each program in STEPS, in order, with the same Python.
    4. Writes everything to logs/main.log: date, computer, Python and package
       versions, the output of each program, and how long each step took.
    5. Stops at the first error and says which program failed.

To adapt it, edit STEPS and FOLDERS below. Nothing else should need to change.
Each program should build its paths from its own location, for example:
    ROOT = Path(__file__).resolve().parents[1]
    df = pd.read_csv(ROOT / "data" / "raw" / "survey.csv")
"""
from __future__ import annotations

import datetime as dt
import os
import platform
import re
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Programs to run, in order, relative to this folder.
STEPS = [
    "code/01_clean_data.py",
    "code/02_analysis.py",
    "code/03_figures.py",
]

# Folders the programs write to. They are created if missing.
FOLDERS = ["data/derived", "output", "logs"]

LOG_FILE = ROOT / "logs" / "main.log"


class Log:
    """Print to the screen and to the log file at the same time."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(path, "w", encoding="utf-8")

    def __call__(self, text: str = "") -> None:
        print(text, flush=True)
        self.file.write(text + "\n")
        self.file.flush()


def installed_versions(log: Log) -> None:
    """Log the installed version of each package in requirements.txt, and flag mismatches."""
    req = ROOT / "requirements.txt"
    if not req.exists():
        log("Packages: no requirements.txt found")
        return
    log("Packages (installed version, checked against requirements.txt):")
    for raw in req.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[=<>!~;\[ @]", line, maxsplit=1)[0]
        pinned = re.search(r"==\s*([\w.]+)", line)
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            log(f"  {name}: NOT INSTALLED (run: pip install -r requirements.txt)")
            continue
        note = ""
        if pinned and pinned.group(1) != version:
            note = f"   <-- WARNING: requirements.txt says {pinned.group(1)}"
        log(f"  {name}=={version}{note}")


def run_step(script: str, log: Log) -> float:
    path = ROOT / script
    if not path.exists():
        log(f"ERROR: program not found: {script}")
        sys.exit(1)
    log("")
    log(f"=== {script} ===")
    start = time.time()
    # MPLBACKEND=Agg lets plotting code run on computers without a screen.
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable, str(path)], cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        log(line.rstrip("\n"))
    code = proc.wait()
    seconds = time.time() - start
    if code != 0:
        log(f"FAILED: {script} stopped with exit code {code} after {seconds:.1f} s. See the messages above.")
        sys.exit(code)
    log(f"--- {script} finished in {seconds:.1f} s")
    return seconds


def main() -> None:
    for folder in FOLDERS:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    log = Log(LOG_FILE)
    log(f"Replication run started {dt.datetime.now():%Y-%m-%d %H:%M:%S}")
    log(f"Package folder: {ROOT.name}")  # name only: full paths can reveal user names
    log(f"Computer: {platform.platform()}, {os.cpu_count()} CPU cores")
    venv = " (in a virtual environment)" if sys.prefix != sys.base_prefix else ""
    log(f"Python: {platform.python_version()}{venv}")
    installed_versions(log)
    total = sum(run_step(step, log) for step in STEPS)
    log("")
    log(f"All {len(STEPS)} programs finished in {total:.1f} s. Log saved to {LOG_FILE.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
