#!/usr/bin/env python3
"""
Check a REDCap data dictionary CSV before it goes to a client.

It looks for the problems that make a REDCap upload fail, or that make a form
behave wrongly after upload: the 18 column headers, variable and form names,
field types, choices ("1, Yes | 0, No"), validation types and min/max values,
branching logic and calculations that point at fields that don't exist,
checkbox and matrix rules, action tags, and fields that look like identifiers
but are not flagged.

Usage (from the kit folder):
    python scripts/validate_redcap.py samples/02_redcap/lakeside_data_dictionary.csv
    python scripts/validate_redcap.py my_dictionary.csv --events instrument_event_mapping.csv \
        --repeating repeating_instruments.csv --report validation_report.txt

Exit code: 0 = no errors, 1 = errors (or warnings when --strict is used),
2 = the file could not be read.

Only needs the Python standard library.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redcap_dictionary as rd  # noqa: E402
import redcap_logic as rl  # noqa: E402

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CODE_RE = re.compile(r"^-?[A-Za-z0-9_]+(\.[0-9]+)?$")
ALIGNMENTS = {"", "LV", "LH", "RV", "RH"}
COLUMN_TITLES = dict(zip("ABCDEFGHIJKLMNOPQR", [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic",
    "Required Field?", "Custom Alignment", "Question Number", "Matrix Group Name",
    "Matrix Ranking?", "Field Annotation"]))
# Words that break REDCap's page code or statistics software when used as variable names.
RESERVED_WORDS = {
    "abstract", "arguments", "await", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "debugger", "default", "delete", "do", "double", "else",
    "enum", "eval", "export", "extends", "false", "final", "finally", "float", "for",
    "function", "goto", "if", "implements", "import", "in", "instanceof", "int",
    "interface", "let", "long", "native", "new", "null", "package", "private", "protected",
    "public", "return", "short", "static", "super", "switch", "synchronized", "this",
    "throw", "throws", "transient", "true", "try", "typeof", "var", "void", "volatile",
    "while", "with", "yield", "event_id", "instance", "hidden_edit_flag", "record",
}
ID_NAME_PATTERNS = [
    r"^(f|l|first|last|full|sur|given|family|maiden|participant|patient|pt|child|mother|"
    r"father|parent|caregiver|carer|guardian|resp|respondent)_?name$",
    r"(^|_)(fname|lname|firstname|lastname|surname|fullname|initials)($|_)",
    r"(^|_)dob($|_)", r"birth", r"phone", r"mobile", r"(^|_)cell($|_)", r"e_?mail",
    r"address", r"street", r"post_?code", r"postal", r"(^|_)zip", r"(^|_)mrn($|_)",
    r"nhs_?(no|num|number)", r"(^|_)ssn($|_)", r"social_?sec", r"passport", r"national_?id",
    r"(^|_)nid($|_)", r"ip_?addr", r"(^|_)gps($|_)", r"latitude", r"longitude",
    r"photo", r"signature",
]
ID_LABEL_PATTERNS = [
    r"\b(first|last|full|family|given|sur|maiden)\s*name\b",
    r"\bname of (the )?(participant|patient|child|respondent|subject|parent|caregiver|carer|"
    r"mother|father|guardian)\b",
    r"\b(participant|patient|child|respondent|subject)'?s? name\b", r"\byour name\b",
    r"\binitials\b", r"\bdate of birth\b", r"\bbirth ?date\b", r"\bphone\b", r"\btelephone\b",
    r"\bmobile (number|no)\b", r"\be-?mail\b", r"\baddress\b", r"\bpost ?code\b",
    r"\bzip ?code\b", r"\bpostal code\b", r"\bmedical record\b", r"\bMRN\b",
    r"\bNHS number\b", r"\bsocial security\b", r"\bpassport\b", r"\bnational (id|identity)\b",
    r"\bGPS\b", r"\bsignature\b", r"\bphoto(graph)?\b",
]
ID_VALIDATIONS = {"email", "phone", "phone_australia", "ssn", "zipcode", "postalcode_australia",
                  "postalcode_canada", "postalcode_french", "postalcode_germany", "mrn_10d",
                  "mrn_generic", "vmrn"}
LOGIC_HELP = ("Field names go in [square brackets], text values in 'quotes', and conditions are "
              "joined with and / or. Example: [sex] = '1' and [age] >= 18")


class Checker:
    def __init__(self, dd: rd.Dictionary, event_map=None, repeating=None):
        self.dd = dd
        self.event_map = event_map
        self.repeating = repeating
        self.issues: list[rd.Issue] = []
        self.field_index = {f.name: i for i, f in reversed(list(enumerate(dd.fields)))}
        self.events_referenced: set[str] = set()
        self.smart_variables: set[str] = set()

    # -- helpers -----------------------------------------------------------
    def add(self, level, f, message, fix="", column="", row=None, field=None):
        self.issues.append(rd.Issue(level, row if row is not None else (f.row if f else None),
                                    field if field is not None else (f.name if f else ""),
                                    message, fix, column))

    def suggest(self, name: str) -> str:
        close = difflib.get_close_matches(name.lower(), list(self.dd.by_name), n=1, cutoff=0.75)
        return f"Did you mean [{close[0]}]?" if close else "Check the spelling, or add the missing field."

    # -- checks ------------------------------------------------------------
    def run(self):
        if not self.dd.fields:
            self.add("ERROR", None, "The dictionary has a header row but no fields.", row=2, field="")
            return
        self.check_names()
        self.check_record_id()
        self.check_forms()
        for f in self.dd.fields:
            self.check_type_and_label(f)
            self.check_choices(f)
            self.check_validation(f)
            self.check_flags(f)
            self.check_annotation(f)
            self.check_piping(f)
            if f.branching:
                self.check_logic(f, f.branching, "branching")
            if f.ftype == "calc" and f.choices_raw:
                self.check_logic(f, f.choices_raw, "calc")
        self.check_matrices()
        self.check_calc_cycles()
        self.check_events()
        self.check_summaries()

    def check_names(self):
        seen = defaultdict(list)
        form_status = {f"{form}_complete" for form in self.dd.forms}
        for f in self.dd.fields:
            name = f.name
            if not name:
                self.add("ERROR", f, "The variable name is empty.", "Give every row a variable name.", "A")
                continue
            seen[name].append(f.row)
            if not NAME_RE.match(name):
                reasons = []
                if name != name.lower():
                    reasons.append("has capital letters")
                if not name[0].isalpha():
                    reasons.append("does not start with a letter")
                if re.search(r"[^A-Za-z0-9_]", name):
                    reasons.append("contains characters other than letters, numbers and underscores")
                better = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")
                if better and not better[0].isalpha():
                    better = "v_" + better
                self.add("ERROR", f, f"Variable name '{name}' {' and '.join(reasons) or 'is not allowed'}.",
                         f"Use lowercase letters, numbers and underscores, starting with a letter, "
                         f"e.g. '{better}'. Then update any logic that uses it.", "A")
            if len(name) > 100:
                self.add("ERROR", f, f"Variable name is {len(name)} characters long (REDCap allows 100).",
                         "Shorten it.", "A")
            elif len(name) > 26:
                self.add("WARNING", f, f"Variable name is {len(name)} characters long. REDCap recommends 26 or "
                         "fewer; Stata and SAS cut names at 32 characters.", "Shorten it.", "A")
            if name.startswith("redcap_"):
                self.add("ERROR", f, "Names starting with 'redcap_' are reserved by REDCap.", "Rename the field.", "A")
            if name in form_status:
                self.add("ERROR", f, f"'{name}' clashes with the status field REDCap adds to the form "
                         f"'{name[:-9]}'.", "Rename the field.", "A")
            if "___" in name:
                self.add("WARNING", f, "The name contains '___' (three underscores), which REDCap uses for "
                         "checkbox columns in exports.", "Use single underscores.", "A")
            if name in RESERVED_WORDS:
                self.add("WARNING", f, f"'{name}' is a reserved word that can break REDCap's page code or "
                         "statistics software.", f"Use a more specific name, e.g. '{name}_1' or a descriptive name.", "A")
            if f.ftype == "checkbox":
                for code, _ in f.choices:
                    column = rd.checkbox_column(name, code)
                    if len(column) > 32:
                        self.add("WARNING", f, f"Export column '{column}' is {len(column)} characters; Stata and "
                                 "SAS cut names at 32.", "Shorten the variable name.", "A")
                        break
        for name, rows in seen.items():
            if len(rows) > 1:
                first = self.dd.by_name[name]
                self.add("ERROR", first, f"Variable name '{name}' is used {len(rows)} times (rows "
                         f"{', '.join(map(str, rows))}).", "Every variable name must be unique in the project.", "A")

    def check_record_id(self):
        first = self.dd.fields[0]
        if first.ftype != "text":
            self.add("ERROR", first, f"The first field ('{first.name}') becomes the record ID, so it must be a "
                     f"text field (it is '{first.ftype}').", "Move the record ID field to the top and make it 'text'.", "D")
        if first.branching:
            self.add("WARNING", first, "The record ID field has branching logic; it must always be shown.",
                     "Remove the branching logic from the first field.", "L")
        if first.matrix:
            self.add("ERROR", first, "The record ID field cannot be part of a matrix.", "Clear its matrix group.", "P")

    def check_forms(self):
        previous, closed = None, set()
        for f in self.dd.fields:
            form = f.form
            if not form:
                self.add("ERROR", f, "The form (instrument) name is empty.", "Fill in column B.", "B")
                continue
            if form != previous:
                if form in closed:
                    self.add("ERROR", f, f"Form '{form}' appears again after another form. All fields of a form "
                             "must be in one block of rows.", "Move this row up next to the other rows of the form.", "B")
                if previous:
                    closed.add(previous)
                previous = form
        for form in self.dd.forms:
            row = self.dd.form_fields(form)[0]
            if not NAME_RE.match(form):
                self.add("ERROR", row, f"Form name '{form}' must use lowercase letters, numbers and "
                         "underscores, starting with a letter.",
                         f"e.g. '{re.sub(r'[^a-z0-9_]+', '_', form.lower()).strip('_')}'", "B", field="")
            if len(form) > 50:
                self.add("WARNING", row, f"Form name '{form}' is long ({len(form)} characters); REDCap may "
                         "shorten it.", "Shorten the form name.", "B", field="")
            data_fields = [x for x in self.dd.form_fields(form) if x.ftype != "descriptive"]
            if not data_fields:
                self.add("WARNING", row, f"Form '{form}' has no fields that store data.", "", "B", field="")

    def check_type_and_label(self, f):
        ftype = f.ftype
        if not ftype:
            self.add("ERROR", f, "The field type is empty.", "Use one of: " + ", ".join(rd.FIELD_TYPES), "D")
        elif ftype not in rd.FIELD_TYPES:
            if ftype.lower() in rd.FIELD_TYPES:
                self.add("ERROR", f, f"Field type '{ftype}' must be lowercase.", f"Write '{ftype.lower()}'.", "D")
            else:
                close = difflib.get_close_matches(ftype.lower(), list(rd.FIELD_TYPES), n=1)
                hint = f"Did you mean '{close[0]}'? " if close else ""
                self.add("ERROR", f, f"Unknown field type '{ftype}'.",
                         hint + "Allowed: " + ", ".join(rd.FIELD_TYPES), "D")
        elif ftype == "sql":
            self.add("WARNING", f, "Dynamic SQL fields can only be added by a REDCap administrator.",
                     "Ask the client's REDCap admin, or use a dropdown instead.", "D")
        if not f.label.strip():
            self.add("ERROR", f, "The field label (the question text) is empty.", "Add the question text.", "E")

    def check_choices(self, f):
        ftype, raw = f.ftype, f.choices_raw
        if ftype in rd.CHOICE_TYPES:
            if not raw:
                self.add("ERROR", f, f"A {ftype} field needs choices.", 'Write them like "1, Yes | 0, No".', "F")
                return
            for problem in f.choice_problems:
                self.add("ERROR", f, f"Choices: {problem}.", 'Write each choice as "code, label" and separate '
                         'choices with " | ", e.g. "1, Yes | 0, No".', "F")
            codes = [c for c, _ in f.choices]
            for code, label in f.choices:
                if code == "":
                    self.add("ERROR", f, f'Choice "{label}" has an empty code.', "Give every choice a code, e.g. 1.", "F")
                elif not CODE_RE.match(code):
                    self.add("ERROR", f, f"Choice code '{code}' contains characters REDCap does not allow.",
                             "Codes should be numbers (best) or letters, numbers and underscores.", "F")
                elif "." in code:
                    self.add("WARNING", f, f"Choice code '{code}' has a decimal point.", "Use whole numbers as codes.", "F")
                if label == "":
                    self.add("ERROR", f, f"Choice code '{code}' has no label.", "Add the answer text after the comma.", "F")
            for code, count in Counter(codes).items():
                if count > 1:
                    self.add("ERROR", f, f"Choice code '{code}' is used {count} times.", "Each code must be unique.", "F")
            for label, count in Counter(lbl.lower() for _, lbl in f.choices).items():
                if count > 1 and label:
                    self.add("WARNING", f, f"The answer label '{label}' appears {count} times.",
                             "Check for a copy-paste mistake.", "F")
            numeric = [c for c in codes if re.fullmatch(r"-?\d+(\.\d+)?", c)]
            if numeric and len(numeric) != len(codes):
                self.add("WARNING", f, "Choice codes mix numbers and text ("
                         + ", ".join(codes[:6]) + "). Statistics software will treat the variable as text.",
                         "Use numbers for every code, e.g. 98 = Don't know, 99 = Prefer not to say.", "F")
            if ftype in ("radio", "dropdown") and len(f.choices) == 1 and not f.choice_problems:
                self.add("WARNING", f, f"This {ftype} field has only one choice.",
                         "Add the other answers, or use a checkbox for a single tick box.", "F")
            if ftype == "checkbox":
                odd = [c for c in codes if c and not re.fullmatch(r"\d+", c)]
                if odd:
                    columns = ", ".join(rd.checkbox_column(f.name, c) for c in odd[:3])
                    self.add("NOTE", f, f"Checkbox codes {', '.join(odd[:3])} are not plain whole numbers; "
                             f"their export columns will be named {columns}.", "", "F")
        elif ftype == "calc":
            if not raw:
                self.add("ERROR", f, "A calculated field needs an equation in column F.",
                         "e.g. round([weight_kg] / (([height_cm] / 100) ^ 2), 1)", "F")
        elif ftype == "slider":
            labels = [p.strip() for p in raw.split("|")] if raw else []
            if len(labels) > 3:
                self.add("WARNING", f, f"A slider shows at most 3 labels (left | middle | right); this one has {len(labels)}.",
                         "Keep 3 or fewer labels.", "F")
        elif ftype in ("yesno", "truefalse", "text", "notes", "descriptive", "file") and raw:
            self.add("WARNING", f, f"Column F has text, but a {ftype} field ignores it.",
                     "Clear column F, or change the field type.", "F")

    def check_validation(self, f):
        v = f.validation
        if not v:
            if (f.vmin or f.vmax) and f.ftype != "slider":
                self.add("ERROR", f, "Min/max values are set but there is no validation type.",
                         "Set a validation type such as integer, number or date_dmy, or clear min/max.", "I")
            if f.ftype == "slider":
                self.check_slider_range(f)
            return
        if f.ftype == "slider":
            if v != "number":
                self.add("ERROR", f, f"For a slider, column H can only be 'number' (shows the value); it is '{v}'.",
                         "Write 'number' or leave it empty.", "H")
            self.check_slider_range(f)
            return
        if f.ftype == "file":
            if v != "signature":
                self.add("ERROR", f, f"For a file field, column H can only be 'signature'; it is '{v}'.",
                         "Write 'signature' or leave it empty.", "H")
            return
        if f.ftype != "text":
            self.add("ERROR", f, f"Validation '{v}' is set on a {f.ftype} field; validation only works on text fields.",
                     "Clear column H, or change the field type to text.", "H")
            return
        if v in rd.LEGACY_VALIDATION:
            self.add("WARNING", f, f"'{v}' is an old validation name.", f"Use '{rd.LEGACY_VALIDATION[v]}'.", "H")
        elif v not in rd.VALIDATION_TYPES:
            if v.lower() in rd.VALIDATION_TYPES:
                self.add("ERROR", f, f"Validation type '{v}' must be lowercase.", f"Write '{v.lower()}'.", "H")
                return
            close = difflib.get_close_matches(v.lower(), list(rd.VALIDATION_TYPES), n=1)
            hint = f"Did you mean '{close[0]}'? " if close else ""
            self.add("WARNING", f, f"'{v}' is not a standard REDCap validation type.",
                     hint + "If it is a custom type, check the client's REDCap server has it enabled.", "H")
            return
        kind = f.validation_kind
        if (f.vmin or f.vmax) and kind not in rd.RANGE_KINDS:
            self.add("ERROR", f, f"Validation '{v}' cannot have min/max values.", "Clear columns I and J.", "I")
            return
        low = self.parse_limit(f, f.vmin, kind, "I")
        high = self.parse_limit(f, f.vmax, kind, "J")
        if low is not None and high is not None and low > high:
            self.add("ERROR", f, f"Min ({f.vmin}) is greater than max ({f.vmax}).", "Swap or correct the limits.", "I")
        if kind == "date" and not (f.vmin or f.vmax) and _looks_like_dob(f):
            self.add("NOTE", f, "Date of birth has no min/max.", "Consider min 1900-01-01 and max today.", "I")

    def check_slider_range(self, f):
        for value, column in ((f.vmin, "I"), (f.vmax, "J")):
            if value and not re.fullmatch(r"-?\d+", value):
                self.add("ERROR", f, f"Slider min/max must be whole numbers; got '{value}'.", "", column)

    def parse_limit(self, f, value, kind, column):
        if not value:
            return None
        if re.fullmatch(r"\[[a-z][a-z0-9_]*\]", value):
            name = value[1:-1]
            if name not in self.dd.by_name:
                self.add("ERROR", f, f"Min/max {value} refers to a field that does not exist.", self.suggest(name), column)
            else:
                self.add("NOTE", f, f"Min/max uses another field ({value}); this needs a recent REDCap version.", "", column)
            return None
        bad = None
        result = None
        if kind == "integer":
            if re.fullmatch(r"-?\d+", value):
                result = int(value)
            else:
                bad = "a whole number"
        elif kind in ("number", "number_comma"):
            try:
                result = float(value.replace(",", ".") if kind == "number_comma" else value)
            except ValueError:
                bad = "a number"
        elif kind == "date":
            if value.lower() == "today":
                return None
            try:
                result = dt.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                bad = "a date written YYYY-MM-DD (or 'today')"
        elif kind in ("datetime", "datetime_seconds"):
            if value.lower() in ("now", "today"):
                return None
            formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
            for fmt in formats:
                try:
                    result = dt.datetime.strptime(value, fmt)
                    break
                except ValueError:
                    pass
            else:
                bad = "a date and time written YYYY-MM-DD HH:MM (or 'now')"
        elif kind in ("time", "time_hms", "time_ms"):
            pattern = {"time": r"\d{1,2}:\d{2}", "time_hms": r"\d{1,2}:\d{2}:\d{2}", "time_ms": r"\d{1,2}:\d{2}"}[kind]
            if re.fullmatch(pattern, value):
                result = ":".join(part.zfill(2) for part in value.split(":"))
            else:
                bad = {"time": "a time written HH:MM", "time_hms": "a time written HH:MM:SS",
                       "time_ms": "a time written MM:SS"}[kind]
        if bad:
            fix = f"Write it as {bad}."
            if kind == "date" and re.fullmatch(r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4}", value):
                fix = ("REDCap stores date limits as YYYY-MM-DD in the data dictionary, whatever the display "
                       "format. e.g. 31-12-2026 becomes 2026-12-31.")
            self.add("ERROR", f, f"{'Min' if column == 'I' else 'Max'} value '{value}' is not {bad}.", fix, column)
            return None
        return result

    def check_flags(self, f):
        for value, what, column in ((f.identifier, "Identifier?", "K"), (f.required, "Required Field?", "M"),
                                    (f.matrix_ranking, "Matrix Ranking?", "Q")):
            if value not in ("", "y", "Y"):
                self.add("ERROR", f, f"'{what}' must be 'y' or empty; it is '{value}'.",
                         "Write y, or leave the cell empty for no.", column)
        if f.alignment not in ALIGNMENTS:
            if f.alignment.upper() in ALIGNMENTS:
                self.add("WARNING", f, f"Custom alignment '{f.alignment}' should be uppercase.",
                         f"Write '{f.alignment.upper()}'.", "N")
            else:
                self.add("ERROR", f, f"Custom alignment '{f.alignment}' is not valid.",
                         "Use LV, LH, RV, RH or leave empty.", "N")
        if f.is_required and f.ftype in ("descriptive", "calc"):
            self.add("WARNING", f, f"'Required' has no effect on a {f.ftype} field.", "Clear column M.", "M")
        if f.matrix_ranking.strip().lower() == "y" and not f.matrix:
            self.add("ERROR", f, "Matrix ranking is set but the field is not in a matrix group.", "Clear column Q.", "Q")
        if not f.is_identifier and f.ftype not in ("descriptive", "calc") and self.looks_like_identifier(f):
            self.add("WARNING", f, f"'{f.name}' looks like it collects identifying information but is not "
                     "flagged as an identifier.",
                     "If it does, put y in 'Identifier?' so de-identified exports leave it out. "
                     "Confirm with the client.", "K")

    def looks_like_identifier(self, f) -> bool:
        if f.validation in ID_VALIDATIONS:
            return True
        if any(re.search(p, f.name) for p in ID_NAME_PATTERNS):
            return True
        label = re.sub(r"\([^)]*\)", " ", rd.strip_html(f.label))  # ignore hints in brackets
        return any(re.search(p, label, re.I) for p in ID_LABEL_PATTERNS)

    def check_annotation(self, f):
        tags = rd.action_tags(f.annotation)
        if not tags and re.search(r"(^|\s)@[a-z]+", f.annotation):
            self.add("WARNING", f, "The annotation has an '@' word in lowercase; action tags must be uppercase.",
                     "e.g. write @HIDDEN, not @hidden.", "R")
        names = [t for t, _ in tags]
        for tag, arg in tags:
            if tag not in rd.ACTION_TAGS:
                self.add("NOTE", f, f"{tag} is not a built-in action tag (fine if it comes from an external "
                         "module installed on the client's server).", "", "R")
            if tag == "@NONEOFTHEABOVE" or tag in ("@HIDECHOICE", "@SHOWCHOICE"):
                if tag == "@NONEOFTHEABOVE" and f.ftype != "checkbox":
                    self.add("ERROR", f, "@NONEOFTHEABOVE only works on checkbox fields.", "Remove the tag.", "R")
                    continue
                codes = [c.strip() for c in arg.split(",") if c.strip()]
                if tag == "@NONEOFTHEABOVE" and not codes:
                    self.add("WARNING", f, "@NONEOFTHEABOVE has no code.", "Write it like @NONEOFTHEABOVE='99'.", "R")
                for code in codes:
                    if code not in f.choice_map:
                        level = "ERROR" if tag == "@NONEOFTHEABOVE" else "WARNING"
                        self.add(level, f, f"{tag} uses code '{code}', which is not one of this field's choices.",
                                 "Use one of: " + ", ".join(f.choice_map), "R")
            if tag == "@MAXCHECKED" and f.ftype != "checkbox":
                self.add("ERROR", f, "@MAXCHECKED only works on checkbox fields.", "Remove the tag.", "R")
            if tag in ("@CHARLIMIT", "@WORDLIMIT") and f.ftype not in ("text", "notes"):
                self.add("WARNING", f, f"{tag} only works on text and notes fields.", "Remove the tag.", "R")
            if tag == "@CALCTEXT":
                if f.ftype != "text":
                    self.add("WARNING", f, "@CALCTEXT should be on a text field.", "Change the field type to text.", "R")
                if arg.strip():
                    self.check_logic(f, arg, "calctext")
            if tag == "@CALCDATE":
                if not f.is_date:
                    self.add("WARNING", f, "@CALCDATE should be on a text field with date validation.",
                             "Set a date validation such as date_dmy.", "R")
                if arg.strip():
                    self.check_logic(f, f"calcdate({arg})", "calcdate")
            if tag in ("@DEFAULT", "@SETVALUE", "@PLACEHOLDER", "@PREFILL"):
                for name, event, text in rd.piping_refs(arg):
                    if name not in self.dd.by_name:
                        self.add("WARNING", f, f"{tag} pipes {text}, but there is no field '{name}'.",
                                 self.suggest(name), "R")
        if "@HIDDEN" in names and f.is_required:
            self.add("WARNING", f, "The field is both @HIDDEN and required, so staff may be asked for an answer "
                     "they cannot see.", "Remove 'required' or the @HIDDEN tag.", "R")
        if "@READONLY" in names and f.is_required and not any(t in names for t in ("@DEFAULT", "@SETVALUE", "@CALCTEXT", "@CALCDATE", "@NOW", "@TODAY")):
            self.add("WARNING", f, "The field is read-only and required, but nothing fills it in.",
                     "Add @DEFAULT/@SETVALUE, or remove 'required'.", "R")

    def check_piping(self, f):
        for text, column in ((f.label, "E"), (f.note, "G"), (f.section, "C")):
            for name, event, original in rd.piping_refs(text):
                if name not in self.dd.by_name:
                    self.add("WARNING", f, f"The text pipes {original}, but there is no field '{name}'. "
                             "(Ignore this if the brackets are meant as plain text.)", self.suggest(name), column)
        for code, label in f.choices:
            for name, event, original in rd.piping_refs(label):
                if name not in self.dd.by_name:
                    self.add("WARNING", f, f"Choice '{code}' pipes {original}, but there is no field '{name}'.",
                             self.suggest(name), "F")

    def check_logic(self, f, text, kind):
        column = "L" if kind == "branching" else ("R" if kind in ("calctext", "calcdate") else "F")
        what = {"branching": "Branching logic", "calc": "Calculation", "calctext": "@CALCTEXT",
                "calcdate": "@CALCDATE"}[kind]
        try:
            tree, warnings = rl.parse(text)
        except rl.LogicError as exc:
            fix = LOGIC_HELP
            if kind == "calc":
                fix = "Example: round([weight_kg] / (([height_cm] / 100) ^ 2), 1)"
            self.add("ERROR", f, f"{what} cannot be read: {exc.message}.", fix, column)
            return
        for warning in warnings:
            self.add("WARNING", f, f"{what}: {warning}.", "", column)
        refs = rl.references(tree)
        arithmetic = arithmetic_refs(tree)  # refs used with + - * / ^ or number functions
        for ref in refs:
            if ref.smart:
                self.smart_variables.add(ref.smart)
                if ref.event:
                    self.check_event_name(f, ref, column)
                continue
            if ref.event:
                self.events_referenced.add(ref.event)
                self.check_event_name(f, ref, column)
            target = self.dd.by_name.get(ref.field)
            if target is None:
                self.add("ERROR", f, f"{what} refers to [{ref.field}], which does not exist.",
                         self.suggest(ref.field), column)
                continue
            if target.name == f.name and kind in ("branching", "calc"):
                self.add("ERROR", f, f"{what} refers to the field itself.",
                         "A field cannot depend on its own value.", column)
            if ref.code is not None and target.ftype != "checkbox":
                self.add("ERROR", f, f"{ref.text}: the (code) form is only for checkbox fields, and "
                         f"'{target.name}' is a {target.ftype} field.",
                         f"Write [{target.name}] = '{ref.code}' instead.", column)
            if ref.code is not None and target.ftype == "checkbox" and ref.code not in target.choice_map:
                self.add("ERROR", f, f"{ref.text}: '{ref.code}' is not one of the codes of '{target.name}' "
                         f"({', '.join(target.choice_map)}).", "Use an existing code.", column)
            if ref.code is None and target.ftype == "checkbox" and not ref.modifier:
                self.add("ERROR", f, f"[{target.name}] is a checkbox; logic must name the option.",
                         f"Write [{target.name}(1)] = '1' for 'option 1 is ticked'.", column)
            if target.ftype == "descriptive":
                self.add("ERROR", f, f"[{target.name}] is a descriptive field and never has a value.",
                         "Point the logic at a field that stores data.", column)
            if kind == "branching" and not ref.event and target.form == f.form:
                if self.field_index.get(target.name, 0) > self.field_index.get(f.name, 0):
                    self.add("WARNING", f, f"Branching logic depends on [{target.name}], which comes later in the form.",
                             "Move the question it depends on above this one.", column)
            if kind in ("branching", "calc") and self.event_map and not ref.event and target.form != f.form:
                mine = set(self.event_map.events_for_form(f.form))
                theirs = set(self.event_map.events_for_form(target.form))
                if mine and theirs and not (mine & theirs):
                    self.add("WARNING", f, f"[{target.name}] is on form '{target.form}', which is never in the same "
                             f"event as '{f.form}'.", "Add the event name in front, e.g. "
                             f"[{sorted(theirs)[0]}][{target.name}].", column)
            if kind == "calc":
                if target.ftype in ("notes", "file"):
                    self.add("ERROR", f, f"{what} uses [{target.name}], a {target.ftype} field, which has no number.",
                             "Remove it from the calculation.", column)
                elif id(ref) in arithmetic and target.is_date:
                    self.add("WARNING", f, f"Calculation does arithmetic on the date field [{target.name}].",
                             "Use datediff([date1], [date2], \"d\") to work with dates.", column)
                elif id(ref) in arithmetic and not target.is_numeric and target.ftype not in ("checkbox", "descriptive"):
                    self.add("WARNING", f, f"Calculation does arithmetic on [{target.name}], which is not a number "
                             f"field ({target.ftype}{' ' + target.validation if target.validation else ''}).",
                             "Give it integer/number validation, or use numeric choice codes.", column)
        for op, left, right in rl.comparisons(tree):
            self.check_comparison(f, op, left, right, what, column)

    def check_comparison(self, f, op, left, right, what, column):
        if left[0] != "ref" and right[0] == "ref":
            left, right = right, left
        if left[0] != "ref" or left[1].smart:
            return
        ref = left[1]
        literal = rl.literal_text(right)
        target = self.dd.by_name.get(ref.field)
        if target is None or literal is None:
            return
        if ref.code is not None and target.ftype == "checkbox":
            if literal not in ("0", "1", ""):
                self.add("WARNING", f, f"{what}: {ref.text} is compared with '{literal}', but a checkbox option is "
                         "only ever '1' (ticked) or '0' (not ticked).", f"Write {ref.text} = '1'.", column)
            return
        if target.ftype in ("radio", "dropdown", "yesno", "truefalse") and op in ("=", "<>") and literal != "":
            if literal not in target.choice_map and not (rl._is_number(literal) and any(
                    rl._is_number(c) and float(c) == float(literal) for c in target.choice_map)):
                self.add("WARNING", f, f"{what}: [{target.name}] is compared with '{literal}', which is not one of "
                         f"its codes ({', '.join(target.choice_map)}).", "Use one of the existing codes.", column)

    def check_event_name(self, f, ref, column):
        if not ref.event or "-" in ref.event:
            return
        if self.event_map is None:
            return
        if ref.event not in self.event_map.forms_by_event:
            close = difflib.get_close_matches(ref.event, self.event_map.events, n=1)
            self.add("ERROR", f, f"[{ref.event}] is not an event in the event mapping file.",
                     (f"Did you mean [{close[0]}]? " if close else "") + "Unique event names look like visit_1_arm_1.",
                     column)
            return
        target = self.dd.by_name.get(ref.field) if ref.field else None
        if target and target.form not in self.event_map.forms_by_event[ref.event]:
            self.add("WARNING", f, f"{ref.text}: form '{target.form}' is not used in event '{ref.event}', so this "
                     "value will always be blank.", "Check the event name or the instrument-event mapping.", column)

    def check_matrices(self):
        blocks = []
        fields = self.dd.fields
        for i, f in enumerate(fields):
            if not f.matrix:
                continue
            if i > 0 and fields[i - 1].matrix == f.matrix and blocks and blocks[-1][1][-1] is fields[i - 1]:
                blocks[-1][1].append(f)
            else:
                blocks.append((f.matrix, [f]))
        seen = set()
        for name, members in blocks:
            first = members[0]
            if name in seen:
                self.add("ERROR", first, f"Matrix group '{name}' is used in two separate places.",
                         "Fields of one matrix must be next to each other; give the second block another name.", "P")
            seen.add(name)
            if not NAME_RE.match(name):
                self.add("ERROR", first, f"Matrix group name '{name}' must use lowercase letters, numbers and "
                         "underscores.", "", "P")
            types = {m.ftype for m in members}
            if not types <= {"radio", "checkbox"}:
                self.add("ERROR", first, f"Matrix group '{name}' contains {', '.join(sorted(types - {'radio', 'checkbox'}))} "
                         "fields; a matrix can only hold radio or checkbox fields.", "", "P")
            if len(types) > 1:
                self.add("ERROR", first, f"Matrix group '{name}' mixes radio and checkbox fields.",
                         "Use one field type for the whole matrix.", "P")
            choice_sets = {tuple(m.choices) for m in members}
            if len(choice_sets) > 1:
                odd = [m.name for m in members if tuple(m.choices) != tuple(first.choices)]
                self.add("ERROR", first, f"Fields in matrix group '{name}' must have identical choices; "
                         f"these differ from the first row: {', '.join(odd)}.", "Copy the same choices to every row.", "F")
            for m in members[1:]:
                if m.section:
                    self.add("WARNING", m, f"A section header in the middle of matrix '{name}' splits the matrix in two.",
                             "Put the matrix header only on the first field of the group.", "C")
            ranking = {m.matrix_ranking.strip().lower() for m in members}
            if "y" in ranking:
                if "checkbox" in types:
                    self.add("ERROR", first, f"Matrix ranking only works with radio matrices ('{name}').", "", "Q")
                if len(ranking) > 1:
                    self.add("WARNING", first, f"Matrix ranking is set on some rows of '{name}' but not others.",
                             "Set it the same on every row.", "Q")
            if len(members) == 1:
                self.add("NOTE", first, f"Matrix group '{name}' has only one field.", "", "P")
            if not first.section:
                self.add("NOTE", first, f"Matrix group '{name}' has no header (section header on its first field).",
                         "Add the matrix question text as the section header of the first row.", "C")

    def check_calc_cycles(self):
        graph = {}
        for f in self.dd.fields:
            if f.ftype == "calc" and f.choices_raw:
                try:
                    tree, _ = rl.parse(f.choices_raw)
                except rl.LogicError:
                    continue
                graph[f.name] = {r.field for r in rl.references(tree) if r.field and r.field != f.name}
        state = {}

        def visit(node, path):
            state[node] = "active"
            for nxt in graph.get(node, ()):
                if nxt not in graph:
                    continue
                if state.get(nxt) == "active":
                    cycle = path[path.index(nxt):] + [nxt] if nxt in path else [node, nxt]
                    self.add("ERROR", self.dd.by_name[node], "Calculated fields depend on each other in a circle: "
                             + " -> ".join(cycle) + ".", "Break the loop so each calculation uses earlier values.", "F")
                elif nxt not in state:
                    visit(nxt, path + [nxt])
            state[node] = "done"

        for name in graph:
            if name not in state:
                visit(name, [name])

    def check_events(self):
        if self.event_map is None:
            if self.events_referenced:
                self.add("NOTE", None, "Logic uses event names (" + ", ".join(sorted(self.events_referenced)) +
                         "). Run again with --events to check them.", "", row=0, field="")
            return
        mapped_forms = {form for forms in self.event_map.forms_by_event.values() for form in forms}
        for form in sorted(mapped_forms - set(self.dd.forms)):
            self.add("ERROR", None, f"The event mapping uses form '{form}', which is not in the dictionary.",
                     "Fix the form name in the mapping file.", row=0, field="")
        for form in self.dd.forms:
            if form not in mapped_forms:
                self.add("WARNING", self.dd.form_fields(form)[0], f"Form '{form}' is not designated to any event, "
                         "so nobody can enter data in it.", "Add it to an event in the mapping.", "B", field="")
        if self.repeating:
            for event, form in sorted(self.repeating):
                if event and event not in self.event_map.forms_by_event:
                    self.add("ERROR", None, f"Repeating setup names event '{event}', which is not in the event mapping.",
                             "", row=0, field="")
                elif form and form not in self.dd.forms:
                    self.add("ERROR", None, f"Repeating setup names form '{form}', which is not in the dictionary.",
                             "", row=0, field="")
                elif event and form and form not in self.event_map.forms_by_event.get(event, []):
                    self.add("ERROR", None, f"Form '{form}' is set to repeat in '{event}' but is not designated to that event.",
                             "", row=0, field="")

    def check_summaries(self):
        free_text = [f.name for f in self.dd.fields[1:]
                     if f.ftype == "notes" or (f.ftype == "text" and not f.validation and not f.is_identifier)]
        if free_text:
            self.add("NOTE", None, f"{len(free_text)} free-text field(s) ({', '.join(free_text[:6])}"
                     f"{', ...' if len(free_text) > 6 else ''}) could end up holding names or other identifiers.",
                     "Keep the reminder in the label or field note: 'no names or contact details'.", row=0, field="")
        if not any(f.is_identifier for f in self.dd.fields):
            self.add("NOTE", None, "No field is flagged as an identifier.",
                     "Confirm with the client that the form collects no names, dates of birth, contact details "
                     "or record numbers.", row=0, field="")
        if self.smart_variables:
            self.add("NOTE", None, "Logic uses smart variables (" + ", ".join(sorted(self.smart_variables)) +
                     "); their values cannot be checked here.", "Test these paths in the client's REDCap project.",
                     row=0, field="")


NUMBER_FUNCTIONS = {"sum", "mean", "min", "max", "median", "stdev", "round", "roundup", "rounddown",
                    "sqrt", "abs", "log", "exp", "mod"}


def arithmetic_refs(tree) -> set:
    """ids of references used as numbers (in + - * / ^ or number functions)."""
    found = set()
    if tree[0] == "ref":
        found.add(id(tree[1]))
    for node in rl.walk(tree):
        children = []
        if node[0] == "bin":
            children = [node[2], node[3]]
        elif node[0] == "neg":
            children = [node[1]]
        elif node[0] == "call" and node[1] in NUMBER_FUNCTIONS:
            children = node[2]
        elif node[0] == "call" and node[1] == "if":
            children = node[2][1:]  # the values returned by if()
        for child in children:
            if child[0] == "ref":
                found.add(id(child[1]))
    return found


def _looks_like_dob(f) -> bool:
    return bool(re.search(r"(^|_)dob($|_)|birth", f.name) or re.search(r"date of birth", f.label, re.I))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(path, dd, issues, event_map, repeating, strict=False, when=None) -> tuple[str, int]:
    errors = [i for i in issues if i.level == "ERROR"]
    warnings = [i for i in issues if i.level == "WARNING"]
    notes = [i for i in issues if i.level == "NOTE"]
    failed = bool(errors) or (strict and bool(warnings))
    lines = []
    title = "REDCap data dictionary check"
    lines += [title, "=" * len(title), ""]
    lines.append(f"File:     {path}")
    if when:
        lines.append(f"Checked:  {when}")
    if dd and dd.fields:
        per_form = ", ".join(f"{form} {len(dd.form_fields(form))}" for form in dd.forms)
        lines.append(f"Fields:   {len(dd.fields)} in {len(dd.forms)} form(s): {per_form}")
    if event_map:
        lines.append(f"Events:   {len(event_map.events)} ({', '.join(event_map.events)}) from {Path(event_map.path).name}")
    if repeating:
        lines.append("Repeating: " + ", ".join(f"{form or '(whole event)'} in {event}" for event, form in sorted(repeating)))
    lines.append("")
    verdict = "FAILED" if failed else "PASSED"
    lines.append(f"RESULT: {verdict} - {len(errors)} error(s), {len(warnings)} warning(s), {len(notes)} note(s)")
    if strict:
        lines.append("(strict mode: warnings count as failures)")
    lines.append("")
    if dd and dd.fields and dd.header_ok:
        lines += summary_lines(dd)
    sections = [
        ("Errors - must fix before uploading", errors),
        ("Warnings - fix, or confirm with the client that they are intended", warnings),
        ("Notes - good to know", notes),
    ]
    for heading, items in sections:
        lines += [heading, "-" * len(heading)]
        if not items:
            lines += ["  None.", ""]
            continue
        for issue in sorted(items, key=lambda i: (i.row or 0, i.field)):
            where = []
            if issue.row:
                where.append(f"Row {issue.row}")
            if issue.column:
                where.append(f"col {issue.column} ({COLUMN_TITLES.get(issue.column, '')})")
            place = ", ".join(where) or "Whole file"
            name = f" [{issue.field}]" if issue.field else ""
            lines.append(f"* {place}{name}")
            lines.append(f"    {issue.message}")
            if issue.fix:
                lines.append(f"    {'Tip' if issue.level == 'NOTE' else 'Fix'}: {issue.fix}")
        lines.append("")
    lines.append("Rows are spreadsheet rows (the header is row 1), so you can find them in Excel.")
    lines.append("This check cannot replace testing: import into a test project and try every path.")
    return "\n".join(lines) + "\n", (1 if failed else 0)


def summary_lines(dd) -> list[str]:
    lines = ["Summary", "-------"]
    types = Counter(f.ftype or "(empty)" for f in dd.fields)
    lines.append("Field types:      " + ", ".join(f"{t} {n}" for t, n in types.most_common()))
    identifiers = [f.name for f in dd.fields if f.is_identifier]
    lines.append("Identifiers:      " + (", ".join(identifiers) if identifiers else "none flagged"))
    required = [f for f in dd.fields if f.is_required]
    lines.append(f"Required fields:  {len(required)}")
    branching = [f for f in dd.fields if f.branching]
    lines.append(f"Branching logic:  {len(branching)} field(s)")
    calcs = [f.name for f in dd.fields if f.ftype == "calc"]
    lines.append("Calculated:       " + (", ".join(calcs) if calcs else "none"))
    groups = []
    for f in dd.fields:
        if f.matrix and f.matrix not in [g for g, _ in groups]:
            groups.append((f.matrix, sum(1 for x in dd.fields if x.matrix == f.matrix)))
    lines.append("Matrix groups:    " + (", ".join(f"{g} ({n} rows)" for g, n in groups) if groups else "none"))
    lines.append(f"Section headers:  {sum(1 for f in dd.fields if f.section)}")
    tags = Counter(t for f in dd.fields for t, _ in rd.action_tags(f.annotation))
    lines.append("Action tags:      " + (", ".join(f"{t} x{n}" for t, n in tags.most_common()) if tags else "none"))
    lines.append("")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a REDCap data dictionary CSV and explain any problems.")
    parser.add_argument("dictionary", help="data dictionary CSV file")
    parser.add_argument("--events", help="instrument-event mapping CSV (arm_num, unique_event_name, form)")
    parser.add_argument("--repeating", help="repeating instruments CSV (event_name, form_name, custom_form_label)")
    parser.add_argument("--report", help="also save the report to this text file")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    parser.add_argument("--no-date", action="store_true", help="leave the date out of the report")
    args = parser.parse_args(argv)

    path = Path(args.dictionary)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2
    dd, issues = rd.load_dictionary(path)
    if dd is None:
        for issue in issues:
            print(f"{issue.level}: {issue.message} {issue.fix}")
        return 2
    event_map = repeating = None
    if args.events:
        event_map, event_issues = rd.load_event_map(args.events)
        issues += event_issues
    if args.repeating:
        repeating, rep_issues = rd.load_repeating(args.repeating)
        issues += rep_issues
    if dd.header_ok:
        checker = Checker(dd, event_map, repeating)
        checker.run()
        issues += checker.issues
    else:
        issues.append(rd.Issue("NOTE", 0, "", "The rows were not checked because the header row is wrong.",
                               "Fix the header row first, then run the check again."))
    when = None if args.no_date else dt.date.today().isoformat()
    report, code = build_report(path.as_posix(), dd, issues, event_map, repeating, args.strict, when)
    print(report, end="")
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Report saved to {args.report}")
    return code


if __name__ == "__main__":
    sys.exit(main())
