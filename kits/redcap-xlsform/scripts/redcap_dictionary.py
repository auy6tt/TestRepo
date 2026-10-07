"""
Helper module used by the other scripts. You do not run it directly.

Reads a REDCap data dictionary CSV (the file you get from Project Setup >
Data Dictionary > Download) and, optionally, an instrument-event mapping CSV
(columns arm_num, unique_event_name, form) for longitudinal projects.

It only needs the Python standard library.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path

# The 18 columns of a REDCap data dictionary, in order.
STANDARD_HEADERS = [
    "Variable / Field Name",
    "Form Name",
    "Section Header",
    "Field Type",
    "Field Label",
    "Choices, Calculations, OR Slider Labels",
    "Field Note",
    "Text Validation Type OR Show Slider Number",
    "Text Validation Min",
    "Text Validation Max",
    "Identifier?",
    "Branching Logic (Show field only if...)",
    "Required Field?",
    "Custom Alignment",
    "Question Number (surveys only)",
    "Matrix Group Name",
    "Matrix Ranking?",
    "Field Annotation",
]

# The same columns as named by the REDCap API (export metadata).
API_HEADERS = [
    "field_name", "form_name", "section_header", "field_type", "field_label",
    "select_choices_or_calculations", "field_note",
    "text_validation_type_or_show_slider_number", "text_validation_min",
    "text_validation_max", "identifier", "branching_logic", "required_field",
    "custom_alignment", "question_number", "matrix_group_name", "matrix_ranking",
    "field_annotation",
]

FIELD_TYPES = {
    "text": "Text box",
    "notes": "Notes box (long text)",
    "dropdown": "Drop-down list (one answer)",
    "radio": "Radio buttons (one answer)",
    "checkbox": "Checkboxes (tick all that apply)",
    "yesno": "Yes / No",
    "truefalse": "True / False",
    "calc": "Calculated field",
    "slider": "Slider (visual analogue scale)",
    "descriptive": "Descriptive text (no data saved)",
    "file": "File upload",
    "sql": "Dynamic query (SQL)",
}

CHOICE_TYPES = {"radio", "dropdown", "checkbox"}
CATEGORICAL_TYPES = {"radio", "dropdown", "checkbox", "yesno", "truefalse"}
FIXED_CHOICES = {
    "yesno": [("1", "Yes"), ("0", "No")],
    "truefalse": [("1", "True"), ("0", "False")],
}

# Validation types REDCap ships with. kind -> how min/max and values are checked.
VALIDATION_TYPES = {
    "date_dmy": ("date", "Date (D-M-Y)"),
    "date_mdy": ("date", "Date (M-D-Y)"),
    "date_ymd": ("date", "Date (Y-M-D)"),
    "datetime_dmy": ("datetime", "Date and time (D-M-Y H:M)"),
    "datetime_mdy": ("datetime", "Date and time (M-D-Y H:M)"),
    "datetime_ymd": ("datetime", "Date and time (Y-M-D H:M)"),
    "datetime_seconds_dmy": ("datetime_seconds", "Date and time (D-M-Y H:M:S)"),
    "datetime_seconds_mdy": ("datetime_seconds", "Date and time (M-D-Y H:M:S)"),
    "datetime_seconds_ymd": ("datetime_seconds", "Date and time (Y-M-D H:M:S)"),
    "time": ("time", "Time (HH:MM)"),
    "time_hh_mm_ss": ("time_hms", "Time (HH:MM:SS)"),
    "time_mm_ss": ("time_ms", "Time (MM:SS)"),
    "integer": ("integer", "Whole number"),
    "number": ("number", "Number"),
    "number_1dp": ("number", "Number, 1 decimal place"),
    "number_2dp": ("number", "Number, 2 decimal places"),
    "number_3dp": ("number", "Number, 3 decimal places"),
    "number_4dp": ("number", "Number, 4 decimal places"),
    "number_comma_decimal": ("number_comma", "Number (comma as decimal)"),
    "number_1dp_comma_decimal": ("number_comma", "Number, 1 decimal place (comma)"),
    "number_2dp_comma_decimal": ("number_comma", "Number, 2 decimal places (comma)"),
    "number_3dp_comma_decimal": ("number_comma", "Number, 3 decimal places (comma)"),
    "number_4dp_comma_decimal": ("number_comma", "Number, 4 decimal places (comma)"),
    "email": ("email", "Email address"),
    "phone": ("phone", "Phone number (North America)"),
    "phone_australia": ("phone", "Phone number (Australia)"),
    "zipcode": ("postcode", "US zip code"),
    "postalcode_australia": ("postcode", "Postcode (Australia)"),
    "postalcode_canada": ("postcode", "Postal code (Canada)"),
    "postalcode_french": ("postcode", "Postal code (France)"),
    "postalcode_germany": ("postcode", "Postal code (Germany)"),
    "ssn": ("ssn", "US Social Security Number"),
    "alpha_only": ("letters", "Letters only"),
    "mrn_10d": ("mrn", "Medical record number (10 digits)"),
    "mrn_generic": ("mrn", "Medical record number"),
    "vmrn": ("mrn", "Medical record number (Vanderbilt)"),
}
LEGACY_VALIDATION = {"int": "integer", "float": "number", "date": "date_ymd",
                     "datetime": "datetime_ymd", "datetime_seconds": "datetime_seconds_ymd"}
RANGE_KINDS = {"date", "datetime", "datetime_seconds", "time", "time_hms", "time_ms",
               "integer", "number", "number_comma"}

# Built-in action tags (REDCap 14/15). Tags from external modules are reported as notes.
ACTION_TAGS = {
    "@APPUSERNAME-APP", "@BARCODE-APP", "@CALCDATE", "@CALCTEXT", "@CHARLIMIT",
    "@CONSENT-VERSION", "@DEFAULT", "@DOWNLOAD-COUNT", "@FORCE-MINMAX", "@HIDDEN",
    "@HIDDEN-APP", "@HIDDEN-FORM", "@HIDDEN-PDF", "@HIDDEN-SURVEY", "@HIDEBUTTON",
    "@HIDECHOICE", "@IF", "@INLINE", "@LANGUAGE-CURRENT-FORM",
    "@LANGUAGE-CURRENT-SURVEY", "@LANGUAGE-FORCE", "@LANGUAGE-FORCE-FORM",
    "@LANGUAGE-FORCE-SURVEY", "@LANGUAGE-SET", "@LATITUDE", "@LONGITUDE",
    "@MAXCHECKED", "@MAXCHOICE", "@MAXCHOICE-SURVEY-COMPLETE", "@NOMISSING",
    "@NONEOFTHEABOVE", "@NOW", "@NOW-SERVER", "@NOW-UTC", "@PASSWORDMASK",
    "@PLACEHOLDER", "@PREFILL", "@RANDOMORDER", "@READONLY", "@READONLY-APP",
    "@READONLY-FORM", "@READONLY-SURVEY", "@RICHTEXT", "@SETVALUE", "@SHOWCHOICE",
    "@SYNC-APP", "@TODAY", "@TODAY-SERVER", "@TODAY-UTC", "@USERNAME", "@WORDLIMIT",
}

FORM_STATUS = {"0": "Incomplete", "1": "Unverified", "2": "Complete"}
BOM = "\ufeff"
REDCAP_EXTRA_COLUMNS = ["redcap_event_name", "redcap_repeat_instrument",
                        "redcap_repeat_instance", "redcap_data_access_group",
                        "redcap_survey_identifier"]


@dataclass
class Issue:
    level: str          # ERROR, WARNING or NOTE
    row: int | None     # spreadsheet row (header row = 1)
    field: str          # variable name ('' if not about one field)
    message: str
    fix: str = ""
    column: str = ""    # dictionary column letter, e.g. "L"


@dataclass
class Field:
    row: int
    name: str
    form: str
    section: str
    ftype: str
    label: str
    choices_raw: str
    note: str
    validation: str
    vmin: str
    vmax: str
    identifier: str
    branching: str
    required: str
    alignment: str
    qnum: str
    matrix: str
    matrix_ranking: str
    annotation: str
    choices: list = dc_field(default_factory=list)       # [(code, label)]
    choice_problems: list = dc_field(default_factory=list)

    @property
    def is_identifier(self) -> bool:
        return self.identifier.strip().lower() == "y"

    @property
    def is_required(self) -> bool:
        return self.required.strip().lower() == "y"

    @property
    def choice_map(self) -> dict:
        return dict(self.choices)

    @property
    def validation_kind(self) -> str | None:
        name = LEGACY_VALIDATION.get(self.validation, self.validation)
        info = VALIDATION_TYPES.get(name)
        return info[0] if info else None

    @property
    def is_numeric(self) -> bool:
        """True if the stored value is a number (for calculations)."""
        if self.ftype in ("calc", "slider", "yesno", "truefalse"):
            return True
        if self.ftype == "text":
            return self.validation_kind in ("integer", "number", "number_comma")
        if self.ftype in ("radio", "dropdown"):
            return bool(self.choices) and all(_is_number(c) for c, _ in self.choices)
        return False

    @property
    def is_date(self) -> bool:
        return self.ftype == "text" and self.validation_kind in ("date", "datetime", "datetime_seconds")

    def export_columns(self) -> list[str]:
        """Column names this field gets in a REDCap CSV export."""
        if self.ftype == "descriptive":
            return []
        if self.ftype == "checkbox":
            return [checkbox_column(self.name, code) for code, _ in self.choices]
        return [self.name]


def checkbox_column(name: str, code: str) -> str:
    """Export column for one checkbox option, e.g. race___2 (minus signs become _)."""
    return f"{name}___{re.sub(r'[^A-Za-z0-9_]', '_', code).lower()}"


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except (TypeError, ValueError):
        return False


def parse_choices(raw: str):
    """Split '1, Yes | 0, No' into [('1', 'Yes'), ('0', 'No')]. Returns (choices, problems)."""
    choices, problems = [], []
    text = raw.strip()
    if not text:
        return choices, problems
    if "|" not in text and "\n" in text:
        problems.append("choices are on separate lines; REDCap needs them separated by ' | '")
        parts = text.splitlines()
    else:
        parts = text.split("|")
    for part in parts:
        piece = part.strip()
        if not piece:
            problems.append("there is an empty choice (two '|' in a row, or a '|' at the start or end)")
            continue
        if "," not in piece:
            problems.append(f'choice "{piece}" has no comma between the code and the label')
            continue
        code, label = piece.split(",", 1)
        choices.append((code.strip(), label.strip()))
    return choices, problems


@dataclass
class Dictionary:
    path: str
    fields: list
    header_style: str
    by_name: dict
    forms: list
    header_ok: bool = True

    def form_fields(self, form: str) -> list:
        return [f for f in self.fields if f.form == form]

    @property
    def record_id(self):
        return self.fields[0] if self.fields else None

    def export_header(self, longitudinal: bool = False, repeating: bool = False) -> list[str]:
        """Column order of a raw REDCap CSV export (all fields, all forms)."""
        header = []
        record_id = self.record_id.name if self.record_id else "record_id"
        header.append(record_id)
        if longitudinal:
            header.append("redcap_event_name")
        if repeating:
            header += ["redcap_repeat_instrument", "redcap_repeat_instance"]
        for form in self.forms:
            for f in self.form_fields(form):
                if f.name == record_id:
                    continue
                header += f.export_columns()
            header.append(f"{form}_complete")
        return header


def read_csv_text(path: str | Path):
    """Read a CSV file as text. Returns (text, delimiter, issues)."""
    issues = []
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
        issues.append(Issue("WARNING", None, "", "The file is not saved as UTF-8, so accented letters "
                            "and symbols may turn into strange characters in REDCap.",
                            "In Excel use File > Save As > 'CSV UTF-8 (Comma delimited)'."))
    first_line = text.splitlines()[0] if text.strip() else ""
    delimiter = ","
    if first_line.count(";") > first_line.count(","):
        delimiter = ";"
        issues.append(Issue("ERROR", 1, "", "The file uses semicolons (;) between columns. REDCap needs commas.",
                            "Excel in some countries saves CSV with semicolons. Save as "
                            "'CSV UTF-8 (Comma delimited)' or change the list separator."))
    elif first_line.count("\t") > first_line.count(","):
        delimiter = "\t"
        issues.append(Issue("ERROR", 1, "", "The file uses tabs between columns. REDCap needs commas.",
                            "Save it as 'CSV UTF-8 (Comma delimited)'."))
    return text, delimiter, issues


def load_dictionary(path: str | Path):
    """Read a data dictionary. Returns (Dictionary or None, list of Issue)."""
    issues: list[Issue] = []
    try:
        text, delimiter, read_issues = read_csv_text(path)
    except OSError as exc:
        return None, [Issue("ERROR", None, "", f"Cannot open the file: {exc}")]
    issues += read_issues
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    if not rows:
        return None, issues + [Issue("ERROR", None, "", "The file is empty.")]
    raw_width = len(rows[0])
    header = [h.replace(BOM, "").strip() for h in rows[0]]
    while header and header[-1] == "":
        header.pop()
    style = "standard"
    header_ok = True
    if header == STANDARD_HEADERS:
        pass
    elif header == API_HEADERS:
        style = "api"
        issues.append(Issue("NOTE", 1, "", "The column headers are the API names (field_name, form_name, ...). "
                            "That is fine for the API; the web upload page expects the standard "
                            "18 headers ('Variable / Field Name', ...).",
                            "Download a data dictionary from REDCap and copy its header row if the upload is refused."))
    elif [h.lower() for h in header] == [h.lower() for h in STANDARD_HEADERS]:
        issues.append(Issue("WARNING", 1, "", "The column headers differ from REDCap's only in capital letters.",
                            "Copy the header row from a data dictionary downloaded from REDCap."))
    elif len(header) != 18:
        header_ok = False
        missing = [h for h in STANDARD_HEADERS if h not in header]
        issues.append(Issue("ERROR", 1, "", f"The header row has {len(header)} columns; a REDCap data "
                            "dictionary has exactly 18, in a fixed order."
                            + (f" Missing: {'; '.join(missing)}." if missing else ""),
                            "Start from a data dictionary downloaded from REDCap (or templates/"
                            "data_dictionary_template.csv in this kit) and keep all 18 columns, even empty ones."))
    else:
        for i, expected in enumerate(STANDARD_HEADERS):
            got = header[i]
            if got != expected and got.lower() != API_HEADERS[i]:
                issues.append(Issue("ERROR", 1, "", f"Column {_col(i)} should be '{expected}' but is '{got}'.",
                                    "Put the 18 standard columns back in their original order and spelling."))
    fields: list[Field] = []
    for index, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            if any(r for r in rows[index:] if any(c.strip() for c in r)):  # blank row before more data
                issues.append(Issue("WARNING", index, "", "This row is empty.", "Delete the empty row."))
            continue
        cells = list(row)
        if len(cells) > 18 and any(c.strip() for c in cells[18:]):
            issues.append(Issue("ERROR", index, cells[0].strip(), f"This row has {len(cells)} cells instead of 18, "
                                "so text has spilled into extra columns.",
                                "Usually a comma inside text that is not wrapped in quotes. Re-save from Excel "
                                "as CSV, which adds the quotes for you."))
        elif len(cells) != raw_width and header_ok:
            issues.append(Issue("WARNING", index, cells[0].strip() if cells else "",
                                f"This row has {len(cells)} cells but the header row has {raw_width}. "
                                "Text may have shifted into the wrong columns.",
                                "Look for a comma inside text that is not wrapped in quotes, or a missing comma."))
        cells = (cells + [""] * 18)[:18]
        values = [c.strip() for c in cells]
        f = Field(index, *values)
        f.ftype = f.ftype.strip()
        if f.ftype in CHOICE_TYPES:
            f.choices, f.choice_problems = parse_choices(f.choices_raw)
        elif f.ftype in FIXED_CHOICES:
            f.choices = list(FIXED_CHOICES[f.ftype])
        fields.append(f)
    by_name = {}
    for f in fields:
        by_name.setdefault(f.name, f)
    forms = []
    for f in fields:
        if f.form and f.form not in forms:
            forms.append(f.form)
    return Dictionary(str(path), fields, style, by_name, forms, header_ok), issues


def _col(index: int) -> str:
    return chr(ord("A") + index)


def column_letter(key: str) -> str:
    """Spreadsheet column letter of a dictionary column, e.g. 'branching' -> 'L'."""
    order = ["name", "form", "section", "ftype", "label", "choices_raw", "note", "validation",
             "vmin", "vmax", "identifier", "branching", "required", "alignment", "qnum",
             "matrix", "matrix_ranking", "annotation"]
    return _col(order.index(key))


# ---------------------------------------------------------------------------
# Longitudinal projects: instrument-event mapping
# ---------------------------------------------------------------------------

@dataclass
class EventMap:
    path: str
    events: list            # unique event names in file order
    forms_by_event: dict    # event -> [forms]
    arm_by_event: dict

    def events_for_form(self, form: str) -> list:
        return [e for e in self.events if form in self.forms_by_event.get(e, [])]


def load_event_map(path: str | Path):
    """Read an instrument-event mapping CSV (arm_num, unique_event_name, form)."""
    issues = []
    text, delimiter, read_issues = read_csv_text(path)
    issues += read_issues
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    needed = {"unique_event_name", "form"}
    columns = {c.strip() for c in (reader.fieldnames or [])}
    if not needed <= columns:
        issues.append(Issue("ERROR", 1, "", f"The event mapping file needs the columns arm_num, "
                            f"unique_event_name and form; it has: {', '.join(sorted(columns)) or 'none'}.",
                            "Download it from REDCap: Project Setup > Designate Instruments for My Events."))
        return None, issues
    events, forms_by_event, arm_by_event = [], {}, {}
    for row in reader:
        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        event, form = row.get("unique_event_name", ""), row.get("form", "")
        if not event or not form:
            continue
        if event not in events:
            events.append(event)
        forms_by_event.setdefault(event, []).append(form)
        arm_by_event[event] = row.get("arm_num", "1")
    return EventMap(str(path), events, forms_by_event, arm_by_event), issues


def load_repeating(path: str | Path):
    """Read a repeating instruments file (event_name, form_name, custom_form_label).
    Returns a set of (event, form) pairs; form '' means the whole event repeats."""
    text, delimiter, issues = read_csv_text(path)
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    pairs = set()
    for row in reader:
        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        pairs.add((row.get("event_name", ""), row.get("form_name", "")))
    return pairs, issues


# ---------------------------------------------------------------------------
# Action tags and piping
# ---------------------------------------------------------------------------

_TAG = re.compile(r"@[A-Z][A-Z0-9_-]*")


def action_tags(annotation: str) -> list[tuple[str, str]]:
    """Find action tags in a Field Annotation. Returns [(tag, argument text)].
    The argument is what follows the tag: ='...' or (...) or ''."""
    found = []
    for match in _TAG.finditer(annotation or ""):
        tag = match.group()
        rest = annotation[match.end():]
        arg = ""
        stripped = rest.lstrip()
        if stripped.startswith("="):
            value = stripped[1:].lstrip()
            if value[:1] in ("'", '"'):
                close = value.find(value[0], 1)
                arg = value[1:close] if close != -1 else value[1:]
            else:
                arg = re.split(r"\s", value, maxsplit=1)[0]
        elif rest.startswith("("):
            depth, end = 0, None
            for i, ch in enumerate(rest):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            arg = rest[1:end] if end is not None else rest[1:]
        found.append((tag, arg))
    return found


_PIPE = re.compile(r"(?:\[[^\[\]\n]+\])+")
_PIPE_PART = re.compile(r"[a-z][a-z0-9_]*(?:\([^()]*\))?(?::[a-z-]+)?")


def piping_refs(text: str) -> list[tuple[str, str | None, str]]:
    """Find piped fields like [first_name] or [visit_1_arm_1][weight] in label text.
    Returns [(field name, event or None, original text)]. Bracketed words that
    cannot be variable names (spaces, capitals, smart variables) are skipped."""
    refs = []
    for match in _PIPE.finditer(text or ""):
        parts = re.findall(r"\[([^\[\]]+)\]", match.group())
        names = [p.strip() for p in parts]
        if any("-" in p.split(":")[0] for p in names):
            continue  # smart variable
        if not all(_PIPE_PART.fullmatch(p) for p in names[:2]):
            continue
        if len(names) >= 2 and not names[1].isdigit():
            event, main = names[0], names[1]
        else:
            event, main = None, names[0]
        refs.append((main.split("(")[0].split(":")[0], event, match.group()))
    return refs


class RecordContext:
    """Looks up values for one record in REDCap export rows, so logic can be evaluated.

    rows: {(event, repeat_instrument, instance): {column: raw value}} for ONE record.
    current: the key of the row being checked.
    """

    def __init__(self, dd: "Dictionary", record_id: str, rows: dict, current: tuple):
        self.dd = dd
        self.record_id = record_id
        self.rows = rows
        self.current = current

    def get(self, ref) -> str:
        from redcap_logic import Unknown  # local import keeps the modules independent
        event, repeat_form, instance = self.current
        if ref.smart:
            name = ref.smart.split(":")[0]
            if name == "event-name" and not ref.field:
                return event
            if name == "record-name":
                return self.record_id
            if name == "current-instance":
                return instance or "1"
            raise Unknown(f"smart variable [{ref.smart}]")
        field = self.dd.by_name.get(ref.field)
        if field is None:
            raise Unknown(f"unknown field [{ref.field}]")
        if field.ftype == "checkbox":
            if ref.code is None:
                raise Unknown(f"checkbox [{ref.field}] without a code")
            column = checkbox_column(field.name, ref.code)
        else:
            column = field.name
        target_event = event
        if ref.event and ref.event != "event-name":
            if "-" in ref.event:
                raise Unknown(f"event smart variable [{ref.event}]")
            target_event = ref.event
        if ref.instance and ref.instance not in ("current-instance",):
            raise Unknown(f"instance reference {ref.text}")
        if repeat_form and field.form == repeat_form and target_event == event:
            row = self.rows.get(self.current, {})
        else:
            row = self.rows.get((target_event, "", ""))
            if row is None:  # e.g. a classic project without event names
                row = self.rows.get(("", "", ""), {})
        return row.get(column, "")


def strip_html(text: str) -> str:
    """Remove HTML tags and tidy spaces (for codebooks and wording checks)."""
    text = re.sub(r"<br\s*/?>", " ", text or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
            .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", text).strip()
