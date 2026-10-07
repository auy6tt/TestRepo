#!/usr/bin/env python3
"""
Make a FAKE REDCap export (raw CSV) from a data dictionary, for testing.

Use it to test the cleaning script, to show a client what their export will look like,
or to import test records into a development copy of their project. Every value is
random and made up: no real person is behind any row. The script follows validation
limits, choice codes and branching logic, works out calculated fields, and can add
deliberate mistakes (listed in an "answer key") so you can prove the cleaning script
finds them.

Usage (from the kit folder):
    python scripts/make_fake_export.py --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
        --events samples/02_redcap/instrument_event_mapping.csv \
        --repeating samples/02_redcap/repeating_instruments.csv \
        --event-days samples/02_redcap/events.csv \
        --event-logic "visit_*=[screening_arm_1][fu_agree] = '1'" \
        --repeat-logic "health_event=[fu_health_event] = '1'" \
        --records 24 --errors 8 --seed 7 --today 2026-10-07 \
        --out samples/05_test_data/fake_export.csv

Only needs the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redcap_dictionary as rd  # noqa: E402
import redcap_logic as rl  # noqa: E402

# Name patterns -> realistic ranges. Edit these to suit a study; the dictionary's
# own min/max always win.
NUMBER_HINTS = [
    (r"(^|_)(sbp|systolic)", (100, 175)), (r"(^|_)(dbp|diastolic)", (60, 105)),
    (r"height", (150, 192)), (r"weight", (52, 110)), (r"(^|_)age($|_)", (18, 85)),
    (r"(^|_)(hr|pulse|heart_rate)", (55, 100)), (r"temp", (36.0, 38.5)),
]
ALWAYS_YES = re.compile(r"consent")  # fake people always consented, so no data exists without consent
LIKELY_YES = re.compile(r"agree|eligib|attended|took_place|signed")
LIKELY_NO = re.compile(r"event|adverse|hosp|admit|death|died|withdr")
DOB = re.compile(r"(^|_)dob($|_)|birth")


class Generator:
    def __init__(self, dd, event_map, repeating, event_days, event_logic, repeat_logic, seed, today,
                 start, max_instances):
        self.dd = dd
        self.event_map = event_map
        self.repeating = repeating or set()
        self.event_days = event_days
        self.event_logic = event_logic
        self.repeat_logic = repeat_logic
        self.random = random.Random(seed)
        self.today = today
        self.start = start
        self.max_instances = max_instances
        self.logic_cache = {}
        self.referenced = self.referenced_columns()

    # -- helpers -----------------------------------------------------------
    def parse(self, text):
        if text not in self.logic_cache:
            try:
                self.logic_cache[text] = rl.parse(text)[0]
            except rl.LogicError:
                self.logic_cache[text] = None
        return self.logic_cache[text]

    def evaluate(self, text, context, default=True):
        tree = self.parse(text)
        if tree is None:
            return default
        try:
            return rl.evaluate(tree, context.get)
        except rl.Unknown:
            return default

    def referenced_columns(self) -> set:
        """Export columns that logic or calculations depend on (left alone by error injection)."""
        found = set()
        texts = [f.branching for f in self.dd.fields if f.branching]
        texts += [f.choices_raw for f in self.dd.fields if f.ftype == "calc" and f.choices_raw]
        texts += [logic for _, logic in self.event_logic] + list(self.repeat_logic.values())
        for text in texts:
            tree = self.parse(text)
            if tree is None:
                continue
            for ref in rl.references(tree):
                field = self.dd.by_name.get(ref.field) if ref.field else None
                if field is None:
                    continue
                if field.ftype == "checkbox" and ref.code is not None:
                    found.add(rd.checkbox_column(field.name, ref.code))
                else:
                    found.update(field.export_columns())
        return found

    def events(self):
        return self.event_map.events if self.event_map else [""]

    def forms_for(self, event):
        if not self.event_map:
            return list(self.dd.forms)
        return [f for f in self.dd.forms if f in self.event_map.forms_by_event.get(event, [])]

    def is_repeating(self, event, form):
        return (event, form) in self.repeating or ("", form) in self.repeating

    # -- values ------------------------------------------------------------
    def number_range(self, f):
        low = high = None
        try:
            low = float(f.vmin) if f.vmin else None
            high = float(f.vmax) if f.vmax else None
        except ValueError:
            pass
        for pattern, (a, b) in NUMBER_HINTS:
            if re.search(pattern, f.name):
                low = max(a, low) if low is not None else a
                high = min(b, high) if high is not None else b
                break
        low = 0 if low is None else low
        high = low + 100 if high is None else high
        return low, max(low, high)

    def date_limits(self, f):
        def limit(text, fallback):
            if not text:
                return fallback
            if text.lower() in ("today", "now"):
                return self.today
            try:
                return dt.date.fromisoformat(text[:10])
            except ValueError:
                return fallback
        return limit(f.vmin, dt.date(1900, 1, 1)), limit(f.vmax, dt.date(2100, 1, 1))

    def value(self, f, anchor: dt.date, number: int) -> str:
        r = self.random
        if f.ftype in ("radio", "dropdown"):
            codes = [c for c, _ in f.choices]
            usual = [c for c in codes if c not in ("98", "99", "-99", "88", "-88")] or codes
            return r.choice(codes if r.random() < 0.08 else usual)
        if f.ftype in ("yesno", "truefalse"):
            if ALWAYS_YES.search(f.name):
                return "1"
            chance = 0.85 if LIKELY_YES.search(f.name) else (0.25 if LIKELY_NO.search(f.name) else 0.5)
            return "1" if r.random() < chance else "0"
        if f.ftype == "slider":
            low = int(f.vmin) if f.vmin.lstrip("-").isdigit() else 0
            high = int(f.vmax) if f.vmax.lstrip("-").isdigit() else 100
            return str(r.randint(low, high))
        if f.ftype == "notes":
            return "" if r.random() < 0.7 else "Fake note for testing."
        if f.ftype != "text":
            return ""
        kind = f.validation_kind
        if kind == "integer":
            low, high = self.number_range(f)
            return str(r.randint(int(round(low)), int(round(high))))
        if kind in ("number", "number_comma"):
            low, high = self.number_range(f)
            places = int(f.validation[7]) if re.match(r"number_\ddp", f.validation) else 1
            text = f"{r.uniform(low, high):.{places}f}"
            return text.replace(".", ",") if kind == "number_comma" else text
        if kind in ("date", "datetime", "datetime_seconds"):
            low, high = self.date_limits(f)
            if DOB.search(f.name) or re.search(r"date of birth", f.label, re.I):
                day = anchor - dt.timedelta(days=r.randint(18 * 365 + 5, 85 * 365))
            else:
                day = anchor
            day = min(max(day, low), high)
            if kind == "date":
                return day.isoformat()
            text = f"{day.isoformat()} {r.randint(8, 17):02d}:{r.choice([0, 15, 30, 45]):02d}"
            return text + (":00" if kind == "datetime_seconds" else "")
        if kind == "time":
            return f"{r.randint(8, 17):02d}:{r.choice([0, 15, 30, 45]):02d}"
        if kind == "email":
            return f"participant{number}@example.org"
        if kind == "phone" or re.search(r"phone|mobile", f.name):
            return f"555-01{r.randint(0, 99):02d}"
        if kind == "postcode":
            return "99999"
        if kind == "letters":
            return "Fake"
        if kind == "mrn":
            return f"{9000000000 + number}"
        return f"Fake answer {number}"

    def fill_row(self, row, forms, context, anchor, number):
        for form in forms:
            filled_any = False
            for f in self.dd.form_fields(form):
                if f is self.dd.fields[0] or f.ftype in ("descriptive", "file", "sql"):
                    continue
                shown = True if not f.branching else self.evaluate(f.branching, context)
                if f.ftype == "calc":
                    tree = self.parse(f.choices_raw)
                    value = ""
                    if tree is not None:
                        try:
                            value = rl.format_number(rl.evaluate(tree, context.get))
                        except rl.Unknown:
                            value = ""
                    row[f.name] = value
                    continue
                if f.ftype == "checkbox":
                    none_codes = [arg for tag, arg in rd.action_tags(f.annotation) if tag == "@NONEOFTHEABOVE"]
                    none_codes = [c.strip() for codes in none_codes for c in codes.split(",")]
                    ticked = set()
                    if shown:
                        for code, _ in f.choices:
                            if code not in none_codes and self.random.random() < 0.3:
                                ticked.add(code)
                        if not ticked and none_codes:
                            ticked.add(none_codes[0])
                        filled_any = True
                    for code, _ in f.choices:
                        row[rd.checkbox_column(f.name, code)] = ("1" if code in ticked else "0") if shown else "0"
                    continue
                if not shown:
                    row[f.name] = ""
                    continue
                if not f.is_required and f.ftype != "notes" and self.random.random() < 0.08:
                    row[f.name] = ""  # some optional questions are skipped
                    continue
                row[f.name] = self.value(f, anchor, number)
                filled_any = filled_any or row[f.name] != ""
            row[f"{form}_complete"] = "2" if filled_any else "0"

    def make(self, records: int) -> tuple[list, list]:
        header = self.dd.export_header(longitudinal=bool(self.event_map), repeating=bool(self.repeating))
        id_field = self.dd.fields[0].name
        out_rows = []
        for n in range(1, records + 1):
            record_id = str(n)
            start = self.start + dt.timedelta(days=self.random.randint(0, 60))
            rows = {}
            for event in self.events():
                key = (event, "", "")
                context = rd.RecordContext(self.dd, record_id, rows, key)
                if event and event != self.events()[0]:
                    rules = [logic for pattern, logic in self.event_logic if fnmatch.fnmatch(event, pattern)]
                    if any(not self.evaluate(logic, context, default=True) for logic in rules):
                        continue
                offset = self.event_days.get(event, 30 * self.events().index(event))
                anchor = min(start + dt.timedelta(days=offset + self.random.randint(-3, 3)), self.today)
                base = {c: "" for c in header}
                base[id_field] = record_id
                if self.event_map:
                    base["redcap_event_name"] = event
                rows[key] = base
                forms = self.forms_for(event)
                self.fill_row(base, [f for f in forms if not self.is_repeating(event, f)], context, anchor, n)
                for form in [f for f in forms if self.is_repeating(event, f)]:
                    logic = self.repeat_logic.get(form)
                    if logic is not None:
                        count = self.random.randint(1, self.max_instances) if self.evaluate(logic, context, False) else 0
                    else:
                        count = self.random.randint(0, self.max_instances)
                    for instance in range(1, count + 1):
                        rkey = (event, form, str(instance))
                        row = {c: "" for c in header}
                        row[id_field] = record_id
                        if self.event_map:
                            row["redcap_event_name"] = event
                        row["redcap_repeat_instrument"] = form
                        row["redcap_repeat_instance"] = str(instance)
                        rows[rkey] = row
                        rcontext = rd.RecordContext(self.dd, record_id, rows, rkey)
                        event_anchor = anchor - dt.timedelta(days=self.random.randint(1, 20))
                        self.fill_row(row, [form], rcontext, event_anchor, n)
            out_rows += list(rows.values())
        return header, out_rows

    # -- deliberate mistakes -----------------------------------------------
    def inject(self, rows, count, header):
        """Add `count` deliberate mistakes. Returns answer-key rows."""
        id_field = self.dd.fields[0].name
        key_rows = []
        kinds = ["out_of_range", "invalid_code", "missing_required", "bad_date", "not_a_number",
                 "hidden_has_value", "calc_mismatch", "none_of_the_above_conflict"]
        by_record = {}
        for row in rows:
            k = (row.get("redcap_event_name", ""), row.get("redcap_repeat_instrument", ""),
                 row.get("redcap_repeat_instance", ""))
            by_record.setdefault(row[id_field], {})[k] = row
        used = set()
        slot = 0
        while len(key_rows) < count and slot < count + 3 * len(kinds):
            kind = kinds[slot % len(kinds)]
            slot += 1
            for _ in range(300):  # try up to 300 random rows for this kind of mistake
                found = self.try_inject(kind, self.random.choice(rows), by_record, used, id_field)
                if found:
                    key_rows.append(found)
                    break
        return key_rows

    def try_inject(self, kind, row, by_record, used, id_field):
        """Try to add one mistake of this kind to this row. Returns an answer-key row or None."""
        record = row[id_field]
        event = row.get("redcap_event_name", "")
        repeat = row.get("redcap_repeat_instrument", "")
        instance = row.get("redcap_repeat_instance", "")
        forms = [repeat] if repeat else [f for f in self.forms_for(event) if not self.is_repeating(event, f)]
        started = [f for f in forms if row.get(f"{f}_complete") == "2"]
        candidates = [f for form in started for f in self.dd.form_fields(form)
                      if f.name not in self.referenced and f is not self.dd.fields[0]
                      and (record, event, instance, f.name) not in used]
        context = rd.RecordContext(self.dd, record, by_record[record], (event, repeat, instance))

        def shown(f):
            return True if not f.branching else self.evaluate(f.branching, context)

        choice = None
        if kind == "out_of_range":
            options = [f for f in candidates if f.validation_kind in ("integer", "number") and f.vmax
                       and row.get(f.name) and shown(f)]
            if options:
                f = self.random.choice(options)
                choice = (f, str(int(float(f.vmax)) + max(1, int((float(f.vmax) - float(f.vmin or 0)) * 0.2))),
                          f"above the maximum ({f.vmax})")
        elif kind == "invalid_code":
            options = [f for f in candidates if f.ftype in ("radio", "dropdown") and row.get(f.name)]
            if options:
                f = self.random.choice(options)
                choice = (f, "7" if "7" not in f.choice_map else "77", "not one of the choice codes")
        elif kind == "missing_required":
            options = [f for f in candidates if f.is_required and f.ftype not in ("checkbox", "calc")
                       and row.get(f.name) and shown(f)]
            if options:
                f = self.random.choice(options)
                choice = (f, "", "required but blank")
        elif kind == "bad_date":
            options = [f for f in candidates if f.validation_kind == "date" and row.get(f.name)]
            if options:
                f = self.random.choice(options)
                choice = (f, row[f.name][:5] + "02-30", "not a real date")
        elif kind == "not_a_number":
            options = [f for f in candidates if f.validation_kind == "integer" and row.get(f.name) and shown(f)]
            if options:
                f = self.random.choice(options)
                choice = (f, row[f.name] + ".5", "not a whole number")
        elif kind == "hidden_has_value":
            options = [f for f in candidates if f.branching and not row.get(f.name) and not shown(f)
                       and f.ftype in ("text", "radio", "dropdown", "yesno") and f.ftype != "calc"]
            if options:
                f = self.random.choice(options)
                value = self.value(f, self.today, int(record)) if f.ftype != "text" or f.validation else "Fake answer"
                choice = (f, value or "1", "has a value although its branching logic hides it")
        elif kind == "calc_mismatch":
            options = [f for f in candidates if f.ftype == "calc" and rl.is_number(row.get(f.name, ""))]
            if options:
                f = self.random.choice(options)
                choice = (f, rl.format_number(float(row[f.name]) + 5), "stored value differs from the formula")
        elif kind == "none_of_the_above_conflict":
            for f in candidates:
                if f.ftype != "checkbox":
                    continue
                codes = [c.strip() for tag, arg in rd.action_tags(f.annotation) if tag == "@NONEOFTHEABOVE"
                         for c in arg.split(",") if c.strip()]
                if not codes:
                    continue
                others = [c for c, _ in f.choices if c not in codes
                          and rd.checkbox_column(f.name, c) not in self.referenced]
                if others:
                    other = self.random.choice(others)
                    row[rd.checkbox_column(f.name, codes[0])] = "1"
                    row[rd.checkbox_column(f.name, other)] = "1"
                    used.add((record, event, instance, f.name))
                    return [record, event, repeat, instance, f.name, f"{codes[0]} and {other} ticked",
                            kind, "'none of these' ticked together with another option"]
            return None
        if choice:
            f, value, description = choice
            row[f.name] = value
            used.add((record, event, instance, f.name))
            return [record, event, repeat, instance, f.name, value, kind, description]
        return None

    def recalculate(self, rows, record, changed_field):
        """Recompute calculated fields that use `changed_field` for one record (as REDCap does on save)."""
        id_field = self.dd.fields[0].name
        record_rows = {}
        for row in rows:
            if row[id_field] == record:
                key = (row.get("redcap_event_name", ""), row.get("redcap_repeat_instrument", ""),
                       row.get("redcap_repeat_instance", ""))
                record_rows[key] = row
        for key, row in record_rows.items():
            context = rd.RecordContext(self.dd, record, record_rows, key)
            for f in self.dd.fields:
                if f.ftype != "calc" or f.name not in row:
                    continue
                tree = self.parse(f.choices_raw)
                if tree is None or changed_field not in {r.field for r in rl.references(tree)}:
                    continue
                if key[1] and f.form != key[1]:
                    continue
                if not any(row.get(g.name) for g in self.dd.form_fields(f.form) if g.ftype != "calc"):
                    continue
                try:
                    row[f.name] = rl.format_number(rl.evaluate(tree, context.get))
                except rl.Unknown:
                    pass


def parse_assignments(items, what):
    pairs = []
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"ERROR: {what} must look like NAME=LOGIC, got: {item}")
        name, logic = item.split("=", 1)
        pairs.append((name.strip(), logic.strip()))
    return pairs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Make a fake REDCap raw export from a data dictionary.")
    parser.add_argument("--dictionary", required=True)
    parser.add_argument("--events", help="instrument-event mapping CSV (longitudinal projects)")
    parser.add_argument("--repeating", help="repeating instruments CSV (event_name, form_name, custom_form_label)")
    parser.add_argument("--event-days", help="events CSV with unique_event_name and day_offset columns")
    parser.add_argument("--event-logic", action="append",
                        help="only create matching events when the logic is true, e.g. "
                             "\"visit_*=[screening_arm_1][fu_agree] = '1'\" (can repeat)")
    parser.add_argument("--repeat-logic", action="append",
                        help="only add repeat instances of a form when the logic is true, e.g. "
                             "\"health_event=[fu_health_event] = '1'\" (can repeat)")
    parser.add_argument("--max-instances", type=int, default=2, help="most repeat instances per event (default 2)")
    parser.add_argument("--records", type=int, default=20)
    parser.add_argument("--errors", type=int, default=0, help="number of deliberate mistakes to add")
    parser.add_argument("--set", action="append", dest="sets",
                        help="force a value: RECORD:EVENT:FIELD=VALUE (event may be empty), e.g. 3:screening_arm_1:scr_dbp=150")
    parser.add_argument("--seed", type=int, default=1, help="random seed (same seed = same file)")
    parser.add_argument("--today", help="date to treat as today, YYYY-MM-DD (default: real today)")
    parser.add_argument("--start", help="earliest first-visit date, YYYY-MM-DD (default: 120 days before today)")
    parser.add_argument("--out", required=True, help="CSV file to write")
    parser.add_argument("--answer-key", help="CSV listing the deliberate mistakes (default: OUT_answer_key.csv)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # never crash on unusual characters

    dd, issues = rd.load_dictionary(args.dictionary)
    errors = [i for i in issues if i.level == "ERROR"]
    if dd is None or not dd.header_ok or errors:
        for issue in errors or issues:
            print(f"{issue.level}: {issue.message}")
        print("Fix the dictionary first (run validate_redcap.py).")
        return 2
    event_map = rd.load_event_map(args.events)[0] if args.events else None
    repeating = rd.load_repeating(args.repeating)[0] if args.repeating else set()
    event_days = {}
    if args.event_days:
        with open(args.event_days, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                name = row.get("unique_event_name", "").strip()
                if name and row.get("day_offset", "").strip().lstrip("-").isdigit():
                    event_days[name] = int(row["day_offset"])
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    rl.set_today(today)
    start = dt.date.fromisoformat(args.start) if args.start else today - dt.timedelta(days=120)
    generator = Generator(dd, event_map, repeating, event_days, parse_assignments(args.event_logic, "--event-logic"),
                          dict(parse_assignments(args.repeat_logic, "--repeat-logic")), args.seed, today, start,
                          args.max_instances)
    header, rows = generator.make(args.records)
    key_rows = generator.inject(rows, args.errors, header) if args.errors else []
    id_field = dd.fields[0].name
    for item in args.sets or []:
        target, _, value = item.partition("=")
        parts = target.split(":")
        if len(parts) != 3:
            raise SystemExit(f"ERROR: --set must look like RECORD:EVENT:FIELD=VALUE, got: {item}")
        record, event, field = parts
        matches = [r for r in rows if r[id_field] == record and r.get("redcap_event_name", "") == event
                   and not r.get("redcap_repeat_instrument")]
        if not matches or field not in header:
            raise SystemExit(f"ERROR: --set target not found: {item}")
        matches[0][field] = value
        generator.recalculate(rows, record, field)
        key_rows.append([record, event, "", "", field, value, "manual", "value set with --set"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    key_path = Path(args.answer_key) if args.answer_key else out.with_name(out.stem + "_answer_key.csv")
    with open(key_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([id_field, "redcap_event_name", "redcap_repeat_instrument", "redcap_repeat_instance",
                         "field", "value_written", "mistake", "description"])
        writer.writerows(key_rows)
    records = len({r[id_field] for r in rows})
    print(f"Wrote {out}: {len(rows)} rows for {records} fake records ({len(header)} columns).")
    print(f"Wrote {key_path}: {len(key_rows)} deliberate mistake(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
