#!/usr/bin/env python3
"""Turn a PDF of half-size pages (A5 or half Letter) into a print-ready booklet.

Each output page is one side of a sheet with two pages side by side, in the
order needed to fold the printout into a booklet:

  4 pages -> sheet 1 front: [4 | 1], back: [2 | 3]

Print double-sided, "flip on short edge", at 100% size, then fold in half.
Blank pages are added at the end if the page count is not a multiple of 4.

Example
  python scripts/make_booklet.py service-bulletin.pdf
  (writes service-bulletin-print-booklet.pdf next to it)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pymupdf as fitz  # type: ignore
except ImportError:  # pragma: no cover
    import fitz  # type: ignore


def booklet_order(page_count: int) -> list[tuple[int | None, int | None]]:
    """(left, right) page indexes for each printed side; None means blank."""
    total = page_count + (-page_count) % 4
    pages: list[int | None] = list(range(page_count)) + [None] * (total - page_count)
    sides = []
    for sheet in range(total // 4):
        sides.append((pages[total - 1 - 2 * sheet], pages[2 * sheet]))      # front
        sides.append((pages[2 * sheet + 1], pages[total - 2 - 2 * sheet]))  # back
    return sides


def make_booklet(source: Path, target: Path) -> int:
    with fitz.open(source) as doc:
        if doc.page_count == 0:
            raise ValueError("The PDF has no pages.")
        width, height = doc[0].rect.width, doc[0].rect.height
        out = fitz.open()
        for left, right in booklet_order(doc.page_count):
            side = out.new_page(width=2 * width, height=height)
            if left is not None:
                side.show_pdf_page(fitz.Rect(0, 0, width, height), doc, left)
            if right is not None:
                side.show_pdf_page(fitz.Rect(width, 0, 2 * width, height), doc, right)
        out.set_metadata({"title": f"{source.stem} (print-ready booklet)",
                          "creator": "Publisher Rescue kit"})
        out.save(target, garbage=3, deflate=True)
        sides = out.page_count
        out.close()
    return sides


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Make a print-ready booklet PDF from a "
                                     "PDF of A5 or half-Letter pages.")
    parser.add_argument("pdf", type=Path, help="PDF with the pages in reading order")
    parser.add_argument("-o", "--output", type=Path,
                        help="output file (default: <name>-print-booklet.pdf)")
    args = parser.parse_args(argv)
    source = args.pdf.expanduser().resolve()
    if not source.exists():
        print(f"Not found: {source}", file=sys.stderr)
        return 2
    target = args.output or source.with_name(source.stem + "-print-booklet.pdf")
    sides = make_booklet(source, target)
    print(f"Saved {target} ({sides} printed sides, {sides // 2} sheet(s)).")
    print("Print double-sided, flip on short edge, actual size (100%), then fold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
