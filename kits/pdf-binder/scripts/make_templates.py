#!/usr/bin/env python3
"""Create the spreadsheet templates in templates/.

  submittal-log.xlsx           track every submittal: dates, status, days in review
  binder-index-template.xlsx   the index that build_binder.py reads (also .csv)
  sds-site-list-template.xlsx  the on-site chemical list the client confirms

Run it again any time to restore clean copies:
  python scripts/make_templates.py
  python scripts/make_templates.py --out-dir somewhere/else

make_samples.py uses the same functions to fill in the sample files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

try:
    import xlsxwriter
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing package '{exc.name}'. Run: pip install -r requirements.txt")

import kitlib
from xlsxwriter.utility import xl_col_to_name

SUBMITTAL_TYPES = ["Product data", "Shop drawings", "Samples", "Calculations", "Certificates", "Test reports",
                   "O&M manual", "Warranty", "Record drawings", "Closeout", "Other"]
SUBMITTAL_STATUSES = ["Not submitted", "Submitted - under review", "Approved", "Approved as noted",
                      "Revise and resubmit", "Rejected", "For record only", "Closed"]
BALL_IN_COURT = ["Subcontractor", "General contractor", "Architect / engineer", "Owner"]

LOG_COLUMNS = [
    ("Submittal No.", 15), ("Rev", 5), ("Spec section", 11), ("Description", 42), ("Type", 15),
    ("Submitted to", 20), ("Date required", 11), ("Date submitted", 11), ("Date returned", 11),
    ("Status", 22), ("Days in review", 9), ("Late?", 7), ("Ball in court", 15), ("Next action", 30),
    ("Reviewer comments / notes", 42), ("File name", 34),
]
LOG_HEADER_ROW = 6          # zero-based row of the column headings (Excel row 7)
LOG_ROWS = 250


def _as_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value:
        return dt.date.fromisoformat(value)
    return None


def write_submittal_log(path, project: dict | None = None, rows: list[dict] | None = None,
                        today: dt.date | None = None, accent: str = kitlib.DEFAULT_ACCENT):
    """Write a submittal log. rows use the column names in LOG_COLUMNS."""
    today = today or dt.date.today()
    project = project or {}
    workbook = xlsxwriter.Workbook(str(path))
    f = kitlib.xlsx_formats(workbook, accent)
    log = workbook.add_worksheet("Submittal Log")
    summary = workbook.add_worksheet("Summary")
    lists = workbook.add_worksheet("Lists")

    # Lists for the drop-downs
    lists.set_column(0, 2, 28)
    for col, (title, values) in enumerate((("Type", SUBMITTAL_TYPES), ("Status", SUBMITTAL_STATUSES),
                                           ("Ball in court", BALL_IN_COURT))):
        lists.write(0, col, title, f["header"])
        for i, value in enumerate(values, start=1):
            lists.write(i, col, value, f["text"])
    lists.write(len(SUBMITTAL_STATUSES) + 3, 0, "Edit these lists to change the drop-down choices.", f["note"])

    # Header block
    log.hide_gridlines(2)
    log.set_row(0, 26)
    log.write(0, 0, "SUBMITTAL LOG", f["title"])
    template = not rows
    fields = [("Project", "project", 1, 0), ("Project no.", "project_no", 1, 6),
              ("Subcontractor", "subcontractor", 2, 0), ("General contractor", "general_contractor", 2, 6),
              ("Prepared by", "prepared_by", 3, 0), ("Log updated", "updated", 3, 6)]
    for label, key, r, c in fields:
        log.write(r, c, label, f["label"])
        value = project.get(key, "")
        target = (r, c + 1, r, c + 4) if c == 0 else (r, c + 1, r, c + 3)
        if key == "updated":
            log.merge_range(*target, "", f["input_date"])
            if value:
                log.write_datetime(r, c + 1, dt.datetime.combine(_as_date(value), dt.time()), f["input_date"])
        else:
            log.merge_range(*target, value, f["input"])
    log.write(4, 0, "Yellow cells are for you to fill in. Days in review and Late? are worked out for you. "
                    "This log tracks paperwork only; it does not confirm that anything complies.", f["subtitle"])

    for col, (name, width) in enumerate(LOG_COLUMNS):
        log.write(LOG_HEADER_ROW, col, name, f["header"])
        log.set_column(col, col, width)
    log.set_row(LOG_HEADER_ROW, 32)
    idx = {name: i for i, (name, _) in enumerate(LOG_COLUMNS)}
    L = {name: xl_col_to_name(i) for name, i in idx.items()}

    data = list(rows or [])
    if template:
        data = [{
            "Submittal No.": "EXAMPLE 23 34 23-001", "Rev": "0", "Spec section": "23 34 23",
            "Description": "Exhaust fans EF-1 to EF-3 - product data (example row: replace or delete)",
            "Type": "Product data", "Submitted to": "General contractor", "Date required": "2026-03-02",
            "Date submitted": "2026-02-24", "Date returned": "2026-03-06", "Status": "Approved as noted",
            "Ball in court": "Subcontractor", "Next action": "File the reviewed copy",
            "Reviewer comments / notes": "Confirm motor voltage with the electrical drawings.",
            "File name": "23 34 23-001_R0_Exhaust-Fans_Product-Data.pdf", "_example": True}]
    total_rows = max(LOG_ROWS, len(data) + 50)
    first = LOG_HEADER_ROW + 1
    days_values, late_values, status_values = [], [], []
    for n in range(total_rows):
        r = first + n
        excel = r + 1
        entry = data[n] if n < len(data) else {}
        example = entry.get("_example", False)
        text_fmt = f["example"] if example else f["text"]
        date_fmt = f["example_date"] if example else f["date"]
        for name, _ in LOG_COLUMNS:
            if name in ("Days in review", "Late?"):
                continue
            value = entry.get(name, "")
            col = idx[name]
            if name.startswith("Date"):
                day = _as_date(value)
                if day:
                    log.write_datetime(r, col, dt.datetime.combine(day, dt.time()), date_fmt)
                else:
                    log.write_blank(r, col, None, date_fmt)
            else:
                log.write(r, col, value, text_fmt)
        submitted, returned, required = (_as_date(entry.get("Date submitted")), _as_date(entry.get("Date returned")),
                                         _as_date(entry.get("Date required")))
        days = "" if not submitted else ((returned or today) - submitted).days
        late = "LATE" if (required and not submitted and today > required) else ""
        log.write_formula(r, idx["Days in review"],
                          f'=IF({L["Date submitted"]}{excel}="","",IF({L["Date returned"]}{excel}="",'
                          f'TODAY()-{L["Date submitted"]}{excel},{L["Date returned"]}{excel}-{L["Date submitted"]}{excel}))',
                          f["int"], days)
        log.write_formula(r, idx["Late?"],
                          f'=IF(AND(ISNUMBER({L["Date required"]}{excel}),{L["Date submitted"]}{excel}="",'
                          f'TODAY()>{L["Date required"]}{excel}),"LATE","")', f["center"], late)
        days_values.append((days, returned))
        late_values.append(late)
        status_values.append(entry.get("Status", ""))

    last = first + total_rows - 1
    log.data_validation(first, idx["Type"], last, idx["Type"],
                        {"validate": "list", "source": f"=Lists!$A$2:$A${len(SUBMITTAL_TYPES) + 1}"})
    log.data_validation(first, idx["Status"], last, idx["Status"],
                        {"validate": "list", "source": f"=Lists!$B$2:$B${len(SUBMITTAL_STATUSES) + 1}"})
    log.data_validation(first, idx["Ball in court"], last, idx["Ball in court"],
                        {"validate": "list", "source": f"=Lists!$C$2:$C${len(BALL_IN_COURT) + 1}"})
    colours = {"Approved": "st_ok", "Approved as noted": "st_ok", "Revise and resubmit": "st_review",
               "Rejected": "st_bad", "Submitted - under review": "st_info", "Not submitted": "st_grey",
               "For record only": "st_grey", "Closed": "st_grey"}
    for value, key in colours.items():
        log.conditional_format(first, idx["Status"], last, idx["Status"],
                               {"type": "cell", "criteria": "==", "value": f'"{value}"', "format": f[key]})
    log.conditional_format(first, idx["Late?"], last, idx["Late?"],
                           {"type": "cell", "criteria": "==", "value": '"LATE"', "format": f["st_bad"]})
    log.conditional_format(first, idx["Days in review"], last, idx["Days in review"],
                           {"type": "formula", "format": f["st_review"],
                            "criteria": f'=AND(ISNUMBER(${L["Days in review"]}{first + 1}),'
                                        f'${L["Days in review"]}{first + 1}>=14,${L["Date returned"]}{first + 1}="")'})
    log.freeze_panes(first, 1)
    log.autofilter(LOG_HEADER_ROW, 0, last, len(LOG_COLUMNS) - 1)
    log.set_landscape()
    log.set_paper(1)
    log.fit_to_pages(1, 0)
    log.repeat_rows(LOG_HEADER_ROW)

    # Summary
    summary.hide_gridlines(2)
    summary.set_column(0, 0, 34)
    summary.set_column(1, 1, 12)
    summary.write(0, 0, "Submittal summary", f["title"])
    summary.write(1, 0, project.get("project", ""), f["subtitle"])
    summary.write(3, 0, "Status", f["header"])
    summary.write(3, 1, "Count", f["header"])
    rng = f"'Submittal Log'!${L['Status']}${first + 1}:${L['Status']}${last + 1}"
    row = 4
    for status in SUBMITTAL_STATUSES:
        summary.write(row, 0, status, f["bold"])
        summary.write_formula(row, 1, f'=COUNTIF({rng},"{status}")', f["int"], status_values.count(status))
        row += 1
    numbers = f"'Submittal Log'!${L['Submittal No.']}${first + 1}:${L['Submittal No.']}${last + 1}"
    summary.write(row, 0, "Total submittals logged", f["bold"])
    summary.write_formula(row, 1, f"=COUNTA({numbers})", f["int"], sum(1 for d in data if d.get("Submittal No.")))
    row += 1
    late_rng = f"'Submittal Log'!${L['Late?']}${first + 1}:${L['Late?']}${last + 1}"
    summary.write(row, 0, "Late to submit", f["bold"])
    summary.write_formula(row, 1, f'=COUNTIF({late_rng},"LATE")', f["int"], late_values.count("LATE"))
    row += 1
    days_rng = f"'Submittal Log'!${L['Days in review']}${first + 1}:${L['Days in review']}${last + 1}"
    ret_rng = f"'Submittal Log'!${L['Date returned']}${first + 1}:${L['Date returned']}${last + 1}"
    returned_days = [d for d, ret in days_values if ret and d != ""]
    average = round(sum(returned_days) / len(returned_days), 1) if returned_days else ""
    summary.write(row, 0, "Average days in review (returned)", f["bold"])
    summary.write_formula(row, 1, f'=IFERROR(ROUND(AVERAGEIFS({days_rng},{ret_rng},"<>"),1),"")', f["num1"], average)
    for value, key in colours.items():
        summary.conditional_format(4, 0, 4 + len(SUBMITTAL_STATUSES) - 1, 0,
                                   {"type": "cell", "criteria": "==", "value": f'"{value}"', "format": f[key]})

    kitlib.write_readme_sheet(workbook, f, "How to use this submittal log", [
        "One row per submittal, and a new row for each resubmittal (same number, next Rev). Use the general "
        "contractor's numbering if they have one; otherwise spec section + sequence, e.g. 23 34 23-001.",
        "Yellow cells at the top are for the project details. Type and Status have drop-downs (edit them on the "
        "Lists sheet). Days in review and Late? are formulas: don't type over them.",
        "Days in review counts from Date submitted to Date returned, or to today while the item is still out. It "
        "turns amber after 14 days. Late? shows LATE when the required date has passed and nothing was submitted.",
        "File name: the exact name of the PDF you sent, so you can always find it again.",
        "The Summary sheet counts submittals by status.",
        "## Rules",
        "This log tracks paperwork. Approval decisions come from the reviewers. You never certify that a product "
        "complies, and you never alter a manufacturer's document.",
    ])
    workbook.close()


INDEX_HEADERS = [("Section", 30), ("Title", 46), ("File", 40), ("Order", 7), ("Notes", 46), ("Pages", 9),
                 ("Include", 9)]
INDEX_EXAMPLES = [
    ["EXAMPLE - General Information", "Contractor and supplier contact list", "contact-list.pdf", "1",
     "Prepared by the subcontractor", "", "yes"],
    ["EXAMPLE - Rooftop Unit RTU-1", "Product data", "rtu-1-datasheet.pdf", "2", "Spec section 23 74 00", "", "yes"],
    ["EXAMPLE - Rooftop Unit RTU-1", "Installation, operation and maintenance manual", "rtu-1-iom.pdf", "3",
     "", "", "yes"],
    ["EXAMPLE - Rooftop Unit RTU-1", "Performance data only", "rtu-1-iom.pdf", "4", "Pages 12-14 of the manual",
     "12-14", "yes"],
    ["EXAMPLE - Testing and Balancing", "Final test and balance report", "", "5",
     "Blank file = placeholder page until it arrives", "", "yes"],
]


def write_index_template(xlsx_path, csv_path):
    workbook = xlsxwriter.Workbook(str(xlsx_path))
    f = kitlib.xlsx_formats(workbook)
    sheet = workbook.add_worksheet("Index")
    for col, (name, width) in enumerate(INDEX_HEADERS):
        sheet.write(0, col, name, f["header"])
        sheet.set_column(col, col, width)
    for r, values in enumerate(INDEX_EXAMPLES, start=1):
        for c, value in enumerate(values):
            sheet.write(r, c, value, f["example"])
    for r in range(len(INDEX_EXAMPLES) + 1, 200):
        for c in range(len(INDEX_HEADERS)):
            sheet.write_blank(r, c, None, f["text"])
    sheet.data_validation(1, 6, 199, 6, {"validate": "list", "source": ["yes", "no"]})
    sheet.freeze_panes(1, 0)
    kitlib.write_readme_sheet(workbook, f, "How to fill in the binder index", [
        "One row per document, in the order the client or general contractor wants. build_binder.py reads this "
        "sheet. Rows that start with EXAMPLE are ignored, so type over them or delete them.",
        "Section: the tab the document goes in. Every distinct section gets a divider page, in the order the "
        "sections first appear.",
        "Title: what the reader sees in the contents and bookmarks. Keep it short and specific.",
        "File: the PDF's file name inside the folder you pass with --pdf-folder (sub-folders allowed, e.g. "
        "warranties/rtu-1.pdf). Leave it blank for a document you're still waiting for: the binder gets a "
        "PENDING placeholder page.",
        "Order: numbers like 1, 2, 3 or 1.1, 1.2. Rows are sorted by this. Leave the whole column blank to keep "
        "the row order.",
        "Notes: optional; shown in small print under the title in the contents.",
        "Pages: optional; e.g. 3-5 or 1,4-6 to include only some pages. Blank = all pages.",
        "Include: 'no' leaves the row out without deleting it.",
    ])
    workbook.close()
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([name.lower() for name, _ in INDEX_HEADERS])
        for values in INDEX_EXAMPLES:
            writer.writerow(values)


SITE_COLUMNS = [("No.", 5), ("Product name (as on label)", 40), ("Manufacturer / brand", 26), ("Location / area", 22),
                ("Container size", 14), ("Quantity", 9), ("In use?", 8), ("SDS file", 34), ("Notes", 40)]
SITE_HEADER_ROW = 10


def write_site_list(path, info: dict | None = None, rows: list[dict] | None = None):
    """The on-site chemical list. The client confirms it; extract_sds.py reads it."""
    info = info or {}
    workbook = xlsxwriter.Workbook(str(path))
    f = kitlib.xlsx_formats(workbook)
    sheet = workbook.add_worksheet("Site Chemical List")
    sheet.hide_gridlines(2)
    sheet.write(0, 0, "On-site chemical list", f["title"])
    sheet.set_row(0, 26)
    for col, (name, width) in enumerate(SITE_COLUMNS):
        sheet.set_column(col, col, width)
    fields = [("Client", "client"), ("Site address", "site"), ("Walk-through / photos dated", "walkthrough"),
              ("Prepared by", "prepared_by")]
    for r, (label, key) in enumerate(fields, start=1):
        sheet.merge_range(r, 0, r, 1, label, f["label"])
        sheet.merge_range(r, 2, r, 4, info.get(key, ""), f["input"])
    sheet.merge_range(6, 0, 6, 8, "Employer confirmation: this list shows the hazardous chemical products used or "
                                  "stored at this site on the date below.", f["label"])
    sheet.merge_range(7, 0, 7, 1, "Name and title", f["label"])
    sheet.merge_range(7, 2, 7, 4, info.get("confirmed_by", ""), f["input"])
    sheet.write(7, 5, "Date", f["label"])
    sheet.merge_range(7, 6, 7, 7, info.get("confirmed_on", ""), f["input"])
    sheet.write(8, 0, "List every product, including ones in vans, closets and storage. Rows that start with "
                      "EXAMPLE are ignored.", f["subtitle"])
    for col, (name, _) in enumerate(SITE_COLUMNS):
        sheet.write(SITE_HEADER_ROW, col, name, f["header"])
    sheet.set_row(SITE_HEADER_ROW, 30)
    data = list(rows or [])
    if not data:
        data = [{"Product name (as on label)": "EXAMPLE - Brake parts cleaner, aerosol",
                 "Manufacturer / brand": "Brand on the label", "Location / area": "Service bay 2",
                 "Container size": "14 oz can", "Quantity": "6", "In use?": "Yes",
                 "SDS file": "brake-parts-cleaner.pdf", "Notes": "Photo IMG_0412", "_example": True}]
    total = max(150, len(data) + 50)
    for n in range(total):
        r = SITE_HEADER_ROW + 1 + n
        entry = data[n] if n < len(data) else {}
        fmt = f["example"] if entry.get("_example") else f["text"]
        for col, (name, _) in enumerate(SITE_COLUMNS):
            value = entry.get(name, "")
            if name == "No." and entry and not entry.get("_example"):
                value = n + 1 - sum(1 for e in data[:n] if e.get("_example"))
            sheet.write(r, col, value, fmt)
    sheet.data_validation(SITE_HEADER_ROW + 1, 6, SITE_HEADER_ROW + total, 6,
                          {"validate": "list", "source": ["Yes", "No"]})
    sheet.freeze_panes(SITE_HEADER_ROW + 1, 2)
    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)
    sheet.repeat_rows(SITE_HEADER_ROW)
    kitlib.write_readme_sheet(workbook, f, "How to use the on-site chemical list", [
        "Fill this in from the client's shelf photos, purchase records and the existing binder. One row per "
        "product (the same product in two areas = two rows).",
        "Copy the product name exactly as it appears on the label. The manufacturer or brand helps match the "
        "right safety data sheet.",
        "SDS file: once you have the current sheet, put its file name here. extract_sds.py uses it to match "
        "products to sheets; if it's blank, the script matches by name and asks you to confirm.",
        "In use? 'No' rows are skipped (keep them for the record).",
        "The employer confirms this list, not you. Send it to them, ask them to check every area, and record "
        "who confirmed it and when.",
    ])
    workbook.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create the spreadsheet templates.")
    parser.add_argument("--out-dir", default=str(kitlib.KIT_DIR / "templates"), help="where to write them")
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_submittal_log(out / "submittal-log.xlsx")
    write_index_template(out / "binder-index-template.xlsx", out / "binder-index-template.csv")
    write_site_list(out / "sds-site-list-template.xlsx")
    for name in ("submittal-log.xlsx", "binder-index-template.xlsx", "binder-index-template.csv",
                 "sds-site-list-template.xlsx"):
        print(f"Wrote {out / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
