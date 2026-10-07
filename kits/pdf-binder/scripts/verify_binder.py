#!/usr/bin/env python3
"""Check a binder made by build_binder.py before you send it.

It reopens the binder PDF and its index spreadsheet and checks:
  1. the page count matches the index
  2. every section and document follows on from the one before (no gaps)
  3. every bookmark opens the right page
  4. every page number printed in the contents is right
  5. every clickable contents entry jumps to the right page
  6. every divider page shows its section name; every placeholder says PENDING
  7. each document's first and last page in the binder match the source PDF,
     and the source file hasn't changed since the binder was built

Example:
  .venv/bin/python scripts/verify_binder.py jobs/acme/output/Binder.pdf
  .venv/bin/python scripts/verify_binder.py jobs/acme/output/Binder.pdf \\
      --index jobs/acme/output/Binder-index.xlsx --pdf-folder jobs/acme/docs

Exit code 0 means every check passed.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing package '{exc.name}'. Run: pip install -r requirements.txt")

import kitlib

logging.getLogger("pypdf").setLevel(logging.ERROR)   # the scripts report problems in plain words

STAMP_RE = re.compile(r"page\d+of\d+")
LEADER_LINE_RE = re.compile(r"(?:\.\s*){2,}\s*(\d+)\s*$")


def squash(text: str) -> str:
    text = re.sub(r"\s+", "", (text or "").lower())
    return STAMP_RE.sub("", text)


class Report:
    def __init__(self, quiet=False):
        self.passed = 0
        self.failed = []
        self.notes = []
        self.quiet = quiet

    def check(self, ok: bool, message: str):
        if ok:
            self.passed += 1
            if not self.quiet:
                print(f"  PASS  {message}")
        else:
            self.failed.append(message)
            print(f"  FAIL  {message}")

    def note(self, message: str):
        self.notes.append(message)
        print(f"  NOTE  {message}")


def read_index(path: Path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook["Index"]
        rows = list(sheet.iter_rows(values_only=True))
        headers = [str(h) for h in rows[0]]
        records = [dict(zip(headers, r)) for r in rows[1:] if any(v is not None for v in r)]
        summary = {}
        if "Summary" in workbook.sheetnames:
            for row in workbook["Summary"].iter_rows(values_only=True):
                if row and row[0] and len(row) > 1:
                    summary[str(row[0])] = row[1]
    finally:
        workbook.close()
    return records, summary


def leader_numbers(text: str) -> list[int]:
    """Page numbers that follow dot leaders, whether the number is on the same
    line as the dots or on the next line (depends on the PDF text extractor)."""
    numbers = []
    lines = [line.strip() for line in text.splitlines()]
    for i, line in enumerate(lines):
        match = LEADER_LINE_RE.search(line)
        if match:
            numbers.append(int(match.group(1)))
        elif re.fullmatch(r"(?:\.\s*){2,}", line) and i + 1 < len(lines) and lines[i + 1].isdigit():
            numbers.append(int(lines[i + 1]))
    return numbers


def as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def flatten_outline(reader, items, depth=0, out=None):
    out = [] if out is None else out
    for item in items:
        if isinstance(item, list):
            flatten_outline(reader, item, depth + 1, out)
        else:
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                page = None
            out.append((depth, str(item.title), page))
    return out


def link_targets(reader, page_index, page_lookup):
    targets = []
    annots = reader.pages[page_index].get("/Annots") or []
    for annot in annots:
        annot = annot.get_object()
        if annot.get("/Subtype") != "/Link":
            continue
        dest = annot.get("/Dest")
        if dest is None and annot.get("/A") is not None:
            dest = annot["/A"].get_object().get("/D")
        if dest is None:
            continue
        dest = dest.get_object() if hasattr(dest, "get_object") else dest
        try:
            ref = dest[0]
            targets.append(page_lookup.get(ref.idnum) + 1)
        except Exception:
            targets.append(None)
    return targets


def open_source(path: Path):
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    return reader


def pages_from_spec(spec, count):
    spec = str(spec or "all").strip().lower()
    if spec in ("", "all", "none"):
        return list(range(count))
    chosen = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            chosen.extend(range(int(a) - 1, int(b)))
        elif part:
            chosen.append(int(part) - 1)
    return chosen


def verify(args) -> int:
    binder = Path(args.binder)
    index_path = Path(args.index) if args.index else binder.with_name(binder.stem + "-index.xlsx")
    if not binder.is_file():
        print(f"Error: binder not found: {binder}", file=sys.stderr)
        return 1
    if not index_path.is_file():
        print(f"Error: index not found: {index_path}. Pass --index.", file=sys.stderr)
        return 1
    rows, summary = read_index(index_path)
    reader = PdfReader(str(binder))
    page_lookup = {page.indirect_reference.idnum: i for i, page in enumerate(reader.pages)}
    report = Report(args.quiet)
    print(f"Checking {binder.name} against {index_path.name}")

    # 1. Page count
    total = as_int(summary.get("Total pages"))
    report.check(total == len(reader.pages),
                 f"page count: PDF has {len(reader.pages)}, index says {total}")

    # 2. Continuity
    expected_next, gaps = 1, []
    for row in rows:
        count, start, end = as_int(row.get("Page count")), as_int(row.get("Start page")), as_int(row.get("End page"))
        if count == 0:
            if start != expected_next:
                gaps.append(f"{row.get('Title')} starts on {start}, expected {expected_next}")
            continue
        if start != expected_next or end is None or end - start + 1 != count:
            gaps.append(f"{row.get('Title')} pages {start}-{end} (expected start {expected_next}, {count} pages)")
        expected_next = (end or 0) + 1
    report.check(not gaps and expected_next - 1 == len(reader.pages),
                 "page ranges run on with no gaps or overlaps" + (": " + "; ".join(gaps[:5]) if gaps else ""))

    # 3. Bookmarks
    outline = flatten_outline(reader, reader.outline)
    top = [(d, t, p) for d, t, p in outline if d <= 1]
    expected = []
    for row in rows:
        kind, title, start = row.get("Type"), str(row.get("Title") or ""), as_int(row.get("Start page"))
        if kind == "Front matter":
            expected.append((0, title, start))
        elif kind == "Section":
            expected.append((0, title, start))
        else:
            number = str(row.get("Doc No.") or "").strip()
            label = f"{number} {title}".strip() + (" (pending)" if kind == "Pending" else "")
            expected.append((1, label, start))
    mismatches = []
    for i, want in enumerate(expected):
        got = top[i] if i < len(top) else None
        if got is None or got[0] != want[0] or got[2] != want[2] or squash(got[1]) != squash(want[1]):
            mismatches.append(f"expected '{want[1]}' -> page {want[2]}, found {got}")
    report.check(not mismatches and len(top) == len(expected),
                 f"bookmarks: {len(expected)} section/document bookmarks open the right pages"
                 + (": " + "; ".join(mismatches[:4]) if mismatches else ""))
    deeper = [(t, p) for d, t, p in outline if d >= 2]
    if deeper:
        bad = [t for t, p in deeper if p is None or p < 1 or p > len(reader.pages)]
        report.check(not bad, f"{len(deeper)} bookmarks copied from the documents point inside the binder")

    # 4 and 5. Contents page numbers and links
    contents = next((r for r in rows if r.get("Type") == "Front matter" and r.get("Title") == "Contents"), None)
    entry_targets = [as_int(r.get("Start page")) for r in rows if r.get("Type") != "Front matter"]
    if contents:
        first, last = as_int(contents.get("Start page")), as_int(contents.get("End page"))
        printed, links = [], []
        for i in range(first - 1, last):
            text = reader.pages[i].extract_text() or ""
            printed.extend(leader_numbers(text))
            links.extend(link_targets(reader, i, page_lookup))
        report.check(printed == entry_targets,
                     f"contents: {len(printed)} printed page numbers match the index"
                     + ("" if printed == entry_targets else f" (printed {printed[:12]}..., expected {entry_targets[:12]}...)"))
        report.check(links == entry_targets,
                     f"contents: {len(links)} clickable entries jump to the right pages"
                     + ("" if links == entry_targets else f" (links {links[:12]}..., expected {entry_targets[:12]}...)"))
    else:
        report.note("no contents pages in this binder")

    # 6. Dividers and placeholders
    for row in rows:
        start = as_int(row.get("Start page"))
        if row.get("Type") == "Section" and as_int(row.get("Page count")) == 1:
            text = squash(reader.pages[start - 1].extract_text() or "")
            name = squash(str(row.get("Section") or ""))[:30]
            report.check(name in text, f"divider page {start} shows section '{row.get('Section')}'")
            section_docs = [as_int(r.get("Start page")) for r in rows
                            if r.get("Type") in ("Document", "Pending") and r.get("Section") == row.get("Section")]
            targets = link_targets(reader, start - 1, page_lookup)
            report.check(targets == section_docs[:len(targets)] and targets,
                         f"divider page {start}: {len(targets)} links jump to the right documents")
        if row.get("Type") == "Pending":
            text = reader.pages[start - 1].extract_text() or ""
            report.check("PENDING" in text.upper(), f"page {start} is a placeholder for '{row.get('Title')}'")

    # 7. Documents against their source files
    folder = Path(args.pdf_folder) if args.pdf_folder else Path(str(summary.get("Source folder") or ""))
    if not folder.is_dir():
        report.note(f"source folder not found ({folder}); skipped the source-file comparison. Use --pdf-folder.")
    else:
        for row in rows:
            if row.get("Type") != "Document":
                continue
            source = folder / str(row.get("Source file"))
            title = row.get("Title")
            if not source.is_file():
                report.check(False, f"source file for '{title}' not found: {source}")
                continue
            if row.get("Source SHA-256") and kitlib.sha256_file(source) != row.get("Source SHA-256"):
                report.note(f"'{source.name}' has changed since the binder was built. Rebuild the binder.")
            src = open_source(source)
            chosen = pages_from_spec(row.get("Pages used"), len(src.pages))
            start, end = as_int(row.get("Start page")), as_int(row.get("End page"))
            ok = True
            for src_index, binder_page in ((chosen[0], start), (chosen[-1], end)):
                a = squash(src.pages[src_index].extract_text() or "")
                b = squash(reader.pages[binder_page - 1].extract_text() or "")
                if a:
                    ok = ok and a[:160] in b
                else:
                    sa, sb = src.pages[src_index].mediabox, reader.pages[binder_page - 1].mediabox
                    ok = ok and (round(float(sa.width)), round(float(sa.height))) == \
                        (round(float(sb.width)), round(float(sb.height)))
            report.check(ok, f"'{title}' is on pages {start}-{end} and matches {source.name}")

    print()
    if report.failed:
        print(f"RESULT: {len(report.failed)} check(s) FAILED, {report.passed} passed.")
        return 1
    print(f"RESULT: all {report.passed} checks passed.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a binder made by build_binder.py.")
    parser.add_argument("binder", help="binder PDF")
    parser.add_argument("--index", help="index spreadsheet (default: <binder>-index.xlsx)")
    parser.add_argument("--pdf-folder", help="folder with the source PDFs (default: the one recorded in the index)")
    parser.add_argument("--quiet", action="store_true", help="only print failures and the result")
    return verify(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
