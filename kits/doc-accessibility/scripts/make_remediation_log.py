#!/usr/bin/env python3
"""Pre-fill the remediation log for files you have fixed.

Matches each PDF in --after with the file of the same name in --before, runs
the automated checks on both (and veraPDF with --validate), and adds one row
per file to the log, starting from templates/remediation-log-template.xlsx.

It fills only the automated columns. The human-check columns (PAC, reading
order, alt text, tables, links, forms, colour) say "To do" until a person has
done them. Never mark a check as passed that nobody did.

Examples:
  python make_remediation_log.py --before downloads --after fixed --out log.xlsx \\
      --work "Rebuilt in Word with headings and lists; exported tagged PDF" --validate
  python make_remediation_log.py --before downloads --after basic-fixes \\
      --fix-log basic-fixes/fix-log.csv --out log.xlsx --append
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from openpyxl import load_workbook  # noqa: E402
from openpyxl.styles import Alignment  # noqa: E402

from build_templates import LOG_COLUMNS  # noqa: E402
from triage_pdfs import triage_one  # noqa: E402

KIT = Path(__file__).resolve().parent.parent
HUMAN_COLUMNS = ["PAC result", "Reading order (NVDA)", "Alt text", "Tables", "Links", "Forms", "Colour and contrast"]


def read_csv_by(path: str | None, key: str) -> dict:
    if not path:
        return {}
    with open(path, newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle) if row.get(key)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-fill the remediation log (automated columns only).")
    parser.add_argument("--before", required=True, help="folder with the original files")
    parser.add_argument("--after", required=True, help="folder with the fixed PDFs")
    parser.add_argument("--out", required=True, help="the log .xlsx to write")
    parser.add_argument("--template", default=str(KIT / "templates" / "remediation-log-template.xlsx"))
    parser.add_argument("--append", action="store_true", help="add rows to --out if it already exists")
    parser.add_argument("--work", help="what you did (used for every file in this run)")
    parser.add_argument("--tools", help="tools you used (used for every file in this run)")
    parser.add_argument("--fix-log", help="fix-log.csv from fix_basics.py (fills 'Work done' per file)")
    parser.add_argument("--crawl", help="documents.csv from crawl_documents.py (fills the URL)")
    parser.add_argument("--validate", action="store_true", help="run veraPDF on before and after files")
    args = parser.parse_args(argv)

    before_dir, after_dir, out = Path(args.before), Path(args.after), Path(args.out)
    pairs = [(before_dir / pdf.name, pdf) for pdf in sorted(after_dir.glob("*.pdf")) if (before_dir / pdf.name).exists()]
    if not pairs:
        print("No PDFs in --after with a file of the same name in --before.", file=sys.stderr)
        return 1
    fixes, crawl = read_csv_by(args.fix_log, "file"), read_csv_by(args.crawl, "saved_as")

    checks = {}
    if args.validate:
        from validate_pdfs import find_verapdf, run_verapdf
        if find_verapdf():
            checks = run_verapdf([p for pair in pairs for p in pair])
        else:
            print("veraPDF not found; the veraPDF columns are left empty.", file=sys.stderr)

    def verapdf(path: Path) -> str:
        result = checks.get(str(path.resolve()))
        if not result:
            return "Not run"
        return "Pass" if result["compliant"] else f"Fail ({result['failed_rules']} rules)"

    book = load_workbook(out if (args.append and out.exists()) else args.template)
    sheet = book["Log"]
    headers = [name for name, _ in LOG_COLUMNS]
    next_row = sheet.max_row + 1
    while next_row > 2 and not any(sheet.cell(row=next_row - 1, column=c).value for c in range(1, 4)):
        next_row -= 1
    name_col = headers.index("File name") + 1
    already = {sheet.cell(row=r, column=name_col).value for r in range(2, next_row)}
    for before, after in pairs:
        if after.name in already:
            print(f"{after.name}: already in the log, skipped")
            continue
        old, new = triage_one(before), triage_one(after)
        fix = fixes.get(after.name, {})
        work = args.work or (f"Basic fixes: {fix['changes']}" if fix else "")
        tools = args.tools or ("fix_basics.py (pikepdf" + (", ocrmypdf and Tesseract" if "OCR done" in fix.get("ocr", "") else "")
                               + ")" if fix else "")
        if new["tagged"] != "Yes":
            status = "Basic fixes only"
        elif new["issues"]:
            status = "In progress"
        else:
            status = "Ready for human check"
        remaining = "; ".join(new["issues"]) if new["tagged"] == "Yes" else ""
        notes = "; ".join(part for part in (f"Automated checks still find: {remaining}" if remaining else "",
                                            fix.get("still_to_do", "")) if part)
        values = {
            "File ID": next_row - 1, "File name": after.name, "URL": crawl.get(before.name, {}).get("url", ""),
            "Pages": new["pages"], "Before: tagged": old["tagged"], "Before: text": old["text"],
            "Before: title": old["title"] or "(none)", "Before: language": old["lang"] or "(none)",
            "Before: veraPDF PDF/UA-1": verapdf(before) if args.validate else "",
            "Work done": work, "Tools used": tools, "After: tagged": new["tagged"],
            "After: title": new["title"] or "(none)", "After: language": new["lang"] or "(none)",
            "After: veraPDF PDF/UA-1": verapdf(after) if args.validate else "",
            "Status": status, "Notes": notes,
        }
        for name in HUMAN_COLUMNS:
            values[name] = "To do"
        for col, name in enumerate(headers, start=1):
            cell = sheet.cell(row=next_row, column=col, value=values.get(name, ""))
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        print(f"{after.name}: before tagged {old['tagged']}, after tagged {new['tagged']}; status: {status}")
        next_row += 1
    last_col = sheet.cell(row=1, column=len(headers)).column_letter
    sheet.auto_filter.ref = f"A1:{last_col}{next_row - 1}"
    out.parent.mkdir(parents=True, exist_ok=True)
    book.save(out)
    print(f"Wrote {out}. Fill the human-check columns only after a person has done each check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
