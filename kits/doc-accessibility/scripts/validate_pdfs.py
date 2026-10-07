#!/usr/bin/env python3
"""Run veraPDF's PDF/UA-1 machine checks on PDFs and summarise the results.

veraPDF is a free, open-source PDF validator. It tests the parts of PDF/UA
(the accessibility standard for PDF) that a machine can test: tags present,
title and language set, fonts usable, images with alt text and so on.
Passing these checks does NOT mean a file is accessible: a person still has
to check reading order, alt text quality and tables.

Install veraPDF once with:  bash scripts/setup.sh --verapdf
(or download it from verapdf.org on your own computer).

Outputs in --out: validation.csv and validation.md.

Examples:
  python validate_pdfs.py fixed/ --out fixed/
  python validate_pdfs.py before.pdf after.pdf
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DIR = Path.home() / ".cache" / "doc-accessibility" / "verapdf"
MAIN_CLASS = "org.verapdf.apps.GreenfieldCliWrapper"

# Plain-English labels, matched against veraPDF's rule descriptions (first match wins).
PLAIN_LABELS = [
    ("DisplayDocTitle", "Title bar does not show the document title"),
    ("dc:title", "No title in the file's metadata"),
    ("Metadata key", "No XMP metadata in the file"),
    ("PDF/UA Identification", "Not marked as a PDF/UA file"),
    ("MarkInfo", "Not marked as tagged"),
    ("StructTreeRoot", "No tag structure"),
    ("Artifact or tagged as real content", "Some content is not tagged"),
    ("natural language", "Language not set"),
    ("Lang", "Language not set"),
    ("alternate description", "Images or other content without alt text"),
    ("Alt", "Images or other content without alt text"),
    ("ToUnicode", "Text cannot be reliably read out (font has no Unicode mapping)"),
    ("embedded", "Fonts not embedded"),
    ("font", "Font problem"),
    ("Table", "Table structure problem"),
    ("TH", "Table header problem"),
    ("heading", "Heading structure problem"),
    ("Widget", "Form fields not tagged or named"),
    ("Link", "Links not tagged"),
    ("annotation", "Links, comments or form fields not tagged"),
    ("Tabs", "Tab order not set to follow the structure"),
    ("role map", "Custom tags not mapped to standard tags"),
    ("RoleMap", "Custom tags not mapped to standard tags"),
]


def plain_label(description: str) -> str:
    for needle, label in PLAIN_LABELS:
        if needle.lower() in description.lower():
            return label
    return description[:140]


def find_verapdf(explicit: str | None = None) -> list[str] | None:
    """Return the command that runs veraPDF, or None if it is not installed."""
    places = [explicit, os.environ.get("VERAPDF_DIR"), str(DEFAULT_DIR)]
    java = shutil.which("java")
    for place in places:
        if not place:
            continue
        path = Path(place).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return [str(path)]
        script = path / "verapdf"
        if script.is_file():
            return [str(script)]
        jars = glob.glob(str(path / "lib" / "*.jar")) or glob.glob(str(path / "*.jar"))
        if jars and java:
            lib = path / "lib" if glob.glob(str(path / "lib" / "*.jar")) else path
            return [java, "-cp", str(lib / "*"), MAIN_CLASS]
    found = shutil.which("verapdf")
    return [found] if found else None


def run_verapdf(paths: list[Path], flavour: str = "ua1", command: list[str] | None = None,
                timeout: int = 1800) -> dict:
    """Validate PDFs. Returns {absolute path: result dict}."""
    command = command or find_verapdf()
    if command is None:
        raise RuntimeError("veraPDF is not installed. Run: bash scripts/setup.sh --verapdf")
    targets = [str(Path(p).resolve()) for p in paths]
    process = subprocess.run([*command, "-f", flavour, "--format", "json", "--maxfailuresdisplayed", "3", *targets],
                             capture_output=True, text=True, timeout=timeout)
    start = process.stdout.find("{")
    if start < 0:
        raise RuntimeError(f"veraPDF gave no report. {process.stderr.strip()[-500:]}")
    report = json.loads(process.stdout[start:])
    results = {}
    for job in report.get("report", {}).get("jobs", []):
        name = job.get("itemDetails", {}).get("name", "")
        validation = job.get("validationResult") or []
        if isinstance(validation, dict):
            validation = [validation]
        if not validation:
            error = job.get("taskException") or job.get("taskResult") or "could not be checked"
            results[name] = {"compliant": None, "failed_rules": None, "failed_checks": None, "rules": [],
                             "summary": f"Not checked ({str(error)[:100]})"}
            continue
        first = validation[0]
        details = first.get("details", {})
        rules = []
        for rule in details.get("ruleSummaries", []):
            rules.append({"rule": f"{rule.get('clause')}-{rule.get('testNumber')}",
                          "description": rule.get("description", ""),
                          "plain": plain_label(rule.get("description", "")),
                          "failed_checks": rule.get("failedChecks", 0)})
        compliant = bool(first.get("compliant"))
        failed = details.get("failedRules", len(rules))
        summary = ("Passed all PDF/UA-1 machine checks" if compliant
                   else f"Failed {failed} rule{'s' if failed != 1 else ''} ({details.get('failedChecks', 0)} checks)")
        results[name] = {"compliant": compliant, "failed_rules": failed,
                         "failed_checks": details.get("failedChecks", 0), "rules": rules, "summary": summary}
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run veraPDF PDF/UA-1 machine checks and summarise them.")
    parser.add_argument("inputs", nargs="+", help="PDF files or folders")
    parser.add_argument("--out", help="folder for validation.csv and validation.md")
    parser.add_argument("--verapdf", help="veraPDF folder or launcher (default: $VERAPDF_DIR or ~/.cache/doc-accessibility/verapdf)")
    parser.add_argument("--flavour", default="ua1", help="veraPDF profile: ua1 (default) or ua2")
    args = parser.parse_args(argv)

    files = []
    for item in args.inputs:
        path = Path(item)
        files += sorted(path.rglob("*.pdf")) if path.is_dir() else [path]
    files = [f for f in files if f.is_file()]
    if not files:
        print("No PDF files found.", file=sys.stderr)
        return 1
    command = find_verapdf(args.verapdf)
    if command is None:
        print("veraPDF is not installed. Run: bash scripts/setup.sh --verapdf\n"
              "(On your own computer you can also install it from verapdf.org.)", file=sys.stderr)
        return 2
    results = run_verapdf(files, args.flavour, command)

    lines = [f"# veraPDF results ({args.flavour.upper()})", "",
             f"Checked on {dt.date.today().isoformat()}. These are machine checks only. Passing them does not mean "
             "a file is accessible: a person still checks reading order, alt text and tables.", ""]
    rows = []
    for path in files:
        result = results.get(str(path.resolve()), {"summary": "No result", "rules": [], "compliant": None,
                                                    "failed_rules": None, "failed_checks": None})
        print(f"{path}: {result['summary']}")
        lines += [f"## {path.parent.name}/{path.name}", "", result["summary"], ""]
        problems = []
        for rule in result["rules"]:
            count = f"{rule['failed_checks']} check{'s' if rule['failed_checks'] != 1 else ''}"
            print(f"   - {rule['plain']} (rule {rule['rule']}, {count})")
            lines.append(f"- {rule['plain']} (rule {rule['rule']}, {count}). veraPDF says: {rule['description']}")
            problems.append(rule["plain"])
        lines.append("")
        rows.append([f"{path.parent.name}/{path.name}", "Pass" if result["compliant"] else ("Fail" if result["compliant"] is False else "Not checked"),
                     result["failed_rules"], result["failed_checks"], "; ".join(dict.fromkeys(problems))])
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "validation.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["File", "PDF/UA-1 machine checks", "Rules failed", "Checks failed", "Problems"])
            writer.writerows(rows)
        (out / "validation.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {out / 'validation.csv'} and {out / 'validation.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
