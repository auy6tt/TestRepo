#!/usr/bin/env python3
"""Turn a Markdown file into a tidy Word document.

  python md2docx.py notes.md notes.docx --footer "Example Consulting | Not legal advice"

Handles the Markdown used in this kit: headings, paragraphs, lists, check
boxes, tables, quotes, code blocks, bold, italic and links.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", help="input .md file")
    ap.add_argument("docx", nargs="?", help="output .docx file (default: same name)")
    ap.add_argument("--footer", help="text for the page footer")
    args = ap.parse_args()
    src = Path(args.markdown)
    out = Path(args.docx) if args.docx else src.with_suffix(".docx")
    K.md_to_docx(src.read_text(encoding="utf-8"), out, footer=args.footer)
    K.info(f"Wrote {out}")


if __name__ == "__main__":
    main()
