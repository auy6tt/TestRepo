#!/usr/bin/env python3
"""Convert well-structured Word files to tagged PDFs with LibreOffice, then check them.

The PDF can only be as good as the Word file. Before converting, the script
checks each .docx for a title, a language, heading styles, alt text on images
and header rows on tables, and warns you about anything missing. Fix those in
Word (or ask Claude to fix the .docx) and run it again.

After converting, it runs the same checks as triage_pdfs.py on the new PDF.
  --compare OLD.pdf   shows the old and new file side by side and writes
                      comparison.md (one input file only)
  --validate          also runs veraPDF (PDF/UA-1 machine checks), if installed

LibreOffice export settings used: tagged PDF on, PDF/UA on (turn it off with
--no-pdfua), bookmarks from headings on.

Examples:
  python docx_to_tagged_pdf.py agenda.docx --out fixed/
  python docx_to_tagged_pdf.py agenda.docx --out fixed/ --compare downloads/agenda.pdf --validate
  python docx_to_tagged_pdf.py sources/*.docx --out fixed/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triage_pdfs import print_record, triage_one  # noqa: E402

WRITER_TYPES = {".docx", ".doc", ".odt", ".rtf", ".docm", ".dotx"}


def find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in ("/Applications/LibreOffice.app/Contents/MacOS/soffice",
                      r"C:\Program Files\LibreOffice\program\soffice.exe",
                      r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if Path(candidate).exists():
            return candidate
    return None


def export_filter(tagged: bool = True, pdfua: bool = True) -> str:
    def flag(value: bool) -> dict:
        return {"type": "boolean", "value": "true" if value else "false"}

    options = {"UseTaggedPDF": flag(tagged), "PDFUACompliance": flag(pdfua and tagged),
               "ExportBookmarks": flag(True), "ExportNotes": flag(False)}
    return "pdf:writer_pdf_Export:" + json.dumps(options, separators=(",", ":"))


def convert(inputs: list[Path], out_dir: Path, tagged: bool = True, pdfua: bool = True,
            timeout: int = 600) -> list[Path]:
    """Convert Writer documents to PDF with LibreOffice. Returns the PDF paths."""
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice was not found. Install it (Linux: sudo apt-get install -y "
                           "libreoffice-writer; Mac/Windows: libreoffice.org) and try again.")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile:
        command = [soffice, f"-env:UserInstallation={Path(profile).resolve().as_uri()}", "--headless",
                   "--norestore", "--convert-to", export_filter(tagged, pdfua), "--outdir", str(out_dir),
                   *[str(p) for p in inputs]]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    outputs = [out_dir / (p.stem + ".pdf") for p in inputs]
    missing = [p for p in outputs if not p.exists()]
    if missing:
        detail = (result.stderr or result.stdout or "").strip()
        hint = ""
        if "could not be loaded" in detail:
            hint = ("\nLibreOffice may be missing its Writer part. On Ubuntu or Debian run: "
                    "sudo apt-get install -y libreoffice-writer")
        raise RuntimeError(f"LibreOffice did not create {', '.join(p.name for p in missing)}.\n{detail}{hint}")
    return outputs


COMPARE_ROWS = [
    ("Tagged", lambda r: r["tagged"]),
    ("Text", lambda r: r["text"]),
    ("Title", lambda r: r["title"] or "(none)"),
    ("Has title", lambda r: r["has_title"]),
    ("Title bar shows title", lambda r: "Yes" if r.get("display_title") else "No"),
    ("Language", lambda r: r["lang"] or "(none)"),
    ("Tags (elements)", lambda r: (r.get("struct") or {}).get("elements", 0)),
    ("Headings", lambda r: (r.get("struct") or {}).get("headings", 0)),
    ("Lists", lambda r: (r.get("struct") or {}).get("lists", 0)),
    ("Tables / header cells", lambda r: f"{(r.get('struct') or {}).get('tables', 0)} / {(r.get('struct') or {}).get('th', 0)}"),
    ("Images / without alt text", lambda r: f"{(r.get('struct') or {}).get('figures', 0)} / {(r.get('struct') or {}).get('figures_no_alt', 0)}"),
    ("Bookmarks", lambda r: r["bookmarks"]),
    ("Pages", lambda r: r["pages"]),
    ("Issues found", lambda r: "; ".join(r["issues"]) or "none"),
    ("Suggested action", lambda r: r["action"]),
]


def comparison_markdown(name: str, before: dict, after: dict, checks: dict | None) -> str:
    lines = [f"# Before and after: {name}", "",
             f"Made on {dt.date.today().isoformat()} with docx_to_tagged_pdf.py. Automated checks only.", "",
             f"| Check | Before ({before['file']}) | After ({after['file']}) |", "|---|---|---|"]
    for label, getter in COMPARE_ROWS:
        lines.append(f"| {label} | {getter(before)} | {getter(after)} |")
    if checks:
        old = checks.get(str(Path(before["path"]).resolve()))
        new = checks.get(str(Path(after["path"]).resolve()))
        lines.append(f"| veraPDF PDF/UA-1 machine checks | {old['summary'] if old else 'not run'} | "
                     f"{new['summary'] if new else 'not run'} |")
        for label, result in (("before", old), ("after", new)):
            if result and result["rules"]:
                lines += ["", f"veraPDF rules failed ({label}):", ""]
                lines += [f"- {rule['plain']} (rule {rule['rule']}, {rule['failed_checks']} "
                          f"check{'s' if rule['failed_checks'] != 1 else ''})" for rule in result["rules"]]
        lines += ["", "veraPDF tests the parts of PDF/UA a machine can test. Passing them does not mean "
                  "the file is accessible: a person still checks it."]
    lines += ["", "## What a person still has to check", "",
              "- Reading order: read the whole file with NVDA (NVDA+Down arrow) and compare with what you see.",
              "- Alt text: each image's text alternative says what matters; decorative images are not read.",
              "- Tables: header cells are announced when you move through cells (Ctrl+Alt+arrow keys).",
              "- Run PAC (free, Windows) or Acrobat Pro's accessibility check and save the report.",
              "- Record the results in the remediation log. Do not call the file 'compliant'.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Word files to tagged PDF with LibreOffice and check the result.")
    parser.add_argument("inputs", nargs="+", help=".docx files (also .doc, .odt, .rtf)")
    parser.add_argument("--out", default="tagged-pdf", help="output folder (default: %(default)s)")
    parser.add_argument("--compare", help="the old PDF, to show before and after (one input only)")
    parser.add_argument("--validate", action="store_true", help="also run veraPDF PDF/UA-1 checks (needs veraPDF)")
    parser.add_argument("--no-pdfua", action="store_true", help="export tagged PDF without the PDF/UA option")
    args = parser.parse_args(argv)

    inputs = [Path(p) for p in args.inputs]
    for path in inputs:
        if not path.exists() or path.suffix.lower() not in WRITER_TYPES:
            print(f"Not a Word or Writer file: {path}", file=sys.stderr)
            return 1
    if args.compare and len(inputs) != 1:
        print("--compare works with one input file at a time.", file=sys.stderr)
        return 1

    print("Checking the Word files first (the PDF can only be as good as the source):")
    for path in inputs:
        if path.suffix.lower() == ".docx":
            rec = triage_one(path)
            problems = [i for i in rec["issues"]]
            print(f"  {path.name}: " + ("no problems found by the basic checks" if not problems else "; ".join(problems)))
            if problems:
                print("    Fix these in Word (title: File > Info > Properties; language: Review > Language; "
                      "headings: Home > Styles; alt text: right-click the image > View Alt Text), then convert again.")

    out_dir = Path(args.out)
    try:
        outputs = convert(inputs, out_dir, tagged=True, pdfua=not args.no_pdfua)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 2

    checks = None
    if args.validate:
        try:
            from validate_pdfs import find_verapdf, run_verapdf
            command = find_verapdf()
            if command is None:
                print("veraPDF not found, skipping --validate (see setup.sh --verapdf).", file=sys.stderr)
            else:
                targets = [*outputs, *([Path(args.compare)] if args.compare else [])]
                checks = run_verapdf(targets, command=command)
        except Exception as exc:  # validation is optional; report and continue
            print(f"veraPDF check failed: {exc}", file=sys.stderr)

    print("\nChecks on the new PDF files:")
    after_records = []
    for pdf in outputs:
        rec = triage_one(pdf)
        after_records.append(rec)
        print_record(rec)
        if checks and str(pdf.resolve()) in checks:
            print(f"  veraPDF:       {checks[str(pdf.resolve())]['summary']}")

    if args.compare:
        before = triage_one(Path(args.compare))
        after = after_records[0]
        report = comparison_markdown(inputs[0].stem, before, after, checks)
        (out_dir / "comparison.md").write_text(report, encoding="utf-8")
        print("\nBefore and after:")
        width = max(len(label) for label, _ in COMPARE_ROWS) + 2
        for label, getter in COMPARE_ROWS[:-2]:
            print(f"  {label:<{width}} {str(getter(before))[:38]:<40} {str(getter(after))[:38]}")
        if checks:
            for rec, label in ((before, "before"), (after, "after")):
                result = checks.get(str(Path(rec["path"]).resolve()))
                if result:
                    print(f"  veraPDF ({label}): {result['summary']}")
        print(f"\nWrote {out_dir / 'comparison.md'}")
    print("\nNext: a person checks reading order, alt text and tables with NVDA, plus PAC or Acrobat. "
          "Record it in the remediation log. Never call the file 'compliant'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
