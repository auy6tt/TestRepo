#!/usr/bin/env python3
"""Build the portfolio sample: a small website for the FICTIONAL Town of Fernwick.

Creates:
  samples/town-site/      HTML pages, robots.txt, sitemap.xml and documents
  samples/source-files/   the Word files behind the tagged PDFs, including the
                          rebuilt council agenda used for the before/after sample

The documents show problems you meet on real public-body websites:
  - untagged PDFs with missing or junk titles and no language
  - an exact duplicate, an old file and a short notice
  - a fillable form whose fields have no names for screen readers
  - an image-only scan with no real text
  - a properly tagged PDF made from a structured Word file
  - a tagged PDF with fake headings, a table without header cells and an image
    without alt text
  - Word, Excel and PowerPoint files with common problems

Fernwick is not a real place. All names, numbers and addresses are made up.
Phone numbers use the 555-01xx range, which is reserved for fiction.

Then run run_sample_demo.py to crawl the site and produce the outputs.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import pikepdf
from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pptx import Presentation
from pptx.util import Inches as PptInches
from pptx.util import Pt as PptPt
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_to_tagged_pdf import convert  # noqa: E402
from office_helpers import add_picture, add_table, patch_app_properties, set_base_font, set_properties  # noqa: E402

KIT = Path(__file__).resolve().parent.parent
SAMPLES = KIT / "samples"
SITE = SAMPLES / "town-site"
DOCS = SITE / "documents"
SOURCES = SAMPLES / "source-files"
TOWN = "Town of Fernwick"
MADE_WITH = "Fernwick sample builder"

random.seed(2026)


# ---------------------------------------------------------------------------
# Fonts and images
# ---------------------------------------------------------------------------

def font(kind: str, size: int):
    candidates = {
        "serif": ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "Times New Roman.ttf", "times.ttf"],
        "serif-bold": ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "timesbd.ttf"],
        "sans": ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"],
        "sans-bold": ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf"],
    }[kind]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def park_picture(path: Path) -> None:
    img = Image.new("RGB", (1200, 500), (200, 228, 247))
    d = ImageDraw.Draw(img)
    d.ellipse([1020, 40, 1130, 150], fill=(255, 205, 60))
    d.rectangle([0, 330, 1200, 500], fill=(120, 180, 90))
    for x in (180, 420):
        d.rectangle([x - 15, 230, x + 15, 360], fill=(110, 75, 45))
        d.ellipse([x - 90, 110, x + 90, 270], fill=(50, 130, 60))
    d.rounded_rectangle([640, 360, 1080, 460], radius=20, fill=(90, 170, 220), outline=(255, 255, 255), width=6)
    d.rectangle([560, 250, 600, 360], fill=(200, 80, 60))
    d.line([(520, 250), (640, 250)], fill=(200, 80, 60), width=10)
    img.save(path)


def bar_chart_picture(path: Path, title: str, labels: list[str], values: list[float], unit: str) -> None:
    img = Image.new("RGB", (1200, 650), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 20), title, fill="black", font=font("sans-bold", 36))
    top, bottom, left = 110, 560, 150
    biggest = max(values)
    width = (1200 - left - 60) // len(values)
    d.line([(left, top), (left, bottom), (1160, bottom)], fill="black", width=3)
    for i, (label, value) in enumerate(zip(labels, values)):
        x0 = left + i * width + 25
        height = (bottom - top - 30) * value / biggest
        d.rectangle([x0, bottom - height, x0 + width - 50, bottom], fill=(40, 100, 170))
        d.text((x0, bottom + 12), label, fill="black", font=font("sans", 26))
        d.text((x0, bottom - height - 36), f"{value:g}{unit}", fill="black", font=font("sans", 26))
    img.save(path)


def seal_picture(path: Path) -> None:
    img = Image.new("RGB", (400, 400), "white")
    d = ImageDraw.Draw(img)
    d.ellipse([10, 10, 390, 390], outline=(30, 70, 120), width=14)
    d.ellipse([60, 60, 340, 340], outline=(30, 70, 120), width=6)
    text = "FERNWICK"
    f = font("serif-bold", 54)
    d.text(((400 - d.textlength(text, font=f)) / 2, 165), text, fill=(30, 70, 120), font=f)
    img.save(path)


# ---------------------------------------------------------------------------
# Untagged PDFs (made with ReportLab, which does not add tags)
# ---------------------------------------------------------------------------

STYLES = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=11, leading=16, spaceAfter=8)
BIG = ParagraphStyle("big", parent=BODY, fontName="Helvetica-Bold", fontSize=18, leading=24, spaceAfter=6)
MID = ParagraphStyle("mid", parent=BODY, fontName="Helvetica-Bold", fontSize=13, leading=18, spaceBefore=8)
ITEM = ParagraphStyle("item", parent=BODY, leftIndent=22, firstLineIndent=-16, spaceAfter=4)
SUB = ParagraphStyle("sub", parent=ITEM, leftIndent=46)


def footer(c, doc):
    c.saveState()
    c.setFont("Helvetica", 9)
    c.drawString(inch, 0.6 * inch, TOWN)
    c.drawRightString(letter[0] - inch, 0.6 * inch, f"Page {doc.page}")
    c.restoreState()


def finish_pdf(path: Path, title: str | None, when: dt.datetime) -> None:
    """Set realistic metadata: the given title (or none), no language, fixed dates."""
    with pikepdf.open(path, allow_overwriting_input=True) as pdf:
        info = pdf.docinfo
        for key in ("/Subject", "/Keywords", "/Title"):
            if key in info:
                del info[key]
        info["/Author"] = TOWN
        info["/Creator"] = MADE_WITH
        stamp = when.strftime("D:%Y%m%d%H%M%S")
        info["/CreationDate"] = stamp
        info["/ModDate"] = stamp
        if title is not None:
            info["/Title"] = title
        pdf.save(path)


def build_untagged(path: Path, story: list, title: str | None, when: dt.datetime) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    finish_pdf(path, title, when)


def grid_table(rows: list[list[str]], widths: list[float]) -> Table:
    table = Table(rows, colWidths=[w * inch for w in widths], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    return table


AGENDA_ITEMS = [
    ("Call to order", []),
    ("Pledge of Allegiance", []),
    ("Roll call", []),
    ("Approval of the minutes of the February 10, 2026 regular meeting", []),
    ("Public comment (3 minutes per speaker)", []),
    ("Old business", ["Main Street sidewalk project: update from the Town Engineer",
                      "Library roof repair: bid results"]),
    ("New business", ["Resolution 2026-14: authorizing the purchase of one dump truck for the Public Works Department",
                      "Fiscal Year 2027 budget calendar",
                      "Parks and Recreation summer staffing plan",
                      "Appointment to the Planning Board (one seat, term ending 2029)"]),
    ("Department reports", ["Town Manager", "Police Chief", "Public Works Director", "Parks and Recreation Director"]),
    ("Council comments", []),
    ("Executive session, if needed, to discuss a personnel matter", []),
    ("Adjournment", []),
]
CONSENT_ITEMS = [
    "Payment of bills: warrant 2026-05, total $412,880.17",
    "Renewal of the town's general liability insurance policy",
    "Request from the Fernwick Garden Club to use the Town Green on May 16, 2026",
    "Treasurer's report for January 2026",
]
ACCOMMODATION = ("If you need an accommodation to take part in this meeting, contact the Town Clerk at "
                 "(555) 010-0100 at least 48 hours before the meeting.")


def agenda_pdf(path: Path) -> None:
    story = [Paragraph("TOWN OF FERNWICK", MID), Paragraph("Town Council Regular Meeting", BIG),
             Paragraph("AGENDA", BIG),
             Paragraph("Tuesday, March 10, 2026, 7:00 p.m.<br/>Council Chambers, Town Hall, 12 Mill Street", BODY),
             Spacer(1, 10)]
    for number, (item, subs) in enumerate(AGENDA_ITEMS, start=1):
        story.append(Paragraph(f"{number}.&nbsp;&nbsp;{item}", ITEM))
        for letter_index, sub in enumerate(subs):
            story.append(Paragraph(f"{chr(97 + letter_index)}.&nbsp;&nbsp;{sub}", SUB))
    story += [PageBreak(), Paragraph("Consent agenda", MID),
              Paragraph("These items are approved with one vote unless a council member asks to discuss one.", BODY)]
    story += [Paragraph(f"-&nbsp;&nbsp;{item}", ITEM) for item in CONSENT_ITEMS]
    story += [Spacer(1, 10), Paragraph("Accessibility", MID), Paragraph(ACCOMMODATION, BODY),
              Paragraph("Watch the meeting", MID),
              Paragraph("Meetings are shown live on Fernwick Community Television, channel 99.", BODY),
              Paragraph("Next regular meeting: Tuesday, April 14, 2026.", BODY)]
    build_untagged(path, story, None, dt.datetime(2026, 3, 5, 15, 12))


def minutes_pdf(path: Path) -> None:
    p = lambda text: Paragraph(text, BODY)  # noqa: E731
    story = [Paragraph("TOWN OF FERNWICK", MID), Paragraph("Town Council Minutes", BIG),
             p("Regular meeting of February 10, 2026, Council Chambers, Town Hall"),
             p("<b>Present:</b> Mayor Dana Whitfield; Council Members Luis Ortega, Priya Raman, Tom Becker and Grace "
               "Holloway. Also present: Town Manager Alan Price, Town Clerk Maria Lindqvist and Town Engineer Sam Okafor."),
             Paragraph("1. Call to order", MID),
             p("Mayor Whitfield called the meeting to order at 7:02 p.m. The Pledge of Allegiance was recited. "
               "The Clerk called the roll. All members were present."),
             Paragraph("2. Approval of minutes", MID),
             p("Motion by Council Member Ortega, seconded by Council Member Raman, to approve the minutes of the "
               "January 13, 2026 regular meeting as presented. Motion carried 5-0."),
             Paragraph("3. Public comment", MID),
             p("Three residents spoke. A resident of Brook Lane asked about snow removal on the sidewalks near the "
               "elementary school. A resident of Orchard Road supported the library roof repair. A resident of "
               "River Road asked when the spring leaf pickup schedule will be posted."),
             Paragraph("4. Old business", MID),
             p("<b>Main Street sidewalk project.</b> Town Engineer Okafor reported that the design is 90 percent "
               "complete. The town has applied for a state grant of $350,000. Construction could start in July if "
               "the grant is awarded. Council Member Becker asked about parking during construction. Mr. Okafor said "
               "most of the work will be done at night and the north side of Main Street will stay open."),
             p("<b>Library roof repair.</b> The Town Manager reported that bids open on March 2. The estimate is "
               "$186,000. No action was taken.")]
    story += [PageBreak(), Paragraph("5. New business", MID),
              p("<b>Snow and ice budget transfer.</b> Motion by Council Member Holloway, seconded by Council Member "
                "Becker, to transfer $45,000 from the contingency account to the snow and ice account. Motion "
                "carried 5-0."),
              p("<b>Recycling contract.</b> The council discussed a three-year extension of the contract with Valley "
                "Recycling Services. Motion by Council Member Raman, seconded by Council Member Ortega, to approve "
                "the extension at $14.50 per household per month. Motion carried 4-1, with Council Member Becker "
                "opposed."),
              p("<b>Planning Board vacancy.</b> The Mayor announced one vacancy on the Planning Board. Applications "
                "are due March 1."),
              Paragraph("6. Department reports", MID),
              p("The Police Chief reported 214 calls for service in January. Public Works crews treated roads "
                "during six storms. Parks and Recreation will open registration for spring programs on March 1."),
              Paragraph("7. Council comments", MID),
              p("Council Member Holloway thanked the Public Works crews for their storm work. Council Member Raman "
                "reminded residents about the library's tax help sessions."),
              Paragraph("8. Adjournment", MID),
              p("Motion by Council Member Ortega, seconded by Council Member Holloway, to adjourn at 8:41 p.m. "
                "Motion carried 5-0."),
              p("Respectfully submitted, Maria Lindqvist, Town Clerk.")]
    stats = [["Department", "January 2026", "January 2025"], ["Police calls for service", "214", "198"],
             ["Fire and rescue calls", "61", "57"], ["Storms treated", "6", "4"],
             ["Building permits issued", "18", "22"], ["Library visits", "3,912", "3,640"]]
    story += [PageBreak(), Paragraph("Attachment: January 2026 department statistics", MID),
              grid_table(stats, [3.2, 1.5, 1.5]), Spacer(1, 12),
              p("Approved by the Town Council on March 10, 2026.")]
    build_untagged(path, story, "Minutes_Feb2026_FINAL", dt.datetime(2026, 2, 24, 10, 30))


def planning_minutes_2019(path: Path) -> None:
    p = lambda text: Paragraph(text, BODY)  # noqa: E731
    story = [Paragraph("TOWN OF FERNWICK PLANNING BOARD", MID), Paragraph("Minutes, June 18, 2019", BIG),
             p("<b>Present:</b> Chair Ruth Adeyemi, Members Carl Jensen, Nora Fitzgerald and Ben Torres. "
               "Absent: Member Lily Chen."),
             Paragraph("Site plan review: River Road Hardware", MID),
             p("The applicant asked to build a 2,400 square foot addition at the back of the store at 210 River "
               "Road. The board reviewed parking, drainage and lighting. Motion by Member Jensen, seconded by Member "
               "Torres, to approve the site plan with two conditions: shielded lighting and a landscaped buffer "
               "along the rear lot line. Motion carried 4-0."),
             Paragraph("Zoning text amendment: home businesses", MID),
             p("The board discussed a draft amendment allowing small home businesses in residential zones. The draft "
               "will be revised and discussed again in July.")]
    story += [PageBreak(), Paragraph("Other business", MID),
              p("The Chair reminded members about the state planning conference in October. The board agreed to "
                "meet on July 16, 2019."),
              p("The meeting was adjourned at 8:55 p.m."),
              p("Submitted by the Planning Board secretary.")]
    build_untagged(path, story, "Planning Board Minutes June 2019", dt.datetime(2019, 6, 25, 9, 0))


REVENUE = [("Property tax", 12_950_000, 13_420_000), ("State aid", 2_180_000, 2_240_000),
           ("Water and sewer charges", 1_610_000, 1_690_000), ("Fees, permits and licenses", 520_000, 545_000),
           ("Grants", 310_000, 295_000), ("Other income", 205_000, 210_000)]
SPENDING = [("Police and fire", 5_920_000), ("Public works", 3_460_000), ("Employee benefits and insurance", 2_450_000),
            ("General government", 1_850_000), ("Water and sewer", 1_690_000), ("Debt service", 1_410_000),
            ("Parks and recreation", 980_000), ("Library", 640_000)]


def money(value: float) -> str:
    return f"${value:,.0f}"


def budget_pdf(path: Path) -> None:
    p = lambda text: Paragraph(text, BODY)  # noqa: E731
    total_old = sum(r[1] for r in REVENUE)
    total_new = sum(r[2] for r in REVENUE)
    story = [Paragraph("TOWN OF FERNWICK", MID), Paragraph("Fiscal Year 2026 Budget Summary", BIG),
             p("Fiscal year 2026 runs from July 1, 2025 to June 30, 2026. The Town Council adopted this budget on "
               "June 9, 2025."),
             p(f"The total budget is {money(total_new)}, an increase of {money(total_new - total_old)} "
               f"({(total_new - total_old) / total_old:.1%}) over fiscal year 2025. Most of the increase pays for "
               "higher insurance costs, a new dump truck and the Main Street sidewalk project."),
             Paragraph("Budget at a glance", MID),
             grid_table([["Measure", "FY2025", "FY2026"], ["Total budget", money(total_old), money(total_new)],
                         ["Tax rate per $1,000 of assessed value", "$18.42", "$18.90"],
                         ["Average household tax bill", "$5,526", "$5,670"]], [3.2, 1.4, 1.4])]
    revenue_rows = [["Source", "FY2025 actual", "FY2026 adopted", "Change"]]
    revenue_rows += [[name, money(old), money(new), money(new - old)] for name, old, new in REVENUE]
    revenue_rows.append(["Total", money(total_old), money(total_new), money(total_new - total_old)])
    story += [PageBreak(), Paragraph("Where the money comes from", MID), grid_table(revenue_rows, [2.4, 1.3, 1.4, 1.1]),
              Spacer(1, 10), p("Property tax pays for almost three quarters of the budget. State aid is based on the "
                               "state's school and road aid formulas.")]
    spending_rows = [["Department", "FY2026 adopted", "Share"]]
    spending_rows += [[name, money(value), f"{value / total_new:.1%}"] for name, value in SPENDING]
    chart = Drawing(460, 210)
    bars = HorizontalBarChart()
    bars.x, bars.y, bars.width, bars.height = 150, 10, 290, 190
    bars.data = [[v / 1_000_000 for _, v in reversed(SPENDING)]]
    bars.categoryAxis.categoryNames = [n for n, _ in reversed(SPENDING)]
    bars.categoryAxis.labels.fontSize = 8
    bars.valueAxis.valueMin = 0
    bars.bars[0].fillColor = colors.HexColor("#2E6DA4")
    chart.add(bars)
    story += [PageBreak(), Paragraph("Where the money goes", MID), grid_table(spending_rows, [3.0, 1.5, 1.0]),
              Spacer(1, 14), p("Spending by department, in millions of dollars:"), chart]
    capital = [["Project", "Cost", "Funding"], ["Main Street sidewalks", "$420,000", "State grant (applied for) and reserves"],
               ["Library roof", "$186,000", "Capital reserve"], ["Dump truck", "$198,450", "Capital budget"],
               ["Playground surfacing", "$65,000", "Parks reserve"]]
    story += [PageBreak(), Paragraph("Capital projects", MID), grid_table(capital, [2.2, 1.1, 2.9]), Spacer(1, 12),
              p("Questions? Contact the Finance Office at Town Hall, phone (555) 010-0110.")]
    build_untagged(path, story, "untitled", dt.datetime(2025, 6, 12, 14, 0))


def fee_schedule_pdf(path: Path) -> None:
    building = [["Fee", "Amount"],
                ["Building permit, residential", "$12 per $1,000 of construction value (minimum $75)"],
                ["Building permit, commercial", "$15 per $1,000 of construction value (minimum $150)"],
                ["Electrical permit", "$60"], ["Plumbing permit", "$60"], ["Demolition permit", "$100"],
                ["Zoning variance application", "$250"], ["Site plan review", "$400 plus $25 per 1,000 square feet"],
                ["Certificate of occupancy", "$50"]]
    clerk = [["Fee", "Amount"], ["Dog license, spayed or neutered", "$10"], ["Dog license, not spayed or neutered", "$20"],
             ["Late dog license", "$15 extra"], ["Copy of a birth or death certificate", "$15"],
             ["Marriage license", "$40"], ["Photocopies", "$0.25 per page"], ["Returned check", "$30"]]
    parks = [["Fee", "Amount"], ["Pavilion rental, residents", "$50 per day"], ["Pavilion rental, non-residents", "$100 per day"],
             ["Pool season pass, resident family", "$180"], ["Pool day pass", "$6"], ["Trash sticker", "$3 each"],
             ["Bulk item pickup", "$25 per item"], ["Water meter test", "$35"]]
    story = [Paragraph("TOWN OF FERNWICK", MID), Paragraph("Fee Schedule 2026", BIG),
             Paragraph("Fees adopted by the Town Council on December 9, 2025. They apply from January 1, 2026.", BODY),
             Paragraph("Building and zoning", MID), grid_table(building, [2.6, 3.6]),
             PageBreak(), Paragraph("Town Clerk", MID), grid_table(clerk, [2.6, 3.6]),
             Paragraph("Parks, pool and public works", MID), grid_table(parks, [2.6, 3.6])]
    build_untagged(path, story, "Fee Schedule 2026", dt.datetime(2025, 12, 15, 11, 0))


def hearing_notice_pdf(path: Path) -> None:
    story = [Paragraph("TOWN OF FERNWICK", MID), Paragraph("Notice of Public Hearing", BIG),
             Paragraph("The Fernwick Town Council will hold a public hearing on Tuesday, April 14, 2026 at 7:00 p.m. "
                       "in the Council Chambers, Town Hall, 12 Mill Street, on proposed Ordinance 2026-03. The "
                       "ordinance changes the sign rules for businesses on Main Street.", BODY),
             Paragraph("A copy of the proposed ordinance is available at Town Hall during business hours. Send written "
                       "comments to the Town Clerk by April 10, 2026.", BODY),
             Paragraph(ACCOMMODATION.replace("this meeting", "the hearing"), BODY),
             Paragraph("Maria Lindqvist, Town Clerk", BODY)]
    build_untagged(path, story, None, dt.datetime(2026, 3, 20, 9, 30))


def small_pdf(path: Path, heading: str, lines: list[str], when: dt.datetime) -> None:
    build_untagged(path, [Paragraph(heading, BIG)] + [Paragraph(line, BODY) for line in lines], None, when)


def permit_form_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 730, "Town of Fernwick: Building Permit Application")
    c.setFont("Helvetica", 10)
    c.drawString(72, 712, "Building Department, Town Hall, 12 Mill Street. Phone (555) 010-0120.")
    form = c.acroForm
    y = 670
    for label, name in [("Owner name", "owner_name"), ("Property address", "property_address"), ("Phone", "phone"),
                        ("Email", "email"), ("Contractor name", "contractor"),
                        ("Contractor license number", "license_number"), ("Estimated cost of work ($)", "cost")]:
        c.drawString(72, y + 5, label)
        form.textfield(name=name, x=250, y=y, width=290, height=18, borderStyle="inset", forceBorder=True, fontSize=10)
        y -= 32
    c.drawString(72, y + 5, "Type of work:")
    y -= 24
    for label, name in [("New building", "work_new"), ("Addition", "work_addition"),
                        ("Alteration or repair", "work_alteration"), ("Demolition", "work_demolition")]:
        form.checkbox(name=name, x=90, y=y, size=12, buttonStyle="check", borderWidth=1, forceBorder=True)
        c.drawString(110, y + 2, label)
        y -= 22
    c.drawString(72, y, "Description of work:")
    y -= 72
    form.textfield(name="description", x=72, y=y, width=468, height=62, fieldFlags="multiline",
                   borderStyle="inset", forceBorder=True, fontSize=10)
    y -= 40
    c.drawString(72, y + 5, "Signature")
    form.textfield(name="signature", x=140, y=y, width=220, height=18, borderStyle="inset", forceBorder=True)
    c.drawString(380, y + 5, "Date")
    form.textfield(name="date", x=420, y=y, width=120, height=18, borderStyle="inset", forceBorder=True)
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 730, "What to include with your application")
    c.setFont("Helvetica", 11)
    y = 700
    for line in ["1. Two copies of the building plans.", "2. A plot plan showing the work and the lot lines.",
                 "3. Proof of the contractor's insurance.", "4. The permit fee (see the 2026 fee schedule).",
                 "", "Most permits are reviewed within 10 business days. Call the Building Department with questions."]:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    finish_pdf(path, "Building Permit Application", dt.datetime(2025, 9, 2, 8, 45))


def scan_pdf(path: Path) -> None:
    """An image-only 'scan' of a signed resolution: no real text at all."""
    width, height = 1700, 2200
    img = Image.new("L", (width, height), 248)
    d = ImageDraw.Draw(img)
    regular, bold = font("serif", 38), font("serif-bold", 44)
    y = 190

    def write(text, use=regular, center=False, gap=56):
        nonlocal y
        x = (width - d.textlength(text, font=use)) / 2 if center else 210
        d.text((x, y), text, fill=30, font=use)
        y += gap

    write("TOWN OF FERNWICK", bold, center=True, gap=66)
    write("RESOLUTION NO. 2026-14", bold, center=True, gap=100)
    paragraphs = [
        "A RESOLUTION AUTHORIZING THE PURCHASE OF ONE DUMP TRUCK FOR THE PUBLIC WORKS DEPARTMENT",
        "WHEREAS, the Public Works Department's 2009 dump truck has reached the end of its useful life; and",
        "WHEREAS, the Town received three quotes through the state cooperative purchasing program, and the lowest "
        "quote was $198,450 from Valley Truck Center; and",
        "WHEREAS, money for this purchase is included in the Fiscal Year 2026 capital budget;",
        "NOW, THEREFORE, BE IT RESOLVED by the Town Council of the Town of Fernwick that the Town Manager is "
        "authorized to buy one dump truck from Valley Truck Center for no more than $198,450.",
        "ADOPTED by the Town Council on March 10, 2026. Vote: 5 in favor, 0 opposed.",
    ]
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, 62):
            write(line)
        y += 30
    y += 120
    for x0 in (210, 960):
        points = [(x0 + i * 12, y - 30 + 22 * ((i * 7) % 5 - 2) / 2) for i in range(30)]
        d.line(points, fill=40, width=4)
        d.line([(x0, y + 20), (x0 + 480, y + 20)], fill=60, width=2)
    d.text((210, y + 34), "Dana Whitfield, Mayor", fill=30, font=regular)
    d.text((960, y + 34), "Attest: Maria Lindqvist, Town Clerk", fill=30, font=font("serif", 34))
    d.ellipse([1240, 1880, 1520, 2160], outline=110, width=6)
    d.text((1300, 2000), "TOWN SEAL", fill=110, font=font("sans-bold", 34))
    img = img.rotate(0.6, resample=Image.BICUBIC, fillcolor=248)
    noise = ImageDraw.Draw(img)
    for _ in range(2500):
        x, yy = random.randrange(width), random.randrange(height)
        noise.point((x, yy), fill=random.randrange(90, 200))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    with tempfile.TemporaryDirectory() as tmp:
        jpg = Path(tmp) / "scan.jpg"
        img.save(jpg, quality=72, dpi=(200, 200))
        c = canvas.Canvas(str(path), pagesize=letter)
        c.drawImage(str(jpg), 0, 0, width=letter[0], height=letter[1])
        c.showPage()
        c.save()
    finish_pdf(path, None, dt.datetime(2026, 3, 12, 16, 20))


# ---------------------------------------------------------------------------
# Word sources and tagged PDFs (LibreOffice)
# ---------------------------------------------------------------------------

def new_docx(title: str, author: str, when: dt.datetime, language: str = "en-US"):
    document = Document()
    set_properties(document, title=title, author=author, language=language, when=when)
    set_base_font(document, "Calibri", 11)
    return document


def page_count(pdf_path: Path) -> int:
    with pikepdf.open(pdf_path) as pdf:
        return len(pdf.pages)


def agenda_docx(path: Path) -> None:
    """The rebuilt agenda: real headings, real lists, title and language."""
    doc = new_docx("Town Council Regular Meeting Agenda, March 10, 2026", "Town Clerk, Town of Fernwick",
                   dt.datetime(2026, 3, 5, 15, 12))
    doc.add_heading("Town Council Regular Meeting Agenda", level=1)
    doc.add_paragraph("Town of Fernwick. Tuesday, March 10, 2026, 7:00 p.m. Council Chambers, Town Hall, 12 Mill Street.")
    doc.add_heading("Agenda items", level=2)
    for item, subs in AGENDA_ITEMS:
        doc.add_paragraph(item, style="List Number")
        for sub in subs:
            doc.add_paragraph(sub, style="List Bullet 2")
    doc.add_heading("Consent agenda", level=2)
    doc.add_paragraph("These items are approved with one vote unless a council member asks to discuss one.")
    for item in CONSENT_ITEMS:
        doc.add_paragraph(item, style="List Bullet")
    doc.add_heading("Accessibility", level=2)
    doc.add_paragraph(ACCOMMODATION)
    doc.add_heading("Watch the meeting", level=2)
    doc.add_paragraph("Meetings are shown live on Fernwick Community Television, channel 99.")
    doc.add_paragraph("Next regular meeting: Tuesday, April 14, 2026.")
    doc.save(path)


def summer_guide_docx(path: Path, picture: Path) -> None:
    doc = new_docx("Summer Recreation Guide 2026", "Fernwick Parks and Recreation", dt.datetime(2026, 3, 2, 9, 0))
    doc.add_heading("Summer Recreation Guide 2026", level=1)
    doc.add_paragraph("Fernwick Parks and Recreation runs camps, swim lessons and family events from June 22 to "
                      "August 21, 2026. Registration opens April 1.")
    add_picture(doc, picture, 6.0, "Drawing of Fernwick Park on a sunny day: two trees, a slide and the town pool.")
    doc.add_heading("How to register", level=2)
    for step in ["Create a family account at Town Hall or by phone.", "Choose your programs from this guide.",
                 "Pay in person by cash, check or card. Ask us about help with fees."]:
        doc.add_paragraph(step, style="List Number")
    doc.add_heading("Programs", level=2)
    add_table(doc, ["Program", "Ages", "Dates", "Fee (residents)"],
              [["Day camp", "6 to 12", "June 22 to August 14", "$95 per week"],
               ["Swim lessons", "4 to 14", "Two-week sessions from June 29", "$45 per session"],
               ["Teen leaders", "13 to 16", "July 6 to July 31", "$60"],
               ["Family movie nights", "All ages", "Fridays in July", "Free"]],
              widths=[1.6, 1.0, 2.2, 1.5])
    doc.add_heading("Pool hours", level=2)
    for line in ["Open swim: noon to 6 p.m. every day", "Lap swim: 6 to 8 a.m., Monday to Friday",
                 "The pool closes during thunderstorms"]:
        doc.add_paragraph(line, style="List Bullet")
    doc.add_heading("Accessibility", level=2)
    doc.add_paragraph("All programs welcome children with disabilities. Tell us what your child needs when you "
                      "register and we will work with you. The pool has a lift chair and an accessible changing room.")
    doc.add_heading("Contact", level=2)
    doc.add_paragraph("Fernwick Parks and Recreation, 30 Park Road. Phone (555) 010-0130. "
                      "Email parks@fernwick.example.")
    doc.save(path)


def water_report_docx(path: Path, chart: Path) -> None:
    """Looks fine on screen, but uses bold text instead of headings, has no table
    header row and no alt text on the chart."""
    doc = new_docx("2025 Water Quality Report", "Fernwick Water Department", dt.datetime(2026, 5, 28, 10, 0))

    def fake_heading(text, size=14):
        run = doc.add_paragraph().add_run(text)
        run.bold = True
        run.font.size = Pt(size)

    fake_heading("Fernwick Water Department: 2025 Water Quality Report", 18)
    doc.add_paragraph("This report tells you where your water comes from and what our tests found in 2025. "
                      "Your water met every federal and state drinking water standard.")
    fake_heading("Where your water comes from")
    doc.add_paragraph("Fernwick's water comes from three wells near the Fern River. We treat it with chlorine "
                      "and test it every week.")
    add_picture(doc, chart, 6.0, None)
    fake_heading("What we found")
    add_table(doc, ["Substance", "Highest level found", "Allowed limit", "Meets the standard?"],
              [["Lead", "4.1 parts per billion", "15 parts per billion (action level)", "Yes"],
               ["Copper", "0.21 parts per million", "1.3 parts per million (action level)", "Yes"],
               ["Nitrate", "2.4 parts per million", "10 parts per million", "Yes"],
               ["Chlorine", "1.1 parts per million", "4 parts per million", "Yes"]],
              header_row=False, widths=[1.3, 1.7, 2.2, 1.2])
    fake_heading("Questions")
    doc.add_paragraph("Call the Water Department at (555) 010-0140, or come to a Town Council meeting.")
    doc.save(path)


def volunteer_form_docx(path: Path, seal: Path) -> None:
    doc = new_docx("", "Recreation Office", dt.datetime(2025, 8, 18, 13, 0))
    add_picture(doc, seal, 1.0, None)
    run = doc.add_paragraph().add_run("Volunteer Sign-Up Form")
    run.bold = True
    run.font.size = Pt(16)
    doc.add_paragraph("Help at town events, the library and the community garden. Fill in this form and return it "
                      "to Town Hall, or email it to volunteer@fernwick.example.")
    add_table(doc, ["Name:", ""], [["Address:", ""], ["Phone:", ""], ["Email:", ""],
                                   ["I can help with:", "Events / Library / Garden / Senior lunches"],
                                   ["Signature and date:", ""]], header_row=False, widths=[1.8, 4.6])
    doc.save(path)


def tagged_from_docx(docx_path: Path, target: Path, pdfua: bool) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        (pdf,) = convert([docx_path], Path(tmp), tagged=True, pdfua=pdfua)
        shutil.move(str(pdf), str(target))
    with pikepdf.open(target, allow_overwriting_input=True) as pdf:
        pdf.docinfo["/Creator"] = MADE_WITH + " (Word file exported with LibreOffice)"
        pdf.save(target)
    return page_count(target)


# ---------------------------------------------------------------------------
# Excel and PowerPoint
# ---------------------------------------------------------------------------

def pool_schedule_xlsx(path: Path) -> None:
    book = Workbook()
    sheet = book.active  # left as "Sheet" -> renamed to the default-looking "Sheet1"
    sheet.title = "Sheet1"
    sheet.append(["Day", "Lap swim", "Open swim", "Swim lessons"])
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        sheet.append([day, "6 to 8 a.m.", "Noon to 6 p.m.", "9 to 11 a.m."])
    sheet.append(["Saturday", "Closed", "11 a.m. to 7 p.m.", "None"])
    sheet.append(["Sunday", "Closed", "11 a.m. to 7 p.m.", "None"])
    book.properties.creator = "Fernwick Parks and Recreation"
    book.properties.title = None
    book.properties.created = dt.datetime(2026, 4, 2, 9, 0)
    book.save(path)


def budget_pptx(path: Path, chart: Path) -> None:
    deck = Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[0])
    slide.shapes.title.text = "Fiscal Year 2026 Budget"
    slide.placeholders[1].text = "Presentation to the Town Council, May 2025"
    slide = deck.slides.add_slide(deck.slide_layouts[1])
    slide.shapes.title.text = "Where the money comes from"
    body = slide.placeholders[1].text_frame
    body.text = "Property tax: $13.4 million"
    for line in ["State aid: $2.2 million", "Water and sewer charges: $1.7 million", "Fees, grants and other: $1.1 million"]:
        body.add_paragraph().text = line
    slide = deck.slides.add_slide(deck.slide_layouts[5])
    slide.shapes.title.text = "Where the money goes"
    slide.shapes.add_picture(str(chart), PptInches(0.7), PptInches(1.6), width=PptInches(8.6))
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    box = slide.shapes.add_textbox(PptInches(1), PptInches(2.5), PptInches(8), PptInches(2)).text_frame
    box.text = "Questions? Contact the Finance Office at (555) 010-0110."
    box.paragraphs[0].runs[0].font.size = PptPt(28)
    props = deck.core_properties
    props.title = "FY2026 Budget Presentation"
    props.author = "Finance Office, Town of Fernwick"
    props.created = dt.datetime(2025, 5, 6, 18, 0)
    props.modified = dt.datetime(2025, 5, 6, 18, 0)
    deck.save(path)


# ---------------------------------------------------------------------------
# The website
# ---------------------------------------------------------------------------

CSS = """
:root { --ink: #1b1b1b; --link: #0b4f8a; --band: #e8f0f7; }
body { font-family: Georgia, 'Times New Roman', serif; color: var(--ink); margin: 0; line-height: 1.5; }
.skip { position: absolute; left: -999px; } .skip:focus { left: 8px; top: 8px; background: #fff; padding: 4px; }
.demo-note { background: #fff4ce; margin: 0; padding: 8px 16px; font-family: Arial, sans-serif; font-size: 0.9rem; }
header { background: var(--band); padding: 12px 16px; }
.site-name { font-size: 1.6rem; font-weight: bold; margin: 0 0 8px; }
.site-name a { color: var(--ink); text-decoration: none; }
nav ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 18px; }
a { color: var(--link); }
main { max-width: 760px; padding: 8px 16px 32px; }
footer { border-top: 1px solid #ccc; padding: 12px 16px; font-size: 0.9rem; }
"""

NAV = [("index.html", "Home"), ("government/council.html", "Council meetings"), ("government/budget.html", "Budget"),
       ("departments/parks.html", "Parks and recreation"), ("departments/public-works.html", "Public works"),
       ("services/forms.html", "Forms and permits"), ("archive.html", "Archive")]


def write_page(relative: str, title: str, body: str) -> None:
    depth = relative.count("/")
    root = "../" * depth
    nav = "\n".join(f'      <li><a href="{root}{href}">{label}</a></li>' for href, label in NAV)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Town of Fernwick</title>
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<p class="demo-note">Sample website for a fictional town, made to demonstrate a document accessibility check.
Fernwick is not a real place.</p>
<header>
  <p class="site-name"><a href="{root}index.html">Town of Fernwick</a></p>
  <nav aria-label="Main">
    <ul>
{nav}
    </ul>
  </nav>
</header>
<main id="main">
<h1>{title}</h1>
{body.replace('ROOT/', root)}
</main>
<footer>
<p>Town of Fernwick, 12 Mill Street, Fernwick. Phone (555) 010-0100.
ADA coordinator: Town Clerk's office, (555) 010-0100.</p>
</footer>
</body>
</html>
"""
    target = SITE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def build_site() -> None:
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    (SITE / "assets" / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    D = "ROOT/documents/"
    write_page("index.html", "Welcome to Fernwick", f"""
<p>Fernwick is a small river town. Town Hall is open Monday to Friday, 8:30 a.m. to 4:30 p.m.</p>
<h2>News</h2>
<ul>
  <li>The <a href="{D}summer-recreation-guide-2026.pdf">2026 Summer Recreation Guide (PDF)</a> is out.
      Registration opens April 1.</li>
  <li>Read the <a href="{D}water-quality-report-2025.pdf">2025 Water Quality Report</a>.</li>
  <li>The Town Council meets on the second Tuesday of each month. See
      <a href="ROOT/government/council.html">agendas and minutes</a>.</li>
</ul>
<h2>Quick links</h2>
<ul>
  <li><a href="ROOT/services/forms.html">Forms and permits</a></li>
  <li><a href="ROOT/staff-only/index.html">Staff portal</a></li>
</ul>
""")
    write_page("government/council.html", "Council meetings", f"""
<h2>2026 meetings</h2>
<ul>
  <li>March 10, 2026: <a href="{D}council-agenda-2026-03-10.pdf">Agenda (PDF)</a> and
      <a href="{D}council-agenda-2026-03-10-print.pdf">printable agenda</a></li>
  <li>February 10, 2026: <a href="{D}council-minutes-2026-02-10.pdf">Minutes (PDF)</a>.
      To read the approved version, <a href="{D}council-minutes-2026-02-10.pdf">click here</a>.</li>
</ul>
<p>Older agendas and minutes are in the <a href="ROOT/archive.html">archive</a>.</p>
""")
    write_page("government/budget.html", "Budget", f"""
<ul>
  <li><a href="{D}budget-summary-fy2026.pdf">Fiscal Year 2026 budget summary (PDF)</a></li>
  <li><a href="{D}budget-presentation-fy2026.pptx">Budget presentation to the Town Council (PowerPoint)</a></li>
  <li><a href="ROOT/DocumentCenter/View/2041/Fee-Schedule-2026">2026 fee schedule</a></li>
</ul>
""")
    write_page("departments/parks.html", "Parks and recreation", f"""
<ul>
  <li><a href="{D}summer-recreation-guide-2026.pdf">Summer Recreation Guide 2026</a></li>
  <li><a href="{D}pool-schedule-2026.xlsx">Pool schedule (Excel)</a></li>
  <li><a href="{D}volunteer-signup-form.docx">Volunteer sign-up form (Word)</a></li>
</ul>
""")
    write_page("departments/public-works.html", "Public works", f"""
<ul>
  <li><a href="{D}water-quality-report-2025.pdf">2025 Water Quality Report</a></li>
  <li><a href="{D}resolution-2026-14-signed.pdf">Resolution 2026-14, dump truck purchase (signed copy)</a></li>
  <li>State guide to private wells: <a href="https://www.example.org/state-private-well-guide.pdf">download</a></li>
</ul>
""")
    write_page("services/forms.html", "Forms and permits", f"""
<ul>
  <li><a href="{D}building-permit-application.pdf">Building permit application (fillable PDF)</a></li>
  <li><a href="{D}dog-license-application.pdf">Dog license application</a></li>
  <li><a href="{D}volunteer-signup-form.docx">Volunteer sign-up form</a></li>
  <li>For staff: <a href="ROOT/staff-only/timesheet-instructions.pdf">timesheet instructions</a></li>
</ul>
""")
    write_page("archive.html", "Archive", """
<p>Records kept for reference.</p>
<ul><li><a href="ROOT/archive/2019.html">2019 records</a></li></ul>
""")
    write_page("archive/2019.html", "2019 records", f"""
<ul><li><a href="{D}planning-board-minutes-2019-06-18.pdf">Planning Board minutes, June 18, 2019</a></li></ul>
""")
    write_page("notices/public-hearing.html", "Public hearing notice", f"""
<p>This page is not in the menu. It is listed only in the sitemap.</p>
<p><a href="{D}public-hearing-notice-2026-04.pdf">Notice of public hearing on Ordinance 2026-03 (PDF)</a></p>
""")
    write_page("staff-only/index.html", "Staff portal", """
<p><a href="phone-list.pdf">Staff phone list</a></p>
""")
    (SITE / "robots.txt").write_text(
        "# Sample robots.txt for the fictional Town of Fernwick site\n"
        "User-agent: *\nDisallow: /staff-only/\n\nSitemap: {{BASE_URL}}sitemap.xml\n", encoding="utf-8")
    pages = ["index.html", "government/council.html", "government/budget.html", "departments/parks.html",
             "departments/public-works.html", "services/forms.html", "archive.html", "archive/2019.html",
             "notices/public-hearing.html"]
    urls = "\n".join(f"  <url><loc>{{{{BASE_URL}}}}{page}</loc></url>" for page in pages)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    # A link without a file extension, like many town website platforms use.
    routes = {"/DocumentCenter/View/2041/Fee-Schedule-2026": {
        "file": "documents/fee-schedule-2026.pdf", "type": "application/pdf", "filename": "Fee-Schedule-2026.pdf"}}
    (SITE / "routes.json").write_text(json.dumps(routes, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for folder in (SITE, SOURCES):
        if folder.exists():
            shutil.rmtree(folder)
    DOCS.mkdir(parents=True)
    (SITE / "staff-only").mkdir(parents=True)
    SOURCES.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        park, water_chart, spend_chart, seal = (tmp / "park.png", tmp / "water-chart.png",
                                                tmp / "spending-chart.png", tmp / "seal.png")
        park_picture(park)
        bar_chart_picture(water_chart, "Lead found in tap water samples (parts per billion)",
                          ["2021", "2022", "2023", "2024", "2025"], [6.2, 5.8, 5.1, 4.6, 4.1], "")
        bar_chart_picture(spend_chart, "Spending by department ($ millions)",
                          ["Police/fire", "Works", "Benefits", "Gov't", "Water", "Debt"],
                          [5.9, 3.5, 2.5, 1.9, 1.7, 1.4], "")
        seal_picture(seal)

        print("Making untagged PDFs...")
        agenda_pdf(DOCS / "council-agenda-2026-03-10.pdf")
        shutil.copyfile(DOCS / "council-agenda-2026-03-10.pdf", DOCS / "council-agenda-2026-03-10-print.pdf")
        minutes_pdf(DOCS / "council-minutes-2026-02-10.pdf")
        planning_minutes_2019(DOCS / "planning-board-minutes-2019-06-18.pdf")
        budget_pdf(DOCS / "budget-summary-fy2026.pdf")
        fee_schedule_pdf(DOCS / "fee-schedule-2026.pdf")
        hearing_notice_pdf(DOCS / "public-hearing-notice-2026-04.pdf")
        permit_form_pdf(DOCS / "building-permit-application.pdf")
        print("Making the scanned resolution...")
        scan_pdf(DOCS / "resolution-2026-14-signed.pdf")
        small_pdf(SITE / "staff-only" / "timesheet-instructions.pdf", "Timesheet instructions",
                  ["Enter your hours by Friday at noon."], dt.datetime(2026, 1, 5))
        small_pdf(SITE / "staff-only" / "phone-list.pdf", "Staff phone list",
                  ["Internal use only."], dt.datetime(2026, 1, 5))

        print("Making Word sources and tagged PDFs with LibreOffice...")
        agenda_docx(SOURCES / "council-agenda-2026-03-10.docx")
        summer_guide_docx(SOURCES / "summer-recreation-guide-2026.docx", park)
        water_report_docx(SOURCES / "water-quality-report-2025.docx", water_chart)
        pages = tagged_from_docx(SOURCES / "summer-recreation-guide-2026.docx",
                                 DOCS / "summer-recreation-guide-2026.pdf", pdfua=True)
        patch_app_properties(SOURCES / "summer-recreation-guide-2026.docx", MADE_WITH, pages)
        pages = tagged_from_docx(SOURCES / "water-quality-report-2025.docx",
                                 DOCS / "water-quality-report-2025.pdf", pdfua=False)
        patch_app_properties(SOURCES / "water-quality-report-2025.docx", MADE_WITH, pages)
        with tempfile.TemporaryDirectory() as count_dir:
            (agenda_pdf_out,) = convert([SOURCES / "council-agenda-2026-03-10.docx"], Path(count_dir))
            patch_app_properties(SOURCES / "council-agenda-2026-03-10.docx", MADE_WITH, page_count(agenda_pdf_out))

        print("Making Word, Excel and PowerPoint files...")
        volunteer = DOCS / "volunteer-signup-form.docx"
        volunteer_form_docx(volunteer, seal)
        with tempfile.TemporaryDirectory() as count_dir:
            (volunteer_pdf,) = convert([volunteer], Path(count_dir))
            patch_app_properties(volunteer, MADE_WITH, page_count(volunteer_pdf))
        pool_schedule_xlsx(DOCS / "pool-schedule-2026.xlsx")
        budget_pptx(DOCS / "budget-presentation-fy2026.pptx", spend_chart)
        for office_file in (DOCS / "pool-schedule-2026.xlsx", DOCS / "budget-presentation-fy2026.pptx"):
            patch_app_properties(office_file, MADE_WITH)

    print("Making the website...")
    build_site()
    files = sorted(p.relative_to(SAMPLES) for p in SITE.rglob("*") if p.is_file())
    print(f"Done: {len(files)} site files in {SITE.relative_to(KIT)} and the Word sources in {SOURCES.relative_to(KIT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
