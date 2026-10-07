#!/usr/bin/env python3
"""
Check an XLSForm (for KoboToolbox or ODK) and explain any problems in plain English.

It runs three layers of checks:
  1. Quick checks of the spreadsheet itself (names, choice lists, ${references},
     REDCap habits such as [field] or <> that do not work in XLSForm, curly quotes).
  2. pyxform, the official converter used by KoboToolbox and ODK.
  3. ODK Validate, which tests every expression (needs Java; skipped if missing).

Optionally it saves the converted XForm XML (--xml), the file ODK Central and
other tools load.

Usage (from the kit folder):
    python scripts/check_xlsform.py samples/03_xlsform/lakeside_health_check.xlsx
    python scripts/check_xlsform.py my_form.xlsx --xml my_form.xml --report my_form_check.txt

Exit code: 0 = no errors, 1 = errors (or warnings with --strict), 2 = file could not be read.
Needs: pip install pyxform openpyxl
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xlsform_reader as xr  # noqa: E402

XML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
CURLY = re.compile("[\u2018\u2019\u201c\u201d]")
REQUIRED_WORDS = {"", "yes", "no", "true", "false", "true()", "false()", "1", "0"}


@dataclass
class Issue:
    level: str       # ERROR, WARNING, NOTE
    where: str       # e.g. "survey row 12"
    message: str
    fix: str = ""


class Linter:
    def __init__(self, form: xr.XLSForm):
        self.form = form
        self.issues: list[Issue] = []

    def add(self, level, where, message, fix=""):
        self.issues.append(Issue(level, where, message, fix))

    def run(self):
        form = self.form
        if "survey" not in form.sheets:
            self.add("ERROR", "workbook", "There is no sheet called 'survey'.",
                     "An XLSForm needs a sheet named survey (and usually choices and settings).")
            return
        header = form.sheets["survey"].header
        if "type" not in header or "name" not in header:
            self.add("ERROR", "survey sheet", "The survey sheet needs columns called 'type' and 'name'.",
                     "Check the first row of the survey sheet.")
            return
        if not any(h == "label" or h.startswith("label::") for h in header):
            self.add("ERROR", "survey sheet", "The survey sheet has no 'label' column.",
                     "Add a label column (or label::English (en) for each language).")
        self.check_languages()
        names = self.check_survey()
        self.check_choices(names)
        self.check_settings()

    def check_languages(self):
        langs = self.form.languages
        survey_header = self.form.sheets["survey"].header
        if langs and "label" in survey_header:
            self.add("WARNING", "survey sheet", "The form mixes a plain 'label' column with language columns "
                     f"({', '.join('label::' + lang for lang in langs)}).",
                     "Use language columns only, so every language shows the right text.")
        if len(langs) > 1:
            for row in self.form.survey:
                kind, _ = xr.base_type(row.get("type", ""))
                if kind in xr.NO_LABEL_TYPES or not any(row.get(f"label::{lang}") for lang in langs):
                    continue
                missing = [lang for lang in langs if not row.get(f"label::{lang}")]
                if missing:
                    self.add("WARNING", f"survey row {row['_row']}", f"'{row.get('name', '')}' has no label in "
                             f"{', '.join(missing)}.", "Add the translation (from the client's approved version).")

    def check_survey(self) -> dict:
        names: dict = {}
        lists = self.form.choice_lists()
        stack = []
        for row in self.form.survey:
            where = f"survey row {row['_row']}"
            type_text = row.get("type", "")
            name = row.get("name", "")
            kind, list_name = xr.base_type(type_text)
            if not type_text:
                if any(v for k, v in row.items() if not k.startswith("_")):
                    self.add("ERROR", where, "This row has text but no type.", "Fill in the type column, or delete the row.")
                continue
            if kind not in xr.QUESTION_TYPES:
                close = difflib.get_close_matches(kind, sorted(xr.QUESTION_TYPES), n=1)
                self.add("ERROR", where, f"Unknown question type '{type_text}'.",
                         (f"Did you mean '{close[0]}'? " if close else "") + "See xlsform.org for the list of types.")
            if kind in ("begin_group", "begin_repeat"):
                stack.append((kind, name, row["_row"]))
            elif kind in ("end_group", "end_repeat"):
                wanted = "begin_group" if kind == "end_group" else "begin_repeat"
                if not stack:
                    self.add("ERROR", where, f"'{type_text}' has no matching '{wanted}' above it.",
                             "Delete this row or add the missing begin row.")
                else:
                    opened = stack.pop()
                    if opened[0] != wanted:
                        self.add("ERROR", where, f"'{type_text}' closes the {opened[0].split('_')[1]} '{opened[1]}' "
                                 f"opened on row {opened[2]}.", "Groups and repeats must be closed in reverse order.")
                continue
            if not name:
                self.add("ERROR", where, f"A '{type_text}' row needs a name.", "Add a short name such as q1_age.")
                continue
            if not XML_NAME.match(name):
                self.add("ERROR", where, f"Name '{name}' is not allowed.",
                         "Names start with a letter or underscore and use only letters, numbers, _ - and .; no spaces.")
            elif len(name) > 32:
                self.add("NOTE", where, f"Name '{name}' is {len(name)} characters; some export tools cut names at 32.",
                         "Shorter names are easier to analyse.")
            if name in names:
                self.add("WARNING", where, f"Name '{name}' is also used on survey row {names[name]['_row']}.",
                         "Give each question its own name; ${...} references become ambiguous otherwise.")
            else:
                names[name] = row
            label = any(v for k, v in row.items() if (k == "label" or k.startswith("label::")) and v)
            hint = any(v for k, v in row.items() if (k == "hint" or k.startswith("hint::")) and v)
            if kind not in xr.NO_LABEL_TYPES and kind not in ("begin_group", "begin_repeat") and not (label or hint):
                self.add("ERROR", where, f"'{name}' has no label, so people would see an empty question.",
                         "Add the question text in the label column.")
            if kind in ("select_one", "select_multiple", "rank") and list_name:
                if " " in list_name.strip() and "or_other" not in list_name:
                    self.add("ERROR", where, f"Choice list name '{list_name}' has a space.", "Use underscores.")
                elif list_name.replace(" or_other", "") not in lists:
                    close = difflib.get_close_matches(list_name, list(lists), n=1)
                    self.add("ERROR", where, f"'{name}' uses the choice list '{list_name}', which is not on the choices sheet.",
                             (f"Did you mean '{close[0]}'? " if close else "") + "Add the list to the choices sheet.")
            elif kind in ("select_one", "select_multiple", "rank") and not list_name:
                self.add("ERROR", where, f"'{type_text}' needs a choice list name, e.g. select_one yesno.", "")
            if kind == "calculate" and not row.get("calculation"):
                self.add("ERROR", where, f"Calculate row '{name}' has no formula in the calculation column.", "")
            if kind == "range":
                params = row.get("parameters", "")
                for key in ("start", "end", "step"):
                    match = re.search(rf"{key}\s*=\s*(-?[\d.]+)", params)
                    if params and not match:
                        self.add("WARNING", where, f"Range '{name}' has no {key}= value in parameters.",
                                 "e.g. start=0 end=10 step=1")
            required = row.get("required", "").strip()
            if required.lower() not in REQUIRED_WORDS and "${" not in required and "(" not in required:
                self.add("WARNING", where, f"Required is '{required}'. Use yes, or an expression.",
                         "Anything else is read as an expression and may silently mean 'not required'.")
            if required.lower() in ("yes", "true", "true()", "1") and kind in {"note", "calculate", "begin_group",
                                                                             "begin_repeat"} | xr.METADATA_TYPES:
                self.add("WARNING", where, f"'{name}' is a {kind} row and cannot be required.", "Clear the required column.")
            if row.get("constraint") and not any(row.get(k) for k in row if k == "constraint_message"
                                                  or k.startswith("constraint_message::")):
                self.add("NOTE", where, f"'{name}' has a constraint but no constraint_message.",
                         "Add a message that tells the person what to enter, e.g. 'Enter a number from 0 to 7.'")
            for column in xr.EXPRESSION_COLUMNS:
                self.check_expression(where, name, column, row.get(column, ""))
        for opened in stack:
            self.add("ERROR", f"survey row {opened[2]}", f"The {opened[0].split('_')[1]} '{opened[1]}' is never closed.",
                     f"Add an end_{opened[0].split('_')[1]} row.")
        all_names = set(names)
        for row in self.form.survey:
            where = f"survey row {row['_row']}"
            texts = [(c, row.get(c, "")) for c in xr.EXPRESSION_COLUMNS]
            texts += [(k, v) for k, v in row.items() if k.split("::")[0] in ("label", "hint", "constraint_message")]
            for column, text in texts:
                for ref in xr.references(text):
                    if ref not in all_names:
                        close = difflib.get_close_matches(ref, list(all_names), n=1)
                        self.add("ERROR", where, f"The {column.split('::')[0]} of '{row.get('name', '')}' refers to "
                                 f"${{{ref}}}, which is not a question name.",
                                 f"Did you mean ${{{close[0]}}}?" if close else "Check the spelling.")
        return names

    def check_expression(self, where, name, column, text):
        if not text:
            return
        if CURLY.search(text):
            self.add("ERROR", where, f"The {column} of '{name}' has curly quotes (usually pasted from Word): {text}",
                     "Retype the quotes as straight ' quotes. Curly quotes pass the converter but never match.")
        if re.search(r"(?<![!<>=])==(?!=)", text):
            self.add("ERROR", where, f"The {column} of '{name}' uses '=='. XLSForm uses a single '='.", f"{text}")
        if "<>" in text:
            self.add("ERROR", where, f"The {column} of '{name}' uses '<>' (REDCap style). XLSForm uses '!='.",
                     text.replace("<>", "!="))
        if re.search(r"(^|[\s(])\[[a-z][a-z0-9_]*(\([^)]*\))?\]", text):
            self.add("ERROR", where, f"The {column} of '{name}' uses REDCap-style [field] references.",
                     "Write ${field} instead, e.g. ${age} > 17; for a ticked checkbox use selected(${field}, '2').")
        if re.search(r"\s(AND|OR)\s", text):
            self.add("ERROR", where, f"The {column} of '{name}' uses AND/OR in capitals. XLSForm needs lowercase.",
                     "Write and / or in lowercase.")
        if text.count("(") != text.count(")"):
            self.add("ERROR", where, f"The {column} of '{name}' has {text.count('(')} '(' but {text.count(')')} ')'.",
                     "Balance the brackets.")
        if text.count("'") % 2 == 1:
            self.add("ERROR", where, f"The {column} of '{name}' has an odd number of ' quotes.", "Close every quote.")

    def check_choices(self, survey_names):
        lists = self.form.choice_lists()
        if not self.form.choices and "choices" not in self.form.sheets:
            if any(xr.base_type(r.get("type", ""))[0] in ("select_one", "select_multiple", "rank") for r in self.form.survey):
                self.add("ERROR", "workbook", "The form has select questions but no 'choices' sheet.", "Add a choices sheet.")
            return
        used = {}
        for row in self.form.survey:
            kind, list_name = xr.base_type(row.get("type", ""))
            if kind in ("select_one", "select_multiple", "rank") and list_name:
                used.setdefault(list_name.replace(" or_other", ""), set()).add(kind)
        allow_duplicates = self.form.settings.get("allow_choice_duplicates", "").lower() in ("yes", "true")
        for list_name, rows in lists.items():
            if not XML_NAME.match(list_name):
                self.add("ERROR", f"choices row {rows[0]['_row']}", f"Choice list name '{list_name}' is not allowed.",
                         "Use letters, numbers and underscores.")
            seen = {}
            for row in rows:
                where = f"choices row {row['_row']}"
                choice = row.get("name", "")
                if choice == "":
                    self.add("ERROR", where, f"A choice in list '{list_name}' has no name (the stored code).",
                             "Fill in the name column, e.g. 1.")
                    continue
                if choice in seen and not allow_duplicates:
                    self.add("ERROR", where, f"Choice '{choice}' appears twice in list '{list_name}' "
                             f"(also row {seen[choice]}).", "Each choice name must be unique within its list.")
                seen.setdefault(choice, row["_row"])
                if " " in choice and "select_multiple" in used.get(list_name, set()):
                    self.add("ERROR", where, f"Choice '{choice}' has a space but list '{list_name}' is used by a "
                             "select_multiple question.", "Remove the spaces, e.g. use underscores.")
                if not self.form.text(row, "label"):
                    self.add("ERROR", where, f"Choice '{choice}' in list '{list_name}' has no label.", "Add the answer text.")
            for text in [r.get("name", "") for r in rows]:
                if CURLY.search(text):
                    self.add("ERROR", f"choices row {rows[0]['_row']}", f"Choice name '{text}' has curly quotes.", "")
        for list_name in lists:
            if list_name not in used:
                self.add("NOTE", f"choices row {lists[list_name][0]['_row']}",
                         f"Choice list '{list_name}' is not used by any question.", "Delete it if it is not needed.")

    def check_settings(self):
        settings = self.form.settings
        if "settings" not in self.form.sheets:
            self.add("NOTE", "workbook", "There is no settings sheet.",
                     "Add one with form_title, form_id and version so updates are tracked.")
            return
        for key, advice in (("form_title", "the title people see"), ("form_id", "a short unique id"),
                            ("version", "e.g. a date like 2026100701; change it for every update")):
            if not settings.get(key):
                self.add("NOTE", "settings sheet", f"No {key} set ({advice}).", "")
        default = settings.get("default_language", "")
        if default and self.form.languages and default not in self.form.languages:
            self.add("WARNING", "settings sheet", f"default_language is '{default}' but the label columns are for: "
                     f"{', '.join(self.form.languages)}.", "Make default_language match one label::language column exactly.")


# ---------------------------------------------------------------------------
# pyxform and ODK Validate
# ---------------------------------------------------------------------------

EXPLANATIONS = [
    (r"List name not in choices sheet: (\S+)",
     "A question uses the choice list '{0}', which is not on the choices sheet.",
     "Add the list to the choices sheet, or fix the spelling in the type column."),
    (r"Unknown question type '([^']*)'",
     "'{0}' is not a question type XLSForm knows.", "Check the spelling against xlsform.org."),
    (r"the 'name' value '([^']*)' is invalid\. Questions, groups, and repeats must be unique",
     "Two questions in the same group are both called '{0}'.", "Rename one of them."),
    (r"Could not find the name '([^']*)'",
     "An expression refers to ${{{0}}}, but no question has that name.", "Fix the name inside ${...}."),
    (r"Names must begin with a letter or underscore",
     "A name has a space or a character that is not allowed.",
     "Use letters, numbers, _ - and . only, starting with a letter."),
    (r"survey element named '([^']*)' has no label or hint",
     "Question '{0}' has no label, so it would show up empty.", "Add the question text."),
    (r"Unmatched 'begin_(group|repeat)'",
     "A {0} is opened but never closed.", "Add an end_{0} row in the right place."),
    (r"Unmatched 'end_(group|repeat)'",
     "There is an end_{0} without a matching begin_{0}.", "Delete it or add the missing begin row."),
    (r"Missing calculation",
     "A calculate row has no formula.", "Put the formula in the calculation column."),
    (r"Choice names must be unique", "A choice list has the same name (code) twice.",
     "Give every choice in a list its own name."),
    (r"Choice names with spaces cannot be added to multiple choice selects",
     "A select_multiple list has a choice name with a space.", "Remove the spaces (use underscores)."),
    (r"invalid (\w+) expression \[([^\]]*)\]",
     "The {0} expression '{1}' cannot be read.", "Check brackets, quotes and operators."),
    (r"problem with display condition for node \[\$\{(\w+)\}\]",
     "The relevant (display condition) of '{0}' cannot be read.", "Check brackets, quotes and operators."),
    (r"cannot handle function '([^']*)'",
     "The function {0}() does not exist in ODK.", "Check the spelling against the ODK form operators and functions list."),
    (r"Cycle detected|cyclic", "Some calculations or conditions depend on each other in a circle.",
     "Make sure no question depends (directly or indirectly) on itself."),
]


def clean_message(text: str) -> str:
    keep = []
    for line in str(text).splitlines():
        line = line.rstrip()
        if not line or "JAVA_TOOL_OPTIONS" in line or "_JAVA_OPTIONS" in line:
            continue
        if line.lstrip().startswith(("at ", "Caused by", "...", "The following files failed", "Result:")):
            continue
        if re.fullmatch(r"\s*\$\{tmp\w*\}\s*", line):
            continue
        line = re.sub(r"\s*Bad node: org\.javarosa\S*", "", line)
        keep.append(line.strip())
    return "\n".join(dict.fromkeys(keep))


def explain(message: str) -> tuple[str, str]:
    for pattern, meaning, fix in EXPLANATIONS:
        match = re.search(pattern, message)
        if match:
            return meaning.format(*match.groups()), fix
    return "", ""


def run_pyxform(path: Path, use_odk: bool):
    """Returns (xform_xml or None, list of Issue, odk_ran)."""
    issues = []
    try:
        from pyxform.xls2xform import convert
        from pyxform.errors import PyXFormError
        from pyxform.validators.odk_validate import ODKValidateError
    except ImportError:
        issues.append(Issue("ERROR", "setup", "pyxform is not installed.", "Run: pip install pyxform"))
        return None, issues, False
    odk = use_odk and shutil.which("java") is not None
    if use_odk and not odk:
        issues.append(Issue("NOTE", "setup", "Java was not found, so ODK Validate (the deeper expression "
                            "check) was skipped.", "Install Java 8 or newer to run it."))
    warnings: list[str] = []
    try:
        result = convert(xlsform=str(path), validate=odk, pretty_print=True, warnings=warnings)
    except (PyXFormError, ODKValidateError, ValueError, KeyError) as exc:
        message = clean_message(exc)
        source = "ODK Validate" if isinstance(exc, ODKValidateError) else "pyxform"
        meaning, fix = explain(message)
        text = f"{source} stopped with this error:\n      {message.replace(chr(10), chr(10) + '      ')}"
        if meaning:
            text += f"\n    In plain English: {meaning}"
        issues.append(Issue("ERROR", source, text, fix))
        return None, issues, odk
    for warning in result.warnings:
        message = clean_message(warning)
        if not message or message.strip() in ("ODK Validate Warnings:",):
            continue
        meaning, fix = explain(message)
        issues.append(Issue("WARNING", "pyxform" if "ODK" not in message else "ODK Validate",
                            message + (f"\n    In plain English: {meaning}" if meaning else ""), fix))
    return result, issues, odk


def summary_lines(form: xr.XLSForm) -> list[str]:
    counts = Counter()
    required = relevant = constraints = calculations = 0
    for row in form.survey:
        kind, _ = xr.base_type(row.get("type", ""))
        if kind in ("end_group", "end_repeat"):
            continue
        counts[kind] += 1
        required += row.get("required", "").lower() in ("yes", "true", "true()")
        relevant += bool(row.get("relevant"))
        constraints += bool(row.get("constraint"))
        calculations += bool(row.get("calculation"))
    questions = sum(n for k, n in counts.items() if k not in xr.METADATA_TYPES | {"begin_group", "begin_repeat", "calculate", "note"})
    lines = ["Summary", "-------"]
    lines.append(f"Questions:        {questions} (plus {counts['note']} notes, {counts['calculate']} calculations)")
    lines.append(f"Groups / repeats: {counts['begin_group']} / {counts['begin_repeat']}")
    lines.append("Question types:   " + ", ".join(f"{k} {n}" for k, n in counts.most_common()
                                                  if k not in ("begin_group", "begin_repeat")))
    lines.append(f"Required:         {required}")
    lines.append(f"Relevant (skip):  {relevant}")
    lines.append(f"Constraints:      {constraints}")
    lines.append(f"Choice lists:     {len(form.choice_lists())}")
    lines.append("Languages:        " + (", ".join(form.languages) if form.languages else "one (no language columns)"))
    settings = form.settings
    lines.append(f"Form id/version:  {settings.get('form_id', '(not set)')} / {settings.get('version', '(not set)')}")
    lines.append("")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check an XLSForm and explain problems in plain English.")
    parser.add_argument("xlsform", help="the XLSForm .xlsx file")
    parser.add_argument("--xml", help="save the converted XForm XML to this file")
    parser.add_argument("--report", help="also save the report to this text file")
    parser.add_argument("--no-odk-validate", action="store_true", help="skip ODK Validate (Java)")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    parser.add_argument("--no-date", action="store_true", help="leave the date out of the report")
    args = parser.parse_args(argv)

    path = Path(args.xlsform)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2
    if path.suffix.lower() != ".xlsx":
        print("NOTE: the quick checks read .xlsx files only; other formats go straight to pyxform.")
    issues: list[Issue] = []
    form = None
    if path.suffix.lower() == ".xlsx":
        try:
            form = xr.read_xlsform(path)
        except Exception as exc:  # a damaged or non-Excel file
            print(f"ERROR: cannot open {path} as an Excel file: {exc}")
            return 2
        linter = Linter(form)
        linter.run()
        issues += linter.issues
    result, convert_issues, odk_ran = run_pyxform(path, not args.no_odk_validate)
    issues += convert_issues
    if result is not None and args.xml:
        Path(args.xml).write_text(result.xform, encoding="utf-8")
        if result.itemsets:
            (Path(args.xml).parent / "itemsets.csv").write_text(result.itemsets, encoding="utf-8")

    errors = [i for i in issues if i.level == "ERROR"]
    warnings = [i for i in issues if i.level == "WARNING"]
    notes = [i for i in issues if i.level == "NOTE"]
    failed = bool(errors) or (args.strict and bool(warnings))
    lines = ["XLSForm check", "=============", "", f"File:     {path.as_posix()}"]
    if not args.no_date:
        lines.append(f"Checked:  {dt.date.today().isoformat()}")
    try:
        import pyxform
        version = pyxform.__version__
    except Exception:
        version = "not installed"
    lines.append(f"Tools:    pyxform {version}; ODK Validate {'run' if odk_ran else 'not run'}")
    if result is not None:
        lines.append("Convert:  OK - the form converts to an XForm" + (f" (saved to {args.xml})" if args.xml else ""))
    else:
        lines.append("Convert:  FAILED - the form does not convert yet")
    lines += ["", f"RESULT: {'FAILED' if failed else 'PASSED'} - {len(errors)} error(s), {len(warnings)} warning(s), "
              f"{len(notes)} note(s)", ""]
    if form is not None and form.survey:
        lines += summary_lines(form)
    for heading, items in (("Errors - must fix", errors),
                           ("Warnings - fix, or confirm they are intended", warnings),
                           ("Notes - good to know", notes)):
        lines += [heading, "-" * len(heading)]
        if not items:
            lines += ["  None.", ""]
            continue
        for issue in items:
            lines.append(f"* {issue.where}")
            lines.append(f"    {issue.message}")
            if issue.fix:
                lines.append(f"    {'Tip' if issue.level == 'NOTE' else 'Fix'}: {issue.fix}")
        lines.append("")
    lines.append("Rows are spreadsheet rows (the header is row 1).")
    lines.append("Passing these checks is not the same as testing: preview the form in KoboToolbox or ODK")
    lines.append("and try every path before collecting data.")
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Report saved to {args.report}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
