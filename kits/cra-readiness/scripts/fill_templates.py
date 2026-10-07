#!/usr/bin/env python3
"""Fill the kit's document templates with one client's details.

Writes each document as Markdown (.md) and Word (.docx).

  python fill_templates.py --client client.json --out clients/acme/2026-10
  python fill_templates.py --client client.json --out clients/acme/2026-10 --only policy,runbook
  python fill_templates.py --blank --out ../templates     # rebuild the blank .docx templates

Documents: policy, runbook, support, handover (filled from client.json) and
intake (the client questionnaire, no client details needed).

Anything missing from client.json shows up as [TO FILL: name] and is listed at
the end, so you can fix client.json and run the script again.
Notes for you inside templates (<!-- ... -->) are removed from the output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402

DOCUMENTS = {
    "policy": ("vulnerability-handling-policy.md", "Vulnerability handling and disclosure policy"),
    "runbook": ("reporting-runbook.md", "Vulnerability and incident reporting runbook"),
    "support": ("support-period-statement.md", "Support period statement"),
    "handover": ("handover-note.md", "Handover note"),
    "intake": ("client-intake-questionnaire.md", "Client intake questionnaire"),
}
BLANK_DOCS = ["policy", "runbook", "support", "intake"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def monthyear(value) -> str:
    """'2031-03' -> 'March 2031'."""
    m = re.match(r"^(\d{4})-(\d{2})", str(value or ""))
    if not m:
        return str(value or "")
    return f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


def longdate(value) -> str:
    """'2026-10-15' -> '15 October 2026'."""
    try:
        d = dt.date.fromisoformat(str(value))
    except ValueError:
        return str(value or "")
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


LANGUAGES = {"bg": "Bulgarian", "cs": "Czech", "da": "Danish", "de": "German", "el": "Greek", "en": "English",
             "es": "Spanish", "et": "Estonian", "fi": "Finnish", "fr": "French", "ga": "Irish", "hr": "Croatian",
             "hu": "Hungarian", "it": "Italian", "lt": "Lithuanian", "lv": "Latvian", "mt": "Maltese", "nl": "Dutch",
             "pl": "Polish", "pt": "Portuguese", "ro": "Romanian", "sk": "Slovak", "sl": "Slovenian", "sv": "Swedish"}


def langnames(codes) -> str:
    """['en', 'nl'] -> 'English and Dutch'."""
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",") if c.strip()]
    names = [LANGUAGES.get(str(c).lower().split("-")[0], str(c)) for c in codes or []]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def make_env(missing: set):
    from jinja2 import ChainableUndefined, Environment, FileSystemLoader

    class Missing(ChainableUndefined):
        """Shows [TO FILL: name] instead of failing, and remembers what was missing."""

        def __str__(self):
            name = self._undefined_name or "value"
            missing.add(name)
            return f"[TO FILL: {name}]"

        def __iter__(self):
            return iter(())

        def __bool__(self):
            return False

    env = Environment(loader=FileSystemLoader(str(K.TEMPLATES_DIR)), undefined=Missing,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True, autoescape=False)
    env.filters["monthyear"] = monthyear
    env.filters["longdate"] = longdate
    env.filters["langnames"] = langnames
    return env


def tidy(text: str, keep_notes: bool) -> str:
    if not keep_notes:
        text = re.sub(r"<!--.*?-->\n?", "", text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def leftovers(text: str) -> list[str]:
    found = re.findall(r"\[TO FILL: [^\]]+\]", text)
    found += [m for m in re.findall(r"\[[A-Z][^\]\n]{2,80}\](?!\()", text) if not m.startswith("[TO FILL")]
    return sorted(set(found))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", help="client.json")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--only", help="comma-separated list: " + ", ".join(DOCUMENTS))
    ap.add_argument("--blank", action="store_true",
                    help="use templates/client.example.json and write only .docx (for the blank templates)")
    ap.add_argument("--keep-notes", action="store_true", help="keep <!-- notes --> in the output")
    ap.add_argument("--no-docx", action="store_true", help="write Markdown only")
    args = ap.parse_args()

    if args.blank:
        client = K.load_json(K.TEMPLATES_DIR / "client.example.json")
        wanted = BLANK_DOCS
    else:
        if not args.client:
            K.fail("Give --client client.json (or --blank).")
        client = K.load_json(args.client)
        wanted = list(DOCUMENTS)
    if args.only:
        wanted = [w.strip() for w in args.only.split(",") if w.strip()]
        unknown = [w for w in wanted if w not in DOCUMENTS]
        if unknown:
            K.fail(f"Unknown document(s): {', '.join(unknown)}. Choose from {', '.join(DOCUMENTS)}.")

    missing: set = set()
    env = make_env(missing)
    context = dict(client)
    context["today"] = K.today()
    company = K.dig(client, "company.legal_name") or "[Company]"
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    problems = {}
    for key in wanted:
        filename, title = DOCUMENTS[key]
        text = tidy(env.get_template(filename).render(**context), args.keep_notes)
        if not args.blank:
            K.write_text(out_dir / filename, text)
            left = leftovers(text)
            if left:
                problems[filename] = left
        if not args.no_docx:
            if key == "handover":
                footer = f"Prepared by {K.dig(client, 'engagement.consultant_name') or ''}  |  Not legal advice"
            elif key == "intake":
                footer = "Client intake questionnaire  |  Confidential once filled in"
            else:
                version = K.dig(client, "policy.version") if key == "policy" else K.dig(client, f"{key}.version")
                footer = f"{company}  |  {title}" + (f"  |  Version {version}" if version else "")
            docx_path = out_dir / filename.replace(".md", ".docx")
            K.md_to_docx(text, docx_path, footer=footer)
        if args.blank:
            K.info(f"Wrote {key}: {out_dir / filename.replace('.md', '.docx')}")
        else:
            K.info(f"Wrote {key}: {out_dir / filename}" + ("" if args.no_docx else " (+ .docx)"))

    if missing and not args.blank:
        K.warn("These fields are missing from client.json: " + ", ".join(sorted(missing)))
    for filename, items in problems.items():
        K.warn(f"{filename} still contains placeholders: " + "; ".join(items[:8])
               + (" ..." if len(items) > 8 else ""))
    if not args.blank and not missing and not problems:
        K.info("No placeholders left. Read every document once before sending it.")


if __name__ == "__main__":
    main()
