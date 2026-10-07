#!/usr/bin/env python3
"""
Clean and check a REDCap export (raw CSV) against its data dictionary.

THIS IS A TEMPLATE. Copy it for each study and adjust the study-specific settings
below or pass a rules file. It only needs the Python standard library, so the client
can run it on their own computer without installing anything.

What it does:
  * writes a copy of the data with codes replaced by labels (1 -> "Yes")
  * checks every value against the dictionary: choice codes, whole numbers, dates,
    min/max limits, email/time formats
  * lists required questions left blank, but only where the question was actually
    shown (branching logic is evaluated for each record) and the form was started
  * finds values in questions that branching logic hides, calculated fields that do
    not match their formula, 'none of these' ticked with other options, forms marked
    Complete with no data, duplicate rows, and data in forms not used at that event
  * runs your own checks from a rules file (CSV with columns: rule, logic). Write the
    logic in REDCap syntax; a row is flagged when the logic is TRUE, as in REDCap's
    Data Quality module. Example: "[scr_dbp] >= [scr_sbp]"

Only run it on exports the client is allowed to process. Freelancers: test it on FAKE
data (make_fake_export.py) and hand it to the client to run on the real export.

Usage (from the kit folder):
    python scripts/clean_export.py --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
        --export samples/05_test_data/fake_export.csv \
        --events samples/02_redcap/instrument_event_mapping.csv \
        --rules samples/05_test_data/cleaning_rules.csv --outdir samples/06_cleaning_output

Outputs in --outdir (NAME = the export file name):
    NAME_labelled.csv          the data with labels instead of codes
    NAME_issues.csv            one row per problem, ready to send to the study team as queries
    NAME_cleaning_report.txt   a readable summary
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redcap_dictionary as rd  # noqa: E402
import redcap_logic as rl  # noqa: E402

# ---------------------------------------------------------------------------
# STUDY-SPECIFIC SETTINGS (edit for each study)
# ---------------------------------------------------------------------------
# Codes that mean "missing on purpose" and should not be treated as invalid,
# e.g. {"-99", "-98"} if the project uses REDCap's missing data codes.
MISSING_CODES: set[str] = set()
# How close a stored calculated value must be to the formula's result.
CALC_TOLERANCE = 1e-6
# ---------------------------------------------------------------------------

ISSUE_TYPES = {
    "missing_required": "Required question left blank although it was shown",
    "hidden_has_value": "Has a value although branching logic hides the question",
    "invalid_code": "Value is not one of the question's codes",
    "invalid_checkbox": "Checkbox column is not 0 or 1",
    "not_a_number": "Not a valid number for this question",
    "out_of_range": "Outside the min/max limits in the dictionary",
    "bad_date": "Not a valid date or time in the export format",
    "bad_format": "Does not match the question's validation (email, time, letters...)",
    "calc_mismatch": "Stored calculated value differs from its formula",
    "none_of_the_above_conflict": "'None of these' ticked together with other options",
    "complete_but_empty": "Form marked Complete but has no data",
    "duplicate_row": "The same record, event and instance appear more than once",
    "form_not_in_event": "Data in a form that is not used at this event",
    "unknown_event": "Event name is not in the event mapping",
    "custom_rule": "Flagged by a study-specific rule",
}
SYSTEM_COLUMNS = set(rd.REDCAP_EXTRA_COLUMNS)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Cleaner:
    def __init__(self, dd, event_map=None, rules=None, today=None):
        self.dd = dd
        self.event_map = event_map
        self.rules = rules or []
        self.today = today or dt.date.today()
        self.id_field = dd.fields[0].name
        self.issues = []
        self.not_checked = defaultdict(set)   # reason -> field names
        self.trees = {}
        self.columns = {}                     # export column -> (Field, checkbox code or None)
        for f in dd.fields:
            if f.ftype == "checkbox":
                for code, _ in f.choices:
                    self.columns[rd.checkbox_column(f.name, code)] = (f, code)
            elif f.ftype != "descriptive":
                self.columns[f.name] = (f, None)
        self.form_status = {f"{form}_complete": form for form in dd.forms}
        self.stats = {"not_started": Counter(), "status": defaultdict(Counter), "rows_per_event": Counter(),
                      "records_per_event": defaultdict(set)}

    # -- helpers -----------------------------------------------------------
    def tree(self, text):
        if text not in self.trees:
            try:
                self.trees[text] = rl.parse(text)[0]
            except rl.LogicError:
                self.trees[text] = None
        return self.trees[text]

    def add(self, key, form, field, value, issue, detail):
        record, event, repeat, instance = key
        self.issues.append({self.id_field: record, "redcap_event_name": event, "redcap_repeat_instrument": repeat,
                            "redcap_repeat_instance": instance, "form": form, "field": field, "value": value,
                            "issue": issue, "detail": detail})

    def limit(self, text, kind):
        if not text:
            return None
        try:
            if kind in ("integer", "number"):
                return float(text)
            if kind == "number_comma":
                return float(text.replace(",", "."))
            if kind == "date":
                return self.today if text.lower() == "today" else dt.date.fromisoformat(text)
            if kind in ("datetime", "datetime_seconds"):
                if text.lower() in ("now", "today"):
                    return dt.datetime.combine(self.today, dt.time(23, 59, 59))
                return dt.datetime.fromisoformat(text)
        except ValueError:
            return None
        return None

    # -- main --------------------------------------------------------------
    def run(self, header, rows):
        if self.id_field not in header:
            raise SystemExit(f"ERROR: the export has no '{self.id_field}' column (the record ID field).")
        known = set(self.columns) | SYSTEM_COLUMNS | set(self.form_status) | {f"{f}_timestamp" for f in self.dd.forms}
        self.unknown_columns = [c for c in header if c not in known]
        self.missing_columns = [c for c in self.columns if c not in header]
        repeat_pairs = {(r.get("redcap_event_name", ""), r.get("redcap_repeat_instrument", ""))
                        for r in rows if r.get("redcap_repeat_instrument")}
        by_record = defaultdict(dict)
        for row in rows:
            key = (row.get(self.id_field, ""), row.get("redcap_event_name", ""),
                   row.get("redcap_repeat_instrument", ""), row.get("redcap_repeat_instance", ""))
            if key[1:] in by_record[key[0]]:
                self.add(key, "", "", "", "duplicate_row", "This record/event/instance appears more than once.")
                continue
            by_record[key[0]][key[1:]] = row
        for record, record_rows in by_record.items():
            for sub_key, row in record_rows.items():
                self.check_row((record,) + sub_key, row, record_rows, repeat_pairs)
        return self.issues

    def forms_in_row(self, event, repeat, repeat_pairs):
        if repeat:
            return [repeat]
        if self.event_map and event:
            designated = self.event_map.forms_by_event.get(event, [])
        else:
            designated = self.dd.forms
        return [f for f in self.dd.forms if f in designated and (event, f) not in repeat_pairs]

    def check_row(self, key, row, record_rows, repeat_pairs):
        record, event, repeat, instance = key
        self.stats["rows_per_event"][event or "(all)"] += 1
        self.stats["records_per_event"][event or "(all)"].add(record)
        if not record:
            self.add(key, "", self.id_field, "", "missing_required", "Row has no record ID.")
            return
        if self.event_map and event and event not in self.event_map.forms_by_event:
            self.add(key, "", "redcap_event_name", event, "unknown_event", "Event is not in the event mapping file.")
            return
        forms = self.forms_in_row(event, repeat, repeat_pairs)
        if self.event_map and event and not repeat:
            for form in self.dd.forms:
                if form in forms or (event, form) in repeat_pairs:
                    continue
                filled = [c for f in self.dd.form_fields(form) if f is not self.dd.fields[0]
                          for c in f.export_columns()
                          if row.get(c, "") != "" and not (f.ftype == "checkbox" and row.get(c) == "0")]
                if filled:
                    self.add(key, form, filled[0], row.get(filled[0], ""), "form_not_in_event",
                             f"Form '{form}' is not designated to {event} but has data ({len(filled)} value(s)).")
        context = rd.RecordContext(self.dd, record, record_rows, (event, repeat, instance))
        for form in forms:
            self.check_form(key, form, row, context)
        self.check_rules(key, row, forms, context)

    def check_form(self, key, form, row, context):
        fields = [f for f in self.dd.form_fields(form) if f.ftype != "descriptive" and f is not self.dd.fields[0]]
        status = row.get(f"{form}_complete", "")
        event = key[1] or "(all)"
        self.stats["status"][(form, event)][rd.FORM_STATUS.get(status, status or "blank")] += 1
        started = any(self.has_value(f, row) for f in fields if f.ftype != "calc")
        if not started:
            self.stats["not_started"][(form, event)] += 1
            if status == "2":
                self.add(key, form, f"{form}_complete", status, "complete_but_empty",
                         "Form is marked Complete but no question has an answer.")
            return
        for f in fields:
            shown = True
            if f.branching:
                tree = self.tree(f.branching)
                if tree is None:
                    self.not_checked["branching logic could not be read"].add(f.name)
                else:
                    try:
                        shown = rl.truthy(rl.evaluate(tree, context.get))
                    except rl.Unknown as exc:
                        self.not_checked[f"branching logic uses something this script cannot look up ({exc})"].add(f.name)
            if f.ftype == "calc":
                self.check_calc(key, form, f, row, context)
                continue
            if self.has_value(f, row):
                self.check_values(key, form, f, row)
                if not shown:
                    shown_value = self.display_value(f, row)
                    self.add(key, form, f.name, shown_value, "hidden_has_value",
                             f"Branching logic hides this question ({f.branching}) but it has a value.")
            elif shown and f.is_required:
                why = f" (shown because {rl.describe(self.tree(f.branching), self.dd.by_name)})" \
                    if f.branching and self.tree(f.branching) is not None else ""
                self.add(key, form, f.name, "", "missing_required", f"Required question is blank{why}.")

    def has_value(self, f, row) -> bool:
        if f.ftype == "checkbox":
            return any(row.get(rd.checkbox_column(f.name, code), "") not in ("", "0") for code, _ in f.choices)
        return row.get(f.name, "").strip() != ""

    def display_value(self, f, row) -> str:
        if f.ftype == "checkbox":
            return ", ".join(code for code, _ in f.choices if row.get(rd.checkbox_column(f.name, code)) == "1")
        return row.get(f.name, "")

    def check_values(self, key, form, f, row):
        value = row.get(f.name, "").strip()
        if f.ftype == "checkbox":
            ticked = []
            for code, _ in f.choices:
                cell = row.get(rd.checkbox_column(f.name, code), "")
                if cell not in ("", "0", "1"):
                    self.add(key, form, rd.checkbox_column(f.name, code), cell, "invalid_checkbox",
                             "Checkbox columns should only hold 0 or 1.")
                if cell == "1":
                    ticked.append(code)
            for tag, arg in rd.action_tags(f.annotation):
                if tag == "@NONEOFTHEABOVE":
                    none_codes = {c.strip() for c in arg.split(",") if c.strip()}
                    if ticked and set(ticked) & none_codes and set(ticked) - none_codes:
                        labels = "; ".join(f.choice_map.get(c, c) for c in ticked)
                        self.add(key, form, f.name, ", ".join(ticked), "none_of_the_above_conflict",
                                 f"Ticked together: {labels}.")
            return
        if value in MISSING_CODES:
            return
        if f.ftype in ("radio", "dropdown", "yesno", "truefalse"):
            if value not in f.choice_map:
                self.add(key, form, f.name, value, "invalid_code",
                         f"Allowed codes: {', '.join(f.choice_map)}.")
            return
        if f.ftype == "slider":
            number = rl.to_number(value)
            low = float(f.vmin) if rl.is_number(f.vmin) else 0.0
            high = float(f.vmax) if rl.is_number(f.vmax) else 100.0
            if number is None:
                self.add(key, form, f.name, value, "not_a_number", "Slider values are whole numbers.")
            elif not low <= number <= high:
                self.add(key, form, f.name, value, "out_of_range", f"Slider range is {low:g} to {high:g}.")
            return
        if f.ftype != "text" or not f.validation:
            return
        kind = f.validation_kind
        if kind == "integer":
            if not re.fullmatch(r"-?\d+", value):
                self.add(key, form, f.name, value, "not_a_number", "Should be a whole number.")
                return
            self.check_range(key, form, f, value, float(value), kind)
        elif kind in ("number", "number_comma"):
            number = rl.to_number(value.replace(",", ".") if kind == "number_comma" else value)
            if number is None:
                self.add(key, form, f.name, value, "not_a_number", "Should be a number.")
                return
            self.check_range(key, form, f, value, number, kind)
        elif kind == "date":
            try:
                day = dt.date.fromisoformat(value) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None
            except ValueError:
                day = None
            if day is None:
                self.add(key, form, f.name, value, "bad_date", "Should be a real date written YYYY-MM-DD.")
                return
            self.check_range(key, form, f, value, day, kind)
        elif kind in ("datetime", "datetime_seconds"):
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}" + (":\\d{2}" if kind == "datetime_seconds" else "")
            try:
                when = dt.datetime.fromisoformat(value) if re.fullmatch(pattern, value) else None
            except ValueError:
                when = None
            if when is None:
                self.add(key, form, f.name, value, "bad_date", "Should be a real date and time, YYYY-MM-DD HH:MM.")
                return
            self.check_range(key, form, f, value, when, kind)
        elif kind in ("time", "time_hms", "time_ms"):
            pattern = {"time": r"([01]\d|2[0-3]):[0-5]\d", "time_hms": r"([01]\d|2[0-3]):[0-5]\d:[0-5]\d",
                       "time_ms": r"[0-5]\d:[0-5]\d"}[kind]
            if not re.fullmatch(pattern, value):
                self.add(key, form, f.name, value, "bad_date", "Not a valid time for this question.")
        elif kind == "email" and not EMAIL.match(value):
            self.add(key, form, f.name, value, "bad_format", "Not a valid email address.")
        elif kind == "letters" and not re.fullmatch(r"[^\W\d_]+([ '\-][^\W\d_]+)*", value):
            self.add(key, form, f.name, value, "bad_format", "Should contain letters only.")

    def check_range(self, key, form, f, text, value, kind):
        low, high = self.limit(f.vmin, kind), self.limit(f.vmax, kind)
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            low = low.date() if isinstance(low, dt.datetime) else low
            high = high.date() if isinstance(high, dt.datetime) else high
        if low is not None and value < low:
            self.add(key, form, f.name, text, "out_of_range", f"Below the minimum ({f.vmin}).")
        elif high is not None and value > high:
            self.add(key, form, f.name, text, "out_of_range",
                     f"Above the maximum ({f.vmax}{' = ' + self.today.isoformat() if f.vmax.lower() in ('today', 'now') else ''}).")

    def check_calc(self, key, form, f, row, context):
        tree = self.tree(f.choices_raw)
        if tree is None:
            self.not_checked["calculation could not be read"].add(f.name)
            return
        try:
            expected = rl.evaluate(tree, context.get)
        except rl.Unknown as exc:
            self.not_checked[f"calculation uses something this script cannot look up ({exc})"].add(f.name)
            return
        stored = row.get(f.name, "").strip()
        expected_text = rl.format_number(expected)
        if stored == expected_text:
            return
        if stored and expected_text and rl.is_number(stored) and rl.is_number(expected_text):
            places = len(stored.split(".")[1]) if "." in stored else 0
            if abs(round(float(expected_text), places) - float(stored)) <= CALC_TOLERANCE * max(1.0, abs(float(stored))):
                return
        self.add(key, form, f.name, stored, "calc_mismatch",
                 f"Formula gives {expected_text or 'blank'} ({f.choices_raw}). Re-save the form or run "
                 "REDCap's Data Quality rule H to update it.")

    def check_rules(self, key, row, forms, context):
        form_fields = {f.name for form in forms for f in self.dd.form_fields(form)}
        for name, logic, tree in self.rules:
            if tree is None:
                continue
            used = [r.field for r in rl.references(tree) if r.field and not r.event]
            here = [u for u in used if u in form_fields]
            if not here:
                continue
            try:
                flagged = rl.truthy(rl.evaluate(tree, context.get))
            except rl.Unknown as exc:
                self.not_checked[f"rule '{name}' uses something this script cannot look up ({exc})"].add(here[0])
                continue
            if flagged:
                values = ", ".join(f"{u}={row.get(u, '')}" for u in dict.fromkeys(here))
                field = self.dd.by_name[here[0]]
                self.add(key, field.form, here[0], values, "custom_rule", name)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def label_rows(dd, header, rows, drop_identifiers=False):
    columns = {}
    for f in dd.fields:
        if f.ftype == "checkbox":
            for code, _ in f.choices:
                columns[rd.checkbox_column(f.name, code)] = f
        elif f.ftype != "descriptive":
            columns[f.name] = f
    status_columns = {f"{form}_complete" for form in dd.forms}
    drop = set()
    if drop_identifiers:
        drop = {c for c, f in columns.items() if f.is_identifier}
    out_header = [c for c in header if c not in drop]
    out = []
    for row in rows:
        new = {}
        for column in out_header:
            value = row.get(column, "")
            f = columns.get(column)
            if value != "" and f is not None:
                if f.ftype == "checkbox":
                    value = {"1": "Checked", "0": "Unchecked"}.get(value, value)
                elif f.ftype in rd.CATEGORICAL_TYPES:
                    value = rd.strip_html(f.choice_map.get(value, value))
            elif value != "" and column in status_columns:
                value = rd.FORM_STATUS.get(value, value)
            new[column] = value
        out.append(new)
    return out_header, out


def sort_issues(issues, dd, event_map, id_field):
    event_order = {e: i for i, e in enumerate(event_map.events)} if event_map else {}
    field_order = {f.name: i for i, f in enumerate(dd.fields)}

    def key(issue):
        record = issue[id_field]
        number = int(record) if record.isdigit() else 10 ** 9
        instance = issue["redcap_repeat_instance"]
        return (number, record, event_order.get(issue["redcap_event_name"], 99), issue["redcap_repeat_instrument"],
                int(instance) if instance.isdigit() else 0, field_order.get(issue["field"].split("___")[0], 9999))
    return sorted(issues, key=key)


def write_report(path, args, dd, cleaner, header, rows, issues, rules, outputs):
    records = {r.get(cleaner.id_field, "") for r in rows}
    lines = ["REDCap export cleaning report", "=============================", ""]
    lines.append(f"Export:      {Path(args.export).name} ({len(rows)} rows, {len(records)} records, {len(header)} columns)")
    lines.append(f"Dictionary:  {Path(args.dictionary).name}")
    if cleaner.event_map:
        lines.append(f"Events:      {', '.join(cleaner.event_map.events)}")
    if args.rules:
        lines.append(f"Rules:       {Path(args.rules).name} ({len(rules)} rule(s))")
    lines.append(f"Date limits: 'today' means {cleaner.today.isoformat()}")
    lines += ["", f"RESULT: {len(issues)} issue(s) to review" if issues else "RESULT: no issues found", ""]
    lines += ["Issues by type", "--------------"]
    counts = Counter(i["issue"] for i in issues)
    if not counts:
        lines.append("  None.")
    for issue_type, count in counts.most_common():
        lines.append(f"  {issue_type:<28}{count:>4}   {ISSUE_TYPES.get(issue_type, '')}")
    lines.append("")
    if cleaner.event_map or any(r.get("redcap_event_name") for r in rows):
        lines += ["Records per event", "-----------------"]
        for event, recs in cleaner.stats["records_per_event"].items():
            lines.append(f"  {event:<24}{len(recs):>4} record(s), {cleaner.stats['rows_per_event'][event]} row(s)")
        lines.append("")
    lines += ["Form status (rows checked)", "--------------------------"]
    events = list(cleaner.stats["rows_per_event"])
    order = sorted(cleaner.stats["status"], key=lambda k: (events.index(k[1]) if k[1] in events else 99,
                                                           dd.forms.index(k[0]) if k[0] in dd.forms else 99))
    for form, event in order:
        counter = cleaner.stats["status"][(form, event)]
        parts = ", ".join(f"{n} {label}" for label, n in counter.most_common())
        not_started = cleaner.stats["not_started"][(form, event)]
        lines.append(f"  {form} at {event}: {parts}" + (f"; {not_started} with no data yet" if not_started else ""))
    lines.append("")
    if cleaner.unknown_columns or cleaner.missing_columns:
        lines += ["Columns", "-------"]
        if cleaner.unknown_columns:
            lines.append("  In the export but not in the dictionary: " + ", ".join(cleaner.unknown_columns))
        if cleaner.missing_columns:
            shown = cleaner.missing_columns[:15]
            lines.append("  In the dictionary but not in the export: " + ", ".join(shown) +
                         (" ..." if len(cleaner.missing_columns) > 15 else "") + " (fine if the export was a subset)")
        lines.append("")
    lines += ["Issues", "------"]
    if not issues:
        lines.append("  None.")
    for issue in issues[:300]:
        where = f"Record {issue[cleaner.id_field]}"
        if issue["redcap_event_name"]:
            where += f", {issue['redcap_event_name']}"
        if issue["redcap_repeat_instrument"]:
            where += f", {issue['redcap_repeat_instrument']} #{issue['redcap_repeat_instance']}"
        if issue["issue"] == "custom_rule":
            lines.append(f"* {where}: {issue['value']}")
        else:
            value = f" = '{issue['value']}'" if issue["value"] != "" else ""
            lines.append(f"* {where}: {issue['field']}{value}")
        lines.append(f"    {issue['issue']}: {issue['detail']}")
    if len(issues) > 300:
        lines.append(f"  ... and {len(issues) - 300} more in the issues CSV.")
    lines.append("")
    if cleaner.not_checked:
        lines += ["Not checked automatically", "-------------------------"]
        for reason, names in cleaner.not_checked.items():
            lines.append(f"  {', '.join(sorted(names))}: {reason}")
        lines.append("")
    lines += ["Files written", "-------------"] + [f"  {p}" for p in outputs]
    lines += ["", "Each issue is a question for the study team, not an automatic correction. Fix values in",
              "REDCap itself (with a reason in the audit trail), then export and run this again."]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def load_rules(path):
    rules, problems = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for number, row in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            name, logic = row.get("rule", ""), row.get("logic", "")
            if not logic:
                continue
            try:
                tree = rl.parse(logic)[0]
            except rl.LogicError as exc:
                problems.append(f"Rules row {number} ('{name}') cannot be read: {exc.message}")
                tree = None
            rules.append((name or logic, logic, tree))
    return rules, problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Clean and check a REDCap raw CSV export against its data dictionary.")
    parser.add_argument("--dictionary", required=True, help="data dictionary CSV")
    parser.add_argument("--export", required=True, help="REDCap export, 'CSV / Microsoft Excel (raw data)'")
    parser.add_argument("--events", help="instrument-event mapping CSV (longitudinal projects)")
    parser.add_argument("--rules", help="CSV of study-specific checks with columns: rule, logic")
    parser.add_argument("--outdir", help="folder for the outputs (default: next to the export)")
    parser.add_argument("--today", help="date used for 'today' limits, YYYY-MM-DD (default: real today)")
    parser.add_argument("--drop-identifiers", action="store_true",
                        help="leave fields flagged as identifiers out of the labelled file")
    parser.add_argument("--fail-on-issues", action="store_true", help="exit with code 1 if any issue is found")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # never crash on unusual characters

    dd, problems = rd.load_dictionary(args.dictionary)
    errors = [p for p in problems if p.level == "ERROR"]
    if dd is None or not dd.header_ok or errors:
        for p in errors or problems:
            print(f"{p.level}: {p.message}")
        print("Fix the dictionary first (run validate_redcap.py).")
        return 2
    event_map = rd.load_event_map(args.events)[0] if args.events else None
    rules, rule_problems = load_rules(args.rules) if args.rules else ([], [])
    for problem in rule_problems:
        print("WARNING:", problem)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    rl.set_today(today)

    export = Path(args.export)
    with open(export, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = [{(k or "").strip(): (v or "") for k, v in row.items()} for row in reader]
    if not rows:
        print("ERROR: the export has no data rows.")
        return 2
    cleaner = Cleaner(dd, event_map, rules, today)
    issues = sort_issues(cleaner.run(header, rows), dd, event_map, cleaner.id_field)

    outdir = Path(args.outdir) if args.outdir else export.parent
    outdir.mkdir(parents=True, exist_ok=True)
    labelled_path = outdir / f"{export.stem}_labelled.csv"
    issues_path = outdir / f"{export.stem}_issues.csv"
    report_path = outdir / f"{export.stem}_cleaning_report.txt"
    out_header, labelled = label_rows(dd, header, rows, args.drop_identifiers)
    with open(labelled_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=out_header)
        writer.writeheader()
        writer.writerows(labelled)
    columns = [cleaner.id_field, "redcap_event_name", "redcap_repeat_instrument", "redcap_repeat_instance",
               "form", "field", "value", "issue", "detail"]
    with open(issues_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(issues)
    lines = write_report(report_path, args, dd, cleaner, header, rows, issues, rules,
                         [p.as_posix() for p in (labelled_path, issues_path, report_path)])
    for line in lines[:lines.index("Issues")]:
        print(line)
    print(f"Full list: {issues_path.as_posix()}  |  Report: {report_path.as_posix()}")
    return 1 if (args.fail_on_issues and issues) else 0


if __name__ == "__main__":
    sys.exit(main())
