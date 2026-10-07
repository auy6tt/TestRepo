#!/usr/bin/env python3
"""Build the minutes Word document and the motions spreadsheet from a minutes JSON file.

The JSON format is described in SCHEMA.md. The script checks the JSON against
the schema first and stops if anything is wrong. For the deeper checks (vote
counts, quorum, names, [UNCLEAR] markers) run check_minutes.py.

Outputs, written to --out-dir (default: the folder of the JSON file):
  <name>-minutes.docx   the minutes, for the secretary to review
  <name>-motions.xlsx   motions and votes, action items, questions, meeting facts
  <name>-minutes.pdf    only with --pdf (needs LibreOffice)
<name> is the JSON file name without "-minutes" (or the value of --name).

Examples:
  python build_minutes.py ../samples/wrenfield-commons-2026-09-16-minutes.json
  python build_minutes.py work/acme-hoa/2026-10-14/minutes.json --out-dir work/acme-hoa/2026-10-14/output --pdf
  python build_minutes.py minutes.json --template client-template.docx
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from minutes_common import MinutesError, find_unclear, iter_motions, load_minutes, schema_errors
from minutes_docx import TemplateError, render_docx
from minutes_xlsx import render_xlsx


def output_base(json_path: Path, name: str | None) -> str:
    if name:
        return name
    stem = json_path.stem
    for suffix in ("-minutes", "_minutes", " minutes"):
        if stem.lower().endswith(suffix):
            return stem[: -len(suffix)] or stem
    return stem


def convert_to_pdf(docx_path: Path, out_dir: Path) -> Path | None:
    """Convert a .docx to PDF with LibreOffice. Returns the PDF path, or None if it failed."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("Note: LibreOffice (soffice) was not found, so no PDF was made.", file=sys.stderr)
        return None
    with tempfile.TemporaryDirectory() as profile:
        command = [soffice, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
                   "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)]
        try:
            subprocess.run(command, capture_output=True, timeout=240, check=False)
        except subprocess.TimeoutExpired:
            print("Note: LibreOffice took too long, so no PDF was made.", file=sys.stderr)
            return None
    pdf = out_dir / f"{docx_path.stem}.pdf"
    if not pdf.exists():
        print("Note: LibreOffice did not produce a PDF.", file=sys.stderr)
        return None
    return pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build minutes (.docx) and a motions spreadsheet (.xlsx) from a minutes JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:" + __doc__.split("Examples:", 1)[1],
    )
    parser.add_argument("json", help="minutes JSON file (see SCHEMA.md)")
    parser.add_argument("--out-dir", help="folder for the output files (default: the JSON file's folder)")
    parser.add_argument("--name", help="base name for the output files (default: from the JSON file name)")
    parser.add_argument("--template", help="client .docx template with {{placeholders}} (default: the kit's own layout)")
    parser.add_argument("--no-appendix", action="store_true",
                        help="leave out the action items and motions appendices (kit layout only)")
    parser.add_argument("--no-xlsx", action="store_true", help="don't write the spreadsheet")
    parser.add_argument("--pdf", action="store_true", help="also save a PDF of the minutes (needs LibreOffice)")
    args = parser.parse_args(argv)

    json_path = Path(args.json)
    try:
        minutes = load_minutes(json_path)
    except MinutesError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    errors = schema_errors(minutes)
    if errors:
        print(f"Error: {json_path.name} does not match the minutes format (SCHEMA.md). Fix these first:",
              file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else json_path.resolve().parent
    base = output_base(json_path, args.name)
    docx_path = out_dir / f"{base}-minutes.docx"
    xlsx_path = out_dir / f"{base}-motions.xlsx"
    try:
        render_docx(minutes, docx_path, template_path=args.template, appendices=not args.no_appendix)
    except TemplateError as exc:
        print(f"Template error:\n{exc}", file=sys.stderr)
        return 2
    written = [docx_path]
    if not args.no_xlsx:
        written.append(render_xlsx(minutes, xlsx_path))
    if args.pdf:
        pdf = convert_to_pdf(docx_path, out_dir)
        if pdf:
            written.append(pdf)

    motions = list(iter_motions(minutes))
    unclear = find_unclear(minutes)
    print("Wrote:")
    for path in written:
        print(f"  {path}")
    print(f"{len(motions)} motions, {len(minutes.get('action_items') or [])} action items, "
          f"{len(minutes.get('questions') or [])} questions, {len(unclear)} [UNCLEAR] markers.")
    if unclear:
        print("The [UNCLEAR] markers are highlighted in yellow in the Word file. Resolve them with the secretary.")
    print("Next: run check_minutes.py on the JSON (add --transcript for the transcript checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
