#!/usr/bin/env python3
"""Check how Word, PowerPoint or LibreOffice files look after you edit them.

Converts each file to PDF with LibreOffice, saves every page as a PNG picture,
and lists the fonts that were used, so you can spot missing fonts and text
that spills onto an extra page before the client does.

Examples
  python scripts/check_render.py templates/newsletter-two-column-A4.docx
  python scripts/check_render.py ~/jobs/stmarys/templates --out ~/jobs/stmarys/render-check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from office_tools import (  # noqa: E402
    MODULE_BY_EXT,
    OfficeToolsError,
    Soffice,
    read_pdf,
    render_all_pages,
)

# Free fonts with exactly the same letter widths as common Microsoft fonts.
# If you see these, the layout matches what the client will see in Office.
SAME_SIZE_AS = {
    "Carlito": "Calibri",
    "Caladea": "Cambria",
    "LiberationSans": "Arial",
    "LiberationSerif": "Times New Roman",
    "LiberationMono": "Courier New",
}
FALLBACK_FONTS = ("DejaVu", "FreeSans", "FreeSerif", "Noto")


def describe_fonts(fonts: list[str]) -> tuple[list[str], list[str]]:
    notes, warnings = [], []
    for font in fonts:
        family = font.split("-")[0].replace(" ", "")
        if family in SAME_SIZE_AS:
            notes.append(f"{font} (same size as {SAME_SIZE_AS[family]})")
        elif family.startswith(FALLBACK_FONTS) and family not in ("OpenSymbol",):
            warnings.append(font)
            notes.append(f"{font} (a stand-in: the font asked for is not installed here)")
        else:
            notes.append(font)
    return notes, warnings


def collect(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files += sorted(p for p in path.rglob("*")
                            if p.suffix.lower().lstrip(".") in MODULE_BY_EXT
                            and not p.name.startswith(("~$", ".~lock")))
        elif path.exists():
            files.append(path)
        else:
            print(f"Not found: {path}", file=sys.stderr)
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert office files to PDF and page "
                                     "pictures so you can check the layout.")
    parser.add_argument("paths", nargs="+", type=Path, help="files or folders to check")
    parser.add_argument("--out", type=Path, default=Path("render-check"),
                        help="folder for the PDFs and pictures (default: ./render-check)")
    parser.add_argument("--width", type=int, default=1000,
                        help="width of the page pictures in pixels (default 1000)")
    parser.add_argument("--expect-pages", type=int,
                        help="warn if a file does not have exactly this many pages")
    args = parser.parse_args(argv)

    files = collect([p.expanduser() for p in args.paths])
    if not files:
        print("Nothing to check.")
        return 1
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    problems = 0
    try:
        lo = Soffice()
    except OfficeToolsError as error:
        print(error, file=sys.stderr)
        return 2
    with lo:
        for path in files:
            pdf = out / (path.stem + ".pdf")
            result = lo.convert(path, pdf)
            if not result.ok:
                problems += 1
                print(f"FAILED  {path.name}: {result.message}")
                continue
            info = read_pdf(pdf)
            pictures = render_all_pages(pdf, out / path.stem, args.width)
            notes, warnings = describe_fonts(info.fonts)
            print(f"OK      {path.name}: {info.pages} page(s) -> {pdf}")
            print(f"        pictures: {pictures[0].parent}")
            print(f"        fonts: {', '.join(notes) or 'none'}")
            if warnings:
                problems += 1
                print("        CHECK: some text used a stand-in font, so line breaks may "
                      "differ on the client's computer. (If only tick boxes or symbols "
                      "use it, you can ignore this.)")
            if args.expect_pages and info.pages != args.expect_pages:
                problems += 1
                print(f"        CHECK: expected {args.expect_pages} pages, found {info.pages}.")
    print(f"\n{len(files)} file(s) checked, {problems} thing(s) to look at. "
          f"Open the PNG pictures in {out} to see each page.")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
