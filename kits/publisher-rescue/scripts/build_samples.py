#!/usr/bin/env python3
"""Rebuild the portfolio sample from scratch: a FICTIONAL parish, St Aidan's
Church, Wrenford, taken through a whole job.

  samples/st-aidans-wrenford/
    originals/       the "client's files" (stand-ins for .pub files)
    archive/         PDFs, previews, index.xlsx, contact-sheet.html
    templates/       rebuilt newsletter, service bulletin and certificates,
                     filled in, each with a PDF, plus a print-ready booklet
    delivery-note.docx and delivery-note.pdf

Example
  python scripts/build_samples.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
KIT = SCRIPTS.parent
SAMPLE = KIT / "samples" / "st-aidans-wrenford"
CONTENT = SCRIPTS / "sample-data" / "st-aidans-wrenford.json"


def run(script: str, *args) -> None:
    print(f"\n=== {script} {' '.join(str(a) for a in args)}")
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True)


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter
                            ).parse_args(argv)
    if SAMPLE.exists():
        shutil.rmtree(SAMPLE)
    run("make_sample_archive.py", SAMPLE / "originals")
    run("convert_archive.py", SAMPLE / "originals", SAMPLE / "archive", "--ext", "all",
        "--title", "St Aidan's Church, Wrenford: Publisher archive (fictional sample)")
    run("build_templates.py", "--content", CONTENT, "--summary",
        SAMPLE / "archive" / "summary.json", "--paper", "a4", "--out",
        SAMPLE / "templates", "--pdf")
    for suffix in (".docx", ".pdf"):
        note = SAMPLE / "templates" / f"delivery-note{suffix}"
        note.replace(SAMPLE / note.name)
    run("make_booklet.py", SAMPLE / "templates" / "service-bulletin-A5-booklet.pdf")
    print(f"\nSample rebuilt in {SAMPLE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
