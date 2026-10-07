"""
Helper module used by check_xlsform.py and make_codebook.py. You do not run it directly.

Reads the sheets of an XLSForm (.xlsx) into simple Python lists so the other
scripts can check them and describe them. Needs openpyxl (pip install openpyxl).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path

# Columns whose text is shown to people and can be translated (label::French (fr) ...)
TRANSLATABLE = {"label", "hint", "guidance_hint", "constraint_message", "required_message",
                "image", "audio", "video", "big-image", "media::image", "media::audio", "media::video"}

# Columns that hold XPath expressions
EXPRESSION_COLUMNS = ["relevant", "constraint", "calculation", "required", "choice_filter",
                      "default", "repeat_count", "trigger", "read_only", "readonly"]

QUESTION_TYPES = {
    "integer", "decimal", "range", "text", "select_one", "select_multiple", "select_one_from_file",
    "select_multiple_from_file", "rank", "note", "geopoint", "geotrace", "geoshape", "date", "time",
    "datetime", "image", "audio", "background-audio", "video", "file", "barcode", "calculate",
    "acknowledge", "hidden", "xml-external", "csv-external",
    "begin_group", "end_group", "begin_repeat", "end_repeat", "begin group", "end group",
    "begin repeat", "end repeat",
    # metadata
    "start", "end", "today", "deviceid", "phonenumber", "username", "email", "audit",
    "simserial", "subscriberid", "start-geopoint",
}
METADATA_TYPES = {"start", "end", "today", "deviceid", "phonenumber", "username", "email", "audit",
                  "simserial", "subscriberid", "start-geopoint", "background-audio"}
NO_LABEL_TYPES = METADATA_TYPES | {"calculate", "hidden", "end_group", "end_repeat", "end group",
                                   "end repeat", "xml-external", "csv-external"}


@dataclass
class Sheet:
    name: str
    header: list
    rows: list = dc_field(default_factory=list)   # list of dicts; key "_row" = spreadsheet row


@dataclass
class XLSForm:
    path: str
    sheets: dict
    languages: list

    @property
    def survey(self) -> list:
        return self.sheets["survey"].rows if "survey" in self.sheets else []

    @property
    def choices(self) -> list:
        return self.sheets["choices"].rows if "choices" in self.sheets else []

    @property
    def settings(self) -> dict:
        rows = self.sheets["settings"].rows if "settings" in self.sheets else []
        return {k: v for k, v in rows[0].items() if not k.startswith("_")} if rows else {}

    def choice_lists(self) -> dict:
        lists: dict = {}
        for row in self.choices:
            list_name = row.get("list_name", "") or row.get("list name", "")
            if list_name:
                lists.setdefault(list_name, []).append(row)
        return lists

    def text(self, row: dict, column: str, language: str | None = None) -> str:
        """Text of a translatable column in the chosen language (falls back sensibly)."""
        if language:
            value = row.get(f"{column}::{language}")
            if value:
                return value
        value = row.get(column)
        if value:
            return value
        for key, value in row.items():
            if key.startswith(column + "::") and value:
                return value
        return ""


def normalise_header(header: str) -> str:
    """'Label::English (en)' -> 'label::English (en)'; 'label:English' -> 'label::English'."""
    text = str(header or "").strip()
    if "::" in text:
        base, lang = text.split("::", 1)
        return base.strip().lower() + "::" + lang.strip()
    if ":" in text:
        base, lang = text.split(":", 1)
        if base.strip().lower() in TRANSLATABLE or base.strip().lower() == "media":
            return base.strip().lower() + "::" + lang.strip()
    return text.lower()


def cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_xlsform(path: str | Path) -> XLSForm:
    import openpyxl  # imported here so the error message is clear if it is missing

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = {}
    for ws in workbook.worksheets:
        name = ws.title.strip().lower()
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            sheets[name] = Sheet(name, [])
            continue
        header = [normalise_header(h) for h in rows[0]]
        sheet = Sheet(name, header)
        for number, row in enumerate(rows[1:], start=2):
            record = {}
            for i, key in enumerate(header):
                if key and i < len(row):
                    record[key] = cell_text(row[i])
            if not any(record.values()):
                continue
            record["_row"] = number
            sheet.rows.append(record)
        sheets[name] = sheet
    workbook.close()
    languages = []
    for sheet_name in ("survey", "choices"):
        for key in sheets.get(sheet_name, Sheet(sheet_name, [])).header:
            if "::" in key and key.split("::")[0] in ("label", "hint"):
                lang = key.split("::", 1)[1]
                if lang not in languages:
                    languages.append(lang)
    return XLSForm(str(path), sheets, languages)


def base_type(type_text: str) -> tuple[str, str]:
    """'select_one yesno' -> ('select_one', 'yesno'); 'integer' -> ('integer', '')."""
    parts = (type_text or "").strip().split()
    if not parts:
        return "", ""
    first = parts[0].lower()
    if first in ("begin", "end") and len(parts) > 1:
        return f"{first}_{parts[1].lower()}", ""
    if first in ("select_one", "select_multiple", "select_one_from_file", "select_multiple_from_file", "rank"):
        return first, " ".join(parts[1:])
    if first.startswith("select_one(") or first.startswith("select_multiple("):
        return first.split("(")[0], ""
    return first, " ".join(parts[1:])


REF = re.compile(r"\$\{([^}]*)\}")


def references(expression: str) -> list[str]:
    return [name.strip() for name in REF.findall(expression or "")]


if __name__ == "__main__":  # a helper module: running it (for example with --help) only shows this help
    print(__doc__.strip())
