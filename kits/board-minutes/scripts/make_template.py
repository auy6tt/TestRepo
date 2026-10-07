#!/usr/bin/env python3
"""Write the kit's generic minutes template (.docx with placeholders).

The template has the same layout build_minutes.py uses when you don't give it a
client template. Open it in Word to change fonts, colours or the logo (edit the
"Minutes ..." styles), save it, and pass it to build_minutes.py with --template.

Examples:
  python make_template.py                       # writes ../templates/minutes-template.docx
  python make_template.py --locale en-GB -o minutes-template-a4.docx
  python make_template.py --no-appendix -o short-template.docx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from minutes_common import KIT_DIR
from minutes_docx import build_house_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write the kit's generic minutes template (.docx with {{placeholders}}).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:" + __doc__.split("Examples:", 1)[1],
    )
    parser.add_argument("-o", "--output", default=str(KIT_DIR / "templates" / "minutes-template.docx"),
                        help="where to save the template (default: templates/minutes-template.docx)")
    parser.add_argument("--locale", choices=["en-US", "en-GB"], default="en-US",
                        help="en-US: US Letter paper; en-GB: A4 paper (default en-US)")
    parser.add_argument("--no-appendix", action="store_true", help="leave out the action items and motions appendices")
    args = parser.parse_args(argv)

    doc = build_house_template(args.locale, appendices=not args.no_appendix)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
