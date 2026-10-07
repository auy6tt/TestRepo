#!/usr/bin/env python3
"""
Get the plain text out of a client's questionnaire (.docx, .doc, .odt, .rtf, .pdf or .txt)
so the questions can be turned into a data dictionary or XLSForm.

Word files: LibreOffice is used when it is installed, because it keeps the automatic
question numbering ("1.", "2a)") that python-docx cannot see. Otherwise python-docx
reads paragraphs and tables in document order. PDFs need pdftotext (poppler-utils).

Usage (from the kit folder):
    python scripts/extract_text.py samples/01_client_input/lakeside_questionnaire_v1.2.docx
    python scripts/extract_text.py questionnaire.pdf -o questionnaire.txt

Always compare the text with the original layout: tick boxes, grids and arrows
("go to question 7") carry meaning too.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def with_libreoffice(path: Path) -> str | None:
    office = shutil.which("soffice") or shutil.which("libreoffice")
    if not office:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp) / "profile"
        command = [office, f"-env:UserInstallation=file://{profile.as_posix()}", "--headless",
                   "--convert-to", "txt:Text (encoded):UTF8", "--outdir", tmp, str(path)]
        try:
            subprocess.run(command, capture_output=True, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        result = Path(tmp) / (path.stem + ".txt")
        if not result.exists():
            return None
        return result.read_text(encoding="utf-8", errors="replace").lstrip(chr(0xFEFF))


def with_python_docx(path: Path) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(path)
    lines = []
    for block in doc.element.body.iterchildren():
        tag = block.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lines.append(Paragraph(block, doc).text)
        elif tag == "tbl":
            for row in Table(block, doc).rows:
                cells, seen = [], set()
                for cell in row.cells:
                    if id(cell._tc) in seen:  # a merged cell is listed once per column it spans
                        continue
                    seen.add(id(cell._tc))
                    cells.append(" ".join(p.text for p in cell.paragraphs).strip())
                lines.append(" | ".join(cells))
    return "\n".join(lines)


def extract(path: Path, prefer_python: bool = False) -> str:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        tool = shutil.which("pdftotext")
        if not tool:
            raise SystemExit("ERROR: pdftotext is not installed (poppler-utils). Ask the client for the Word file.")
        result = subprocess.run([tool, "-layout", str(path), "-"], capture_output=True, text=True, check=False)
        return result.stdout
    if suffix in (".docx", ".doc", ".odt", ".rtf"):
        if not prefer_python:
            text = with_libreoffice(path)
            if text:
                return text
        if suffix == ".docx":
            return with_python_docx(path)
        raise SystemExit(f"ERROR: {suffix} files need LibreOffice (soffice) to be read.")
    raise SystemExit(f"ERROR: unsupported file type {suffix}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract plain text from a questionnaire file.")
    parser.add_argument("file")
    parser.add_argument("-o", "--output", help="save the text to this file instead of printing it")
    parser.add_argument("--python-docx", action="store_true", help="use python-docx even if LibreOffice is installed")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: not found: {path}")
        return 2
    text = extract(path, args.python_docx)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output} ({len(text.splitlines())} lines)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
