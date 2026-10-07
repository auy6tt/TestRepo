#!/usr/bin/env python3
"""Make the portfolio samples, then run the kit on them.

Everything here is FAKE: invented products, companies, people and project.
Every input page carries a large SAMPLE watermark and a SAMPLE banner.

It creates, under samples/:
  sds-binder/        fake safety data sheets (some deliberately messy, old,
                     scanned or missing), a client site list and a cover file,
                     then inventory.xlsx and the SDS binder built from them
  om-handover/       fake datasheets, manuals, warranties, drawings and
                     reports for an HVAC handover binder, plus a filled-in
                     submittal log
  submittal-package/ a small product-data submittal with a review cover

Usage:
  python scripts/make_samples.py
  python scripts/make_samples.py --business "Jane Doe Document Services"
  python scripts/make_samples.py --inputs-only      # don't run the kit

Put your own business name in with --business before showing the samples.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import functools
import io
import random
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    from pypdf import PdfReader, PdfWriter
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (Image as RLImage, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing package '{exc.name}'. Run: pip install -r requirements.txt")

import kitlib
import make_templates

SCRIPTS = Path(__file__).resolve().parent
SAMPLES = kitlib.KIT_DIR / "samples"
SDS_MARK = "SAMPLE \u2014 NOT A REAL SAFETY DATA SHEET"
RED = colors.HexColor("#C62828")
INK = colors.HexColor("#1B1F24")
GREY = colors.HexColor("#5F6670")


# ===========================================================================
# Shared drawing helpers
# ===========================================================================
def diagonal_mark(c, w, h, text, size=None, color=(0.78, 0.12, 0.12), alpha=0.13, angle=40):
    c.saveState()
    c.setFillColorRGB(*color)
    c.setFillAlpha(alpha)
    c.translate(w / 2, h / 2)
    c.rotate(angle)
    size = size or min(64, (w * 1.05) / max(len(text), 1) * 1.75)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(0, -size / 3, text)
    c.restoreState()


def sample_banner(c, w, h, text, color=RED):
    c.saveState()
    c.setFillColor(color)
    c.rect(0, h - 20, w, 20, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(w / 2, h - 13.5, text)
    c.restoreState()


class NumberedCanvas(canvas.Canvas):
    """Canvas that knows the total page count when it draws page decorations."""

    def __init__(self, *args, decorate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []
        self._decorate = decorate

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            if self._decorate:
                self._decorate(self, self._pageNumber, total)
            super().showPage()
        super().save()


def wrap_lines(text, font, size, width):
    return simpleSplit(text, font, size, width)


def draw_paragraph(c, x, y, text, width, font="Helvetica", size=9, lead=12, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    for line in wrap_lines(text, font, size, width):
        c.drawString(x, y, line)
        y -= lead
    return y


def draw_table(c, x, y, widths, rows, size=8.4, lead=11, header_fill=colors.HexColor("#E8ECF1"), pad=4,
               grid=colors.HexColor("#B8C0CA"), header=True, bold_first_col=False):
    """Simple grid table drawn on a canvas. Returns the y below the table."""
    for r, row in enumerate(rows):
        cells = [wrap_lines(str(v), "Helvetica-Bold" if (header and r == 0) else "Helvetica", size, wd - 2 * pad)
                 for v, wd in zip(row, widths)]
        height = max(len(cell) for cell in cells) * lead + 2 * pad - 2
        if header and r == 0:
            c.setFillColor(header_fill)
            c.rect(x, y - height, sum(widths), height, stroke=0, fill=1)
        c.setStrokeColor(grid)
        c.setLineWidth(0.5)
        cx = x
        for col, (cell, wd) in enumerate(zip(cells, widths)):
            c.rect(cx, y - height, wd, height, stroke=1, fill=0)
            bold = (header and r == 0) or (bold_first_col and col == 0)
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.setFillColor(INK)
            ty = y - pad - size + 1
            for line in cell:
                c.drawString(cx + pad, ty, line)
                ty -= lead
            cx += wd
        y -= height
    return y


# ===========================================================================
# GHS-style pictograms (simplified drawings, rendered as images)
# ===========================================================================
@functools.lru_cache(maxsize=None)
def pictogram_png(code: str) -> bytes:
    s = 240
    img = Image.new("RGB", (s, s), "white")
    d = ImageDraw.Draw(img)
    d.polygon([(s / 2, 8), (s - 8, s / 2), (s / 2, s - 8), (8, s / 2)], fill="white", outline=(214, 0, 0), width=17)

    def P(x, y):
        return (x * s, y * s)

    black = (0, 0, 0)
    if code == "GHS02":
        d.rectangle([P(0.32, 0.69), P(0.68, 0.73)], fill=black)
        flame = [P(0.50, 0.20), P(0.56, 0.31), P(0.63, 0.40), P(0.67, 0.50), P(0.66, 0.59), P(0.61, 0.66),
                 P(0.39, 0.66), P(0.34, 0.59), P(0.34, 0.50), P(0.39, 0.42), P(0.44, 0.47), P(0.45, 0.36)]
        d.polygon(flame, fill=black)
        d.polygon([P(0.50, 0.45), P(0.56, 0.54), P(0.55, 0.62), P(0.45, 0.62), P(0.45, 0.54)], fill="white")
    elif code == "GHS07":
        d.rectangle([P(0.455, 0.27), P(0.545, 0.58)], fill=black)
        d.ellipse([P(0.452, 0.63), P(0.548, 0.72)], fill=black)
    elif code == "GHS08":
        d.ellipse([P(0.43, 0.24), P(0.57, 0.38)], fill=black)
        d.polygon([P(0.30, 0.74), P(0.33, 0.50), P(0.42, 0.41), P(0.58, 0.41), P(0.67, 0.50), P(0.70, 0.74)],
                  fill=black)
        cx, cy, r1, r2 = 0.5, 0.585, 0.10, 0.045
        import math
        star = []
        for k in range(16):
            r = r1 if k % 2 == 0 else r2
            a = math.pi / 8 * k
            star.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(star, fill="white")
    elif code == "GHS09":
        d.line([P(0.27, 0.72), P(0.73, 0.72)], fill=black, width=6)
        d.line([P(0.36, 0.72), P(0.36, 0.33)], fill=black, width=8)
        for y1, y2 in ((0.42, 0.33), (0.50, 0.42)):
            d.line([P(0.36, y1), P(0.27, y2)], fill=black, width=6)
            d.line([P(0.36, y1), P(0.45, y2)], fill=black, width=6)
        d.ellipse([P(0.46, 0.57), P(0.66, 0.67)], fill=black)
        d.polygon([P(0.65, 0.62), P(0.73, 0.56), P(0.73, 0.68)], fill=black)
        d.ellipse([P(0.49, 0.60), P(0.52, 0.63)], fill="white")
    elif code == "GHS05":
        d.polygon([P(0.30, 0.26), P(0.38, 0.22), P(0.47, 0.38), P(0.40, 0.42)], fill=black)
        d.polygon([P(0.53, 0.38), P(0.62, 0.22), P(0.70, 0.26), P(0.60, 0.42)], fill=black)
        for x in (0.43, 0.57):
            d.ellipse([P(x - 0.02, 0.47), P(x + 0.02, 0.53)], fill=black)
        d.rectangle([P(0.28, 0.62), P(0.48, 0.70)], fill=black)
        d.rectangle([P(0.52, 0.62), P(0.74, 0.70)], fill=black)
        d.polygon([P(0.52, 0.62), P(0.58, 0.57), P(0.62, 0.62)], fill="white")
    elif code == "GHS06":
        d.ellipse([P(0.38, 0.22), P(0.62, 0.46)], fill=black)
        d.rectangle([P(0.43, 0.42), P(0.57, 0.52)], fill=black)
        d.ellipse([P(0.42, 0.30), P(0.48, 0.36)], fill="white")
        d.ellipse([P(0.52, 0.30), P(0.58, 0.36)], fill="white")
        d.line([P(0.31, 0.56), P(0.69, 0.72)], fill=black, width=12)
        d.line([P(0.31, 0.72), P(0.69, 0.56)], fill=black, width=12)
    elif code == "GHS04":
        d.rounded_rectangle([P(0.27, 0.44), P(0.70, 0.60)], radius=18, fill=black)
        d.rectangle([P(0.70, 0.48), P(0.76, 0.56)], fill=black)
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


def pictogram_reader(code):
    return ImageReader(io.BytesIO(pictogram_png(code)))


# ===========================================================================
# Fake safety data sheets
# ===========================================================================
PLACEHOLDER_SECTIONS = [
    (4, "FIRST-AID MEASURES"), (5, "FIRE-FIGHTING MEASURES"), (6, "ACCIDENTAL RELEASE MEASURES"),
    (7, "HANDLING AND STORAGE"), (8, "EXPOSURE CONTROLS/PERSONAL PROTECTION"),
    (9, "PHYSICAL AND CHEMICAL PROPERTIES"), (10, "STABILITY AND REACTIVITY"), (11, "TOXICOLOGICAL INFORMATION"),
    (12, "ECOLOGICAL INFORMATION"), (13, "DISPOSAL CONSIDERATIONS"), (14, "TRANSPORT INFORMATION"),
    (15, "REGULATORY INFORMATION"),
]


def placeholder_text(title):
    return (f"Sample text only. A real safety data sheet gives the manufacturer's {title.lower()} information "
            "here. This fictional sheet exists only to show how a binder is put together.")


def sds_modern(path, d):
    """Clean, modern 16-section layout built with platypus."""
    styles = {
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8.6, leading=11, textColor=INK),
        "value": ParagraphStyle("value", fontName="Helvetica", fontSize=8.6, leading=11, textColor=INK),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=8.6, leading=11.5, textColor=INK),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7.4, leading=9, textColor=GREY),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK),
        "kicker": ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=10, leading=13,
                                 textColor=colors.HexColor(d["color"])),
        "signal": ParagraphStyle("signal", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=RED),
    }
    width = letter[0] - 1.3 * inch
    story = [Paragraph("SAFETY DATA SHEET", styles["kicker"]), Paragraph(d["product"], styles["title"]),
             Paragraph(d.get("tagline", "Prepared in the 16-section format (sample)."), styles["small"]),
             Spacer(1, 8)]

    def heading(text):
        table = Table([[Paragraph(text, ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=9.4,
                                                        leading=12, textColor=colors.white))]], colWidths=[width])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(d["color"])),
                                   ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return table

    def pairs(rows):
        data = [[Paragraph(k, styles["label"]), Paragraph(v, styles["value"])] for k, v in rows]
        table = Table(data, colWidths=[1.75 * inch, width - 1.75 * inch])
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                                   ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDE2E8"))]))
        return table

    story += [heading("SECTION 1: IDENTIFICATION"), Spacer(1, 4), pairs(d["identification"]), Spacer(1, 9)]
    story += [heading("SECTION 2: HAZARD(S) IDENTIFICATION"), Spacer(1, 4)]
    hazard_rows = [("Classification", d.get("classification", "Sample text only."))]
    if d.get("signal_labelled", True):
        hazard_rows.append(("Signal word", d["signal"]))
    story.append(pairs(hazard_rows))
    if not d.get("signal_labelled", True):
        story += [Spacer(1, 4), Paragraph(d["signal"].upper(), styles["signal"])]
    story += [Spacer(1, 4), Paragraph("<b>Hazard statements</b>", styles["body"])]
    for line in d["hazard_lines"]:
        story.append(Paragraph(line, styles["body"]))
    pictos = d.get("pictograms", [])
    if pictos:
        label = "Hazard pictograms: " + (d.get("pictogram_text", "") if d.get("pictogram_text") else "")
        story += [Spacer(1, 5), Paragraph(f"<b>{label.strip()}</b>", styles["body"]), Spacer(1, 3)]
        images = [RLImage(io.BytesIO(pictogram_png(code)), width=0.62 * inch, height=0.62 * inch) for code in pictos]
        story.append(Table([images], colWidths=[0.75 * inch] * len(images), hAlign="LEFT"))
    story += [Spacer(1, 4), Paragraph("<b>Precautionary statements</b>", styles["body"]),
              Paragraph("Sample text only. A real sheet lists the precautionary statements here.", styles["body"]),
              Spacer(1, 9)]
    story += [heading("SECTION 3: COMPOSITION/INFORMATION ON INGREDIENTS"), Spacer(1, 4)]
    comp = [["Ingredient", "CAS No.", "Weight %"]] + d.get("ingredients", [
        ["Sample ingredient A", "000-00-0", "40-60"], ["Sample ingredient B", "000-00-0", "10-30"]])
    comp_table = Table(comp, colWidths=[width * 0.55, width * 0.25, width * 0.20])
    comp_table.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.4),
                                    ("FONT", (0, 1), (-1, -1), "Helvetica", 8.4),
                                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C0CA")),
                                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1F5"))]))
    story += [comp_table, Spacer(1, 9)]
    for number, title in PLACEHOLDER_SECTIONS:
        story.append(KeepTogether([heading(f"SECTION {number}: {title}"), Spacer(1, 3),
                                   Paragraph(placeholder_text(title), styles["body"]), Spacer(1, 7)]))
    story.append(KeepTogether([heading("SECTION 16: OTHER INFORMATION"), Spacer(1, 3), pairs(d["other"]),
                               Spacer(1, 4),
                               Paragraph("This is a fictional sample made to demonstrate a binder service. It is "
                                         "not a safety data sheet and must not be used for any product.",
                                         styles["small"])]))

    def decorate(c, page, total):
        w, h = letter
        sample_banner(c, w, h, SDS_MARK + "  \u00b7  FICTIONAL PRODUCT AND COMPANY")
        c.setFont("Helvetica", 7.4)
        c.setFillColor(GREY)
        c.drawString(0.65 * inch, 0.45 * inch, f"{d['product']}  \u00b7  {d['footer']}")
        c.drawRightString(w - 0.65 * inch, 0.45 * inch, f"Page {page} of {total}")
        diagonal_mark(c, w, h, SDS_MARK)

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.65 * inch, rightMargin=0.65 * inch,
                            topMargin=0.62 * inch, bottomMargin=0.7 * inch, title=d["product"] + " (SAMPLE)",
                            author=d["company"] + " (fictional)")
    doc.build(story, canvasmaker=functools.partial(NumberedCanvas, decorate=decorate))


def sds_two_column(path, d):
    """Label column and value column drawn separately (text order differs from reading order)."""
    w, h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle(d["product"] + " (SAMPLE)")
    pages = d["pages"]
    for number, sections in enumerate(pages, start=1):
        y = h - 70
        if number == 1:
            c.setFont("Helvetica-Bold", 20)
            c.setFillColor(colors.HexColor(d["color"]))
            c.drawString(54, y, d["company_short"])
            c.setFont("Helvetica", 9)
            c.setFillColor(GREY)
            c.drawRightString(w - 54, y + 4, "Safety Data Sheet")
            y -= 34
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 15)
            c.drawString(54, y, d["product"])
            y -= 26
        for title, rows in sections:
            c.setFillColor(colors.HexColor("#EEF1F5"))
            c.rect(54, y - 5, w - 108, 18, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 9.6)
            c.drawString(60, y, title)
            y -= 22
            if isinstance(rows, str):
                y = draw_paragraph(c, 60, y, rows, w - 120, size=8.6, lead=11.5) - 8
                continue
            # all labels first, then all values: a different text order from the visual one
            row_y, heights = y, []
            for label, value in rows:
                lines = wrap_lines(value, "Helvetica", 8.8, w - 54 - 230)
                heights.append(max(1, len(lines)) * 12 + 3)
            c.setFont("Helvetica-Bold", 8.8)
            for (label, _), height in zip(rows, heights):
                c.drawString(60, row_y, label)
                row_y -= height
            row_y = y
            c.setFont("Helvetica", 8.8)
            for (_, value), height in zip(rows, heights):
                ty = row_y
                for line in wrap_lines(value, "Helvetica", 8.8, w - 54 - 230):
                    c.drawString(230, ty, line)
                    ty -= 12
                row_y -= height
            y = row_y - 10
        sample_banner(c, w, h, SDS_MARK + "  \u00b7  FICTIONAL PRODUCT AND COMPANY")
        c.setFont("Helvetica", 7.4)
        c.setFillColor(GREY)
        c.drawString(54, 32, f"{d['product']}  \u00b7  {d['footer']}")
        c.drawRightString(w - 54, 32, f"Page {number} of {len(pages)}")
        diagonal_mark(c, w, h, SDS_MARK)
        c.showPage()
    c.save()


def sds_messy(path, d):
    """Letter-spaced headings, run-together codes, hyphenated lines, mixed date style."""
    w, h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle("Microsoft Word - primer_sds_final_v3.docx")

    def spaced_heading(text, y):
        letters = "  ".join(" ".join(word) for word in text.split(" "))
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(INK)
        c.drawString(54, y, letters)
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.line(54, y - 4, w - 54, y - 4)
        return y - 20

    def lines(items, y, size=8.8, lead=12, x=60):
        c.setFont("Helvetica", size)
        c.setFillColor(INK)
        for item in items:
            c.drawString(x, y, item)
            y -= lead
        return y - 6

    for page, blocks in enumerate(d["pages"], start=1):
        y = h - 64
        if page == 1:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(54, y, "SAFETY DATA SHEET")
            c.setFont("Helvetica", 8)
            c.drawRightString(w - 54, y, "Revised: " + d["date_text"] + "    Version 2")
            y -= 26
        for kind, payload in blocks:
            if kind == "heading":
                y = spaced_heading(payload, y)
            else:
                y = lines(payload, y)
        sample_banner(c, w, h, SDS_MARK + "  \u00b7  FICTIONAL PRODUCT AND COMPANY")
        c.setFont("Helvetica", 7.4)
        c.setFillColor(GREY)
        c.drawString(54, 32, d["product"] + "  \u00b7  " + d["footer"])
        c.drawRightString(w - 54, 32, f"Page {page} of {len(d['pages'])}")
        diagonal_mark(c, w, h, SDS_MARK)
        c.showPage()
    c.save()


def sds_old_msds(path, d):
    """Old OSHA-174 style MSDS form with roman-numeral sections."""
    w, h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle("MSDS (SAMPLE)")
    y = h - 62
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(INK)
    c.drawString(54, y, "MATERIAL SAFETY DATA SHEET")
    c.setFont("Helvetica", 7.6)
    c.drawString(54, y - 13, "May be used to comply with OSHA's Hazard Communication Standard, 29 CFR 1910.1200 "
                             "(old form layout, reproduced as a fictional sample)")
    y -= 36
    c.setLineWidth(0.8)
    c.rect(54, y - 22, w - 108, 30, stroke=1, fill=0)
    c.setFont("Helvetica", 8.6)
    c.drawString(60, y - 2, "IDENTITY (As Used on Label and List): " + d["product"])
    c.setFont("Helvetica", 7)
    c.drawString(60, y - 15, "Note: Blank spaces are not permitted. If any item is not applicable, the space "
                             "must be marked to indicate that.")
    y -= 40
    for title, rows in d["sections"]:
        c.setFillColor(colors.HexColor("#D9D9D9"))
        c.rect(54, y - 4, w - 108, 15, stroke=1, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 8.8)
        c.drawString(60, y, title)
        y -= 16
        box_top = y + 10
        c.setFont("Helvetica", 8.6)
        for row in rows:
            c.drawString(62, y - 2, row)
            y -= 13
        c.rect(54, y + 3, w - 108, box_top - y - 3, stroke=1, fill=0)
        y -= 14
    sample_banner(c, w, h, "SAMPLE \u2014 NOT A REAL MSDS  \u00b7  FICTIONAL PRODUCT AND COMPANY")
    diagonal_mark(c, w, h, "SAMPLE \u2014 NOT A REAL SAFETY DATA SHEET")
    c.setFont("Helvetica", 7.4)
    c.setFillColor(GREY)
    c.drawString(54, 32, d["product"] + "  \u00b7  Page 1 of 1")
    c.showPage()
    c.save()


def _font(size, bold=False):
    names = ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
             "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"]
    for folder in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
                   "/usr/share/fonts/dejavu", "/Library/Fonts", "C:/Windows/Fonts"):
        for name in names:
            candidate = Path(folder) / name
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def sds_scanned(path, d):
    """A 'scanned' sheet: each page is only a picture, so there is no text to read."""
    rng = random.Random(7)
    w, h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    for number, blocks in enumerate(d["pages"], start=1):
        img = Image.new("L", (1275, 1650), 250)
        draw = ImageDraw.Draw(img)
        y = 120
        if number == 1:
            draw.text((110, y), "SAFETY DATA SHEET", font=_font(40, True), fill=20)
            y += 64
            draw.text((110, y), d["product"], font=_font(32, True), fill=25)
            y += 60
        for kind, payload in blocks:
            if kind == "heading":
                draw.rectangle([105, y - 6, 1170, y + 34], fill=215)
                draw.text((115, y), payload, font=_font(24, True), fill=15)
                y += 52
            else:
                for line in payload:
                    draw.text((120, y), line, font=_font(22), fill=35)
                    y += 33
                y += 14
        draw.text((110, 1560), f"{d['product']}  -  Page {number} of {len(d['pages'])}", font=_font(18), fill=90)
        mark_font = _font(60, True)
        left, top, right, bottom = ImageDraw.Draw(img).textbbox((0, 0), SDS_MARK, font=mark_font)
        mark = Image.new("L", (right - left + 40, bottom - top + 40), 0)
        ImageDraw.Draw(mark).text((20 - left, 20 - top), SDS_MARK, font=mark_font, fill=255)
        mark = mark.rotate(40, expand=True)
        shade = Image.new("L", mark.size, 175)
        img.paste(shade, (int((1275 - mark.size[0]) / 2), int((1650 - mark.size[1]) / 2)), mark)
        img = img.rotate(0.6, fillcolor=250, resample=Image.BICUBIC)
        pixels = img.load()
        for _ in range(9000):
            x, yy = rng.randrange(1275), rng.randrange(1650)
            pixels[x, yy] = rng.randrange(150, 235)
        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=58)
        buffer.seek(0)
        c.drawImage(ImageReader(buffer), 0, 0, width=w, height=h)
        sample_banner(c, w, h, SDS_MARK + "  \u00b7  SCANNED-IMAGE EXAMPLE")
        diagonal_mark(c, w, h, SDS_MARK, alpha=0.05)
        c.showPage()
    c.save()


def two_column_pages(first_page, closing):
    rest = [(f"{n}. {t}", placeholder_text(t)) for n, t in PLACEHOLDER_SECTIONS]
    return [first_page, rest[:6], rest[6:] + [("16. OTHER INFORMATION", closing)]]


def fake_sds_set():
    """The fictional products in the SDS sample. Each one tests something."""
    two_col_common = "This fictional sample shows how a binder is put together. It is not a safety data sheet."
    sets = [
        ("Corvane_CB-200_Brake-Parts-Cleaner_SDS_US_EN.pdf", sds_modern, {
            "product": "Corvane Brake Parts Cleaner (Non-Chlorinated)", "company": "Corvane Automotive Chemicals, Inc.",
            "color": "#8E1B1B", "footer": "Revision date: 2025-03-14",
            "identification": [
                ("Product name:", "Corvane Brake Parts Cleaner (Non-Chlorinated)"),
                ("Product code:", "CB-200 (14 oz aerosol)"),
                ("Recommended use:", "Sample text only"),
                ("Manufacturer:", "Corvane Automotive Chemicals, Inc."),
                ("Address:", "100 Example Street, Sampletown, ST 00000"),
                ("Emergency telephone:", "555-0142 (fictional number)"),
                ("Revision date:", "2025-03-14"), ("Version:", "3.1")],
            "signal": "Danger",
            "hazard_lines": ["H222 Extremely flammable aerosol.", "H229 Pressurized container: may burst if heated.",
                             "H315 Causes skin irritation.", "H336 May cause drowsiness or dizziness.",
                             "H411 Toxic to aquatic life with long lasting effects."],
            "pictograms": ["GHS02", "GHS07", "GHS09"],
            "pictogram_text": "GHS02 Flame, GHS07 Exclamation mark, GHS09 Environment",
            "other": [("Revision date:", "2025-03-14"), ("Changes:", "Sample text only")],
        }),
        ("lanternfly-tire-shine-sds.pdf", sds_modern, {
            "product": "Lanternfly Tire Shine Spray", "company": "Lanternfly Car Care Co.", "color": "#2E5E3A",
            "footer": "Revision date: 2026-01-12",
            "identification": [
                ("Product name:", "Lanternfly Tire Shine Spray"), ("Product code:", "LF-TS-16"),
                ("Manufacturer:", "Lanternfly Car Care Co."),
                ("Address:", "48 Placeholder Lane, Mocktown, ST 00000"),
                ("Emergency telephone:", "555-0163 (fictional number)"),
                ("Revision date:", "2026-01-12"), ("Version:", "1.2")],
            "signal": "Warning",
            "hazard_lines": ["H223 Flammable aerosol.", "H229 Pressurized container: may burst if heated.",
                             "H412 Harmful to aquatic life with long lasting effects."],
            "pictograms": ["GHS02"], "pictogram_text": "GHS02 Flame",
            "other": [("Revision date:", "2026-01-12")],
        }),
        ("Bluepeak_Washer_Fluid_-20F_SDS.pdf", sds_modern, {
            "product": "Bluepeak All-Season Windshield Washer Fluid -20\u00b0F",
            "company": "Bluepeak Consumer Products Co.", "color": "#1E4E8C",
            "footer": "Revision date 02/14/2023", "tagline": "US format sample. Hazard statements shown without codes.",
            "identification": [
                ("Product Name", "Bluepeak All-Season Windshield Washer Fluid -20\u00b0F"),
                ("Other means of identification", "BP-WWF-20"),
                ("Supplier", "Bluepeak Consumer Products Co."),
                ("Address", "9 Mockingbird Way, Sampleton, ST 00000"),
                ("Emergency phone", "555-0118 (fictional number)"),
                ("Revision date", "02/14/2023")],
            "signal": "Danger",
            "hazard_lines": ["Highly flammable liquid and vapor.",
                             "Toxic if swallowed, in contact with skin or if inhaled.",
                             "Causes damage to organs (eyes, central nervous system)."],
            "pictograms": ["GHS02", "GHS06", "GHS08"],
            "pictogram_text": "Flame, Skull and crossbones, Health hazard",
            "other": [("Revision date", "02/14/2023"), ("Prepared by", "Sample regulatory team (fictional)")],
        }),
        ("HALBERD-RUST-PENETRANT-SDS-2019.pdf", sds_modern, {
            "product": "Halberd Rust Penetrant Aerosol", "company": "Halberd Tool & Chemical Corp.",
            "color": "#4A4A4A", "footer": "Revision Date: June 30, 2019",
            "identification": [
                ("Product name:", "Halberd Rust Penetrant Aerosol"), ("Product code:", "HTC-RP-11"),
                ("Manufacturer:", "Halberd Tool & Chemical Corp."),
                ("Address:", "3 Imaginary Industrial Park, Exampleburg, ST 00000"),
                ("Emergency telephone:", "555-0129 (fictional number)"),
                ("Revision Date:", "June 30, 2019"), ("Version:", "1.0")],
            "signal": "Danger", "signal_labelled": False,
            "hazard_lines": ["H222 Extremely flammable aerosol.", "H229 Pressurized container: may burst if heated.",
                             "H304 May be fatal if swallowed and enters airways.",
                             "H336 May cause drowsiness or dizziness."],
            "pictograms": ["GHS02", "GHS07", "GHS08"],
            "other": [("Revision Date:", "June 30, 2019")],
        }),
        ("ironvale-5w30-synthetic-sds.pdf", sds_two_column, {
            "product": "Ironvale Synthetic Motor Oil 5W-30", "company_short": "IRONVALE LUBRICANTS",
            "color": "#6B4E16", "footer": "Revision date 11/22/2024",
            "page1": [
                ("1. IDENTIFICATION", [("Product name", "Ironvale Synthetic Motor Oil 5W-30"),
                                       ("Product number", "IV-530-Q"),
                                       ("Recommended use", "Sample text only"),
                                       ("Supplier", "Ironvale Lubricants LLC"),
                                       ("Address", "7 Sample Road, Exampleville, ST 00000"),
                                       ("Emergency phone", "555-0155 (fictional number)"),
                                       ("Revision date", "11/22/2024")]),
                ("2. HAZARD(S) IDENTIFICATION", [("Classification", "Not classified as hazardous (sample text)"),
                                                 ("Signal word", "None"), ("Hazard statements", "None"),
                                                 ("Pictograms", "None")]),
                ("3. COMPOSITION/INFORMATION ON INGREDIENTS", [("Sample base oil", "000-00-0   70-90 %"),
                                                               ("Sample additive", "000-00-0   10-30 %")]),
            ],
        }),
        ("Gristmill-HD-Degreaser-GM-HD-5-SDS.pdf", sds_two_column, {
            "product": "Gristmill Heavy-Duty Degreaser Concentrate", "company_short": "GRISTMILL",
            "color": "#0E6B6B", "footer": "Issue date 2025-08-21",
            "page1": [
                ("1. IDENTIFICATION", [("Product name", "Gristmill Heavy-Duty Degreaser Concentrate"),
                                       ("Product code", "GM-HD-5"),
                                       ("Manufacturer", "Gristmill Cleaning Solutions, Inc."),
                                       ("Address", "250 Fictional Avenue, Sampleport, ST 00000"),
                                       ("Emergency phone", "555-0171 (fictional number)"),
                                       ("Issue date", "2025-08-21"), ("Supersedes", "2022-01-10")]),
                ("2. HAZARD(S) IDENTIFICATION", [("Signal word", "Danger"),
                                                 ("Hazard statements", "H290 May be corrosive to metals. "
                                                                       "H314 Causes severe skin burns and eye damage."),
                                                 ("Pictograms", "GHS05 Corrosion"),
                                                 ("Precautionary statements", "Sample text only")]),
                ("3. COMPOSITION/INFORMATION ON INGREDIENTS", [("Sample ingredient C", "000-00-0   5-10 %"),
                                                               ("Sample ingredient D", "000-00-0   1-5 %")]),
            ],
        }),
        ("saltmarsh_primer_gray_sds.pdf", sds_messy, {
            "product": "SALTMARSH AUTOMOTIVE PRIMER - GRAY", "date_text": "14.02.2023",
            "footer": "Saltmarsh Coatings Ltd. (fictional)",
            "pages": [[
                ("heading", "SECTION 1: IDENTIFICATION"),
                ("lines", ["Trade name: SALTMARSH AUTOMOTIVE PRIMER - GRAY", "Product no.: SC-PR-G1",
                           "Supplier: Saltmarsh Coatings Ltd. 22 Harbour Road, Sampleton",
                           "Emergency: 555-0190 (fictional number)", "Revised: 14.02.2023"]),
                ("heading", "SECTION 2: HAZARDS IDENTIFICATION"),
                ("lines", ["Signal word Danger",
                           "Hazard statements: H225; H 319; H302 + H332; H336; H373 May cause damage to organs",
                           "through prolonged or repeated exposure. Highly flammable liquid and vapour. May cause drowsi-",
                           "ness or dizziness.",
                           "Hazard pictograms: GHS02, GHS07, GHS08",
                           "Precautionary statements: sample text only."]),
                ("heading", "SECTION 3: COMPOSITION"),
                ("lines", ["Sample solvent E    000-00-0    25-50 %    H225, H319, H336",
                           "Sample resin F      000-00-0    10-25 %    H312, H315"]),
            ], [
                ("heading", "SECTION 4: FIRST AID"),
                ("lines", ["Sample text only. A real sheet gives first-aid information here."]),
                ("heading", "SECTIONS 5 TO 15"),
                ("lines", ["Sample text only. This fictional sheet leaves out sections 5 to 15."]),
                ("heading", "SECTION 16: OTHER INFORMATION"),
                ("lines", ["Full text of H-statements in section 3:",
                           "H225 Highly flammable liquid and vapour. H312 Harmful in contact with skin.",
                           "H315 Causes skin irritation. H319 Causes serious eye irritation.",
                           "Revised: 14.02.2023 (fictional sample)"]),
            ]],
        }),
        ("tri-county-hand-cleaner-msds.pdf", sds_old_msds, {
            "product": "TRI-COUNTY HAND CLEANER W/ PUMICE",
            "sections": [
                ("Section I - Manufacturer's Information", [
                    "Manufacturer's Name: Tri-County Soap Works", "Address: 61 Example Mill Road, Oldtown, ST 00000",
                    "Emergency Telephone Number: 555-0177 (fictional)", "Date Prepared: 04/12/2008"]),
                ("Section II - Hazardous Ingredients/Identity Information", ["Sample text only."]),
                ("Section III - Physical/Chemical Characteristics", ["Sample text only."]),
                ("Section IV - Fire and Explosion Hazard Data", ["Sample text only."]),
                ("Section V - Reactivity Data", ["Sample text only."]),
                ("Section VI - Health Hazard Data", ["Sample text only."]),
                ("Section VII - Precautions for Safe Handling and Use", ["Sample text only."]),
                ("Section VIII - Control Measures", ["Sample text only."]),
            ],
        }),
        ("pemberton-glass-cleaner.pdf", sds_scanned, {
            "product": "Pemberton Glass Cleaner",
            "pages": [[
                ("heading", "SECTION 1: IDENTIFICATION"),
                ("lines", ["Product name: Pemberton Glass Cleaner", "Manufacturer: Pemberton Household Supply (fictional)",
                           "Revision date: 2024-09-03"]),
                ("heading", "SECTION 2: HAZARD(S) IDENTIFICATION"),
                ("lines", ["Signal word: Warning", "H319 Causes serious eye irritation.",
                           "Sample text only. This page is a picture, so no text can be read from it."]),
            ], [
                ("heading", "SECTIONS 3 TO 16"),
                ("lines", ["Sample text only. A real sheet continues here."]),
            ]],
        }),
    ]
    for _, maker, data in sets:
        if maker is sds_two_column:
            closing = (f"{data['footer']}. " if data["footer"].startswith("Issue") else "") + two_col_common
            data["pages"] = two_column_pages(data.pop("page1"), closing)
    return sets


SITE_LIST_ROWS = [
    ("Corvane Brake Parts Cleaner (Non-Chlorinated)", "Corvane", "Service Bays", "14 oz aerosol", "24", "Yes", "", ""),
    ("Halberd Rust Penetrant", "Halberd", "Service Bays", "11 oz aerosol", "12", "Yes", "", ""),
    ("Ironvale Synthetic Motor Oil 5W-30", "Ironvale", "Service Bays", "5 qt jug", "10", "Yes", "", ""),
    ("Ridgeback R-1234yf Refrigerant", "Ridgeback", "Service Bays", "10 lb cylinder", "2", "Yes", "",
     "Requested from supplier"),
    ("Bluepeak Washer Fluid -20", "Bluepeak", "Service Bays", "1 gal jug", "18", "Yes", "", ""),
    ("Saltmarsh Automotive Primer - Gray", "Saltmarsh", "Paint & Body Room", "1 qt can", "4", "Yes", "", ""),
    ("Gristmill HD Degreaser Concentrate", "Gristmill", "Parts Washer & Storage", "5 gal pail", "2", "Yes", "", ""),
    ("Tri-County Hand Cleaner w/ Pumice", "Tri-County", "Office & Janitorial", "4.5 lb tub", "3", "Yes", "", ""),
    ("Pemberton Glass Cleaner", "Pemberton", "Office & Janitorial", "32 oz spray", "6", "Yes",
     "pemberton-glass-cleaner.pdf", "Scanned copy from the client"),
    ("Corvane Carb & Choke Cleaner", "Corvane", "Service Bays", "12 oz aerosol", "0", "No", "",
     "No longer used (client, 2026-09)"),
]


# ===========================================================================
# Fake construction documents
# ===========================================================================
def page_frame(c, w, h, brand, brand_color, label, mark, footer_left, page=None, pages=None):
    c.setFillColor(colors.HexColor(brand_color))
    c.rect(0, h - 58, w, 58, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h - 36, brand)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(w - 40, h - 34, label)
    sample_banner(c, w, h, mark, color=colors.HexColor("#B71C1C"))
    c.setFont("Helvetica", 7.2)
    c.setFillColor(GREY)
    c.drawString(40, 32, footer_left)
    if page:
        c.drawRightString(w - 40, 32, f"Page {page} of {pages}")
    diagonal_mark(c, w, h, mark.split("  ")[0], alpha=0.10)


def unit_sketch(c, x, y, kind, color):
    """Very simple product drawing for the datasheets."""
    c.setStrokeColor(colors.HexColor("#3C4650"))
    c.setFillColor(colors.HexColor("#E9EDF2"))
    c.setLineWidth(1.2)
    if kind == "rtu":
        c.rect(x, y, 190, 90, stroke=1, fill=1)
        c.rect(x + 10, y + 10, 60, 70, stroke=1, fill=0)
        for i in range(3):
            c.circle(x + 105 + i * 30, y + 70, 12, stroke=1, fill=0)
        for i in range(6):
            c.line(x + 92 + i * 15, y + 12, x + 92 + i * 15, y + 50)
    elif kind == "fan":
        c.rect(x + 20, y + 25, 150, 50, stroke=1, fill=1)
        c.circle(x + 95, y + 50, 20, stroke=1, fill=0)
        c.rect(x, y + 35, 20, 30, stroke=1, fill=1)
        c.rect(x + 170, y + 35, 20, 30, stroke=1, fill=1)
    elif kind == "vav":
        c.rect(x + 40, y + 20, 120, 60, stroke=1, fill=1)
        c.circle(x + 25, y + 50, 18, stroke=1, fill=1)
        c.rect(x + 160, y + 30, 30, 40, stroke=1, fill=1)
    else:
        c.roundRect(x + 55, y + 5, 80, 90, 8, stroke=1, fill=1)
        c.setFillColor(colors.HexColor(color))
        c.rect(x + 68, y + 50, 54, 30, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + 95, y + 60, "72\u00b0")
    c.setFont("Helvetica", 7)
    c.setFillColor(GREY)
    c.drawString(x, y - 12, "Illustration only (sample).")


def datasheet(path, p, size=letter):
    w, h = size
    c = canvas.Canvas(str(path), pagesize=size)
    c.setTitle(f"{p['product']} - product data (SAMPLE)")
    mark = "SAMPLE DATASHEET  \u2014  NOT A REAL PRODUCT  \u00b7  FICTIONAL MANUFACTURER"
    pages = 2 if p.get("specs2") else 1
    page_frame(c, w, h, p["brand"], p["color"], "PRODUCT DATA", mark,
               f"{p['brand']} (fictional)  \u00b7  Form {p['form']}  \u00b7  Sample values only", 1, pages)
    y = h - 96
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, y, p["product"])
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GREY)
    c.drawString(40, y - 18, p["subtitle"])
    y -= 46
    y = draw_paragraph(c, 40, y, p["intro"], w - 300, size=9.4, lead=13)
    unit_sketch(c, w - 245, h - 250, p["sketch"], p["color"])
    y = min(y, h - 270) - 6
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor(p["color"]))
    c.drawString(40, y, "FEATURES")
    y -= 15
    for feature in p["features"]:
        c.setFillColor(INK)
        c.circle(45, y + 3, 1.6, stroke=0, fill=1)
        y = draw_paragraph(c, 53, y, feature, w - 100, size=9, lead=12) - 2
    y -= 8
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor(p["color"]))
    c.drawString(40, y, "SPECIFICATIONS (SAMPLE VALUES)")
    y -= 8
    draw_table(c, 40, y, [190, w - 80 - 190], [["Item", "Value"]] + p["specs"], bold_first_col=True)
    c.showPage()
    if pages == 2:
        page_frame(c, w, h, p["brand"], p["color"], "PRODUCT DATA", mark,
                   f"{p['brand']} (fictional)  \u00b7  Form {p['form']}  \u00b7  Sample values only", 2, 2)
        y = h - 96
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(colors.HexColor(p["color"]))
        c.drawString(40, y, "PERFORMANCE AND ELECTRICAL DATA (SAMPLE VALUES)")
        y = draw_table(c, 40, y - 8, [150, 110, 110, w - 80 - 370], p["specs2"]) - 24
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(40, y, "DIMENSIONS")
        y -= 20
        c.setStrokeColor(INK)
        c.setLineWidth(1)
        c.rect(80, y - 130, 260, 120, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(80, y - 145, 340, y - 145)
        c.setFont("Helvetica", 8)
        c.setFillColor(INK)
        c.drawCentredString(210, y - 155, p.get("dims", "Length (sample)"))
        c.line(355, y - 130, 355, y - 10)
        c.drawString(362, y - 72, "Height (sample)")
        c.setFont("Helvetica", 7.6)
        c.setFillColor(GREY)
        c.drawString(40, y - 185, "All values on this page are invented for a sample. Not for design or ordering.")
        c.showPage()
    c.save()


def manual(path, p, size=letter):
    w, h = size
    c = canvas.Canvas(str(path), pagesize=size)
    c.setTitle(f"{p['product']} - IOM manual (SAMPLE)")
    mark = "SAMPLE MANUAL  \u2014  NOT A REAL PRODUCT  \u00b7  FICTIONAL MANUFACTURER"
    chapters = p["chapters"]
    total = 2 + len(chapters)
    footer = f"{p['brand']} (fictional)  \u00b7  {p['manual_no']}"
    # cover
    c.setFillColor(colors.HexColor(p["color"]))
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(50, h - 200, p["brand"])
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, h - 260, p["product"])
    c.setFont("Helvetica", 14)
    c.drawString(50, h - 285, "Installation, Operation and Maintenance Manual")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 310, p["manual_no"])
    sample_banner(c, w, h, mark, color=colors.HexColor("#B71C1C"))
    diagonal_mark(c, w, h, "SAMPLE MANUAL", color=(1, 1, 1), alpha=0.18)
    c.bookmarkPage("cover")
    c.addOutlineEntry("Cover", "cover", level=0)
    c.showPage()
    # contents
    page_frame(c, w, h, p["brand"], p["color"], "IOM MANUAL", mark, footer, 2, total)
    c.bookmarkPage("contents")
    c.addOutlineEntry("Contents", "contents", level=0)
    y = h - 100
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(INK)
    c.drawString(50, y, "Contents")
    y -= 30
    c.setFont("Helvetica", 10.5)
    for n, (title, _) in enumerate(chapters, start=1):
        c.drawString(60, y, f"{n}   {title}")
        c.drawRightString(w - 60, y, str(n + 2))
        y -= 18
    c.showPage()
    for n, (title, body) in enumerate(chapters, start=1):
        page_frame(c, w, h, p["brand"], p["color"], "IOM MANUAL", mark, footer, n + 2, total)
        key = f"ch{n}"
        c.bookmarkPage(key)
        c.addOutlineEntry(f"{n} {title}", key, level=0)
        y = h - 100
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(p["color"]))
        c.drawString(50, y, f"{n}  {title}")
        y -= 26
        for block in body:
            if isinstance(block, list):
                y = draw_table(c, 50, y, [w * 0.42, w * 0.20, w - 100 - w * 0.62], block) - 14
            else:
                y = draw_paragraph(c, 50, y, block, w - 100, size=9.6, lead=13.5) - 8
        c.showPage()
    c.showOutline()
    c.save()


def warranty(path, p, size=letter):
    w, h = size
    c = canvas.Canvas(str(path), pagesize=size)
    c.setTitle(f"{p['brand']} warranty (SAMPLE)")
    mark = "SAMPLE WARRANTY  \u2014  NOT A REAL PRODUCT  \u00b7  FICTIONAL MANUFACTURER"
    c.setStrokeColor(colors.HexColor(p["color"]))
    c.setLineWidth(3)
    c.rect(30, 40, w - 60, h - 90, stroke=1, fill=0)
    c.setLineWidth(0.8)
    c.rect(38, 48, w - 76, h - 106, stroke=1, fill=0)
    c.setFillColor(colors.HexColor(p["color"]))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w / 2, h - 110, p["brand"])
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(w / 2, h - 145, "LIMITED WARRANTY CERTIFICATE")
    c.setFont("Helvetica", 9)
    c.setFillColor(GREY)
    c.drawCentredString(w / 2, h - 162, "Sample document. Terms below are invented and have no legal effect.")
    y = h - 210
    for label, value in p["fields"]:
        c.setFont("Helvetica-Bold", 9.6)
        c.setFillColor(INK)
        c.drawString(80, y, label)
        c.setFont("Helvetica", 9.6)
        c.drawString(250, y, value)
        c.setStrokeColor(colors.HexColor("#C9D0D8"))
        c.setLineWidth(0.4)
        c.line(250, y - 4, w - 80, y - 4)
        y -= 24
    y -= 10
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(80, y, "Coverage (sample terms)")
    y -= 18
    for line in p["coverage"]:
        y = draw_paragraph(c, 90, y, "- " + line, w - 180, size=9.4, lead=13) - 3
    y -= 30
    c.setStrokeColor(INK)
    c.line(80, y, 280, y)
    c.line(w - 280, y, w - 80, y)
    c.setFont("Helvetica", 8.6)
    c.drawString(80, y - 13, "Authorized representative (fictional)")
    c.drawString(w - 280, y - 13, "Date")
    sample_banner(c, w, h, mark, color=colors.HexColor("#B71C1C"))
    diagonal_mark(c, w, h, "SAMPLE WARRANTY", alpha=0.10)
    c.showPage()
    c.save()


def table_doc(path, title, subtitle, columns, rows, widths, company, notes=None, rotated_rows=None):
    """A contractor-prepared table document. rotated_rows adds a landscape page stored with /Rotate 90."""
    w, h = letter
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    mark = "SAMPLE DOCUMENT  \u2014  FICTIONAL PROJECT  \u00b7  NOT FOR USE"
    pages = 2 if rotated_rows else 1

    def header(cw, ch, page):
        c.setFillColor(colors.HexColor("#33475B"))
        c.rect(0, ch - 58, cw, 58, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, ch - 36, company)
        c.setFont("Helvetica", 8)
        c.drawRightString(cw - 40, ch - 48, "Harborview Family Clinic (fictional) \u00b7 Project 2026-014")
        sample_banner(c, cw, ch, mark, color=colors.HexColor("#B71C1C"))
        c.setFont("Helvetica", 7.2)
        c.setFillColor(GREY)
        c.drawString(40, 32, f"{title}  \u00b7  sample document")
        c.drawRightString(cw - 40, 32, f"Page {page} of {pages}")

    header(w, h, 1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(40, h - 96, title)
    c.setFont("Helvetica", 9.5)
    c.setFillColor(GREY)
    c.drawString(40, h - 113, subtitle)
    y = draw_table(c, 40, h - 128, widths, [columns] + rows)
    if notes:
        y -= 18
        for note in notes:
            y = draw_paragraph(c, 40, y, note, w - 80, size=8.6, lead=11.5, color=GREY) - 4
    diagonal_mark(c, w, h, "SAMPLE DOCUMENT", alpha=0.08)
    c.showPage()
    if rotated_rows:
        # Draw a landscape page inside a portrait page; the page is rotated afterwards.
        c.saveState()
        c.translate(w, 0)
        c.rotate(90)
        lw, lh = h, w
        header(lw, lh, 2)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(40, lh - 92, rotated_rows["title"])
        draw_table(c, 40, lh - 108, rotated_rows["widths"], [rotated_rows["columns"]] + rotated_rows["rows"],
                   size=8)
        diagonal_mark(c, lw, lh, "SAMPLE DOCUMENT", alpha=0.08)
        c.restoreState()
        c.showPage()
    c.save()
    buffer.seek(0)
    reader = PdfReader(buffer)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if rotated_rows and i == 1:
            page.rotate(90)
        writer.add_page(page)
    writer.add_metadata({"/Title": f"{title} (SAMPLE)"})
    with open(path, "wb") as handle:
        writer.write(handle)


def text_doc(path, title, subtitle, sections, company):
    w, h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle(f"{title} (SAMPLE)")
    mark = "SAMPLE DOCUMENT  \u2014  FICTIONAL PROJECT  \u00b7  NOT FOR USE"
    page = 1
    total = 2

    def frame():
        c.setFillColor(colors.HexColor("#33475B"))
        c.rect(0, h - 58, w, 58, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, h - 36, company)
        sample_banner(c, w, h, mark, color=colors.HexColor("#B71C1C"))
        c.setFont("Helvetica", 7.2)
        c.setFillColor(GREY)
        c.drawString(40, 32, f"{title}  \u00b7  sample document")
        c.drawRightString(w - 40, 32, f"Page {page} of {total}")
        diagonal_mark(c, w, h, "SAMPLE DOCUMENT", alpha=0.08)

    frame()
    y = h - 96
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(40, y, title)
    c.setFont("Helvetica", 9.5)
    c.setFillColor(GREY)
    c.drawString(40, y - 17, subtitle)
    y -= 46
    for heading, paragraphs in sections:
        if y < 160:
            c.showPage()
            page += 1
            frame()
            y = h - 96
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#33475B"))
        c.drawString(40, y, heading)
        y -= 16
        for text in paragraphs:
            y = draw_paragraph(c, 48, y, text, w - 96, size=9.4, lead=13) - 6
        y -= 6
    while page < total:
        c.showPage()
        page += 1
        frame()
        c.setFont("Helvetica", 9.4)
        c.setFillColor(GREY)
        c.drawString(40, h - 100, "End of sample sequence of operations.")
    c.showPage()
    c.save()


def drawing(path):
    w, h = 1224, 792            # 11 x 17 inches, landscape
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle("M-101 Mechanical record drawing (SAMPLE)")
    c.setStrokeColor(INK)
    c.setLineWidth(2)
    c.rect(24, 24, w - 48, h - 48)
    c.setLineWidth(0.8)
    c.rect(w - 300, 24, 276, 150)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(INK)
    c.drawString(w - 290, 150, "HARBORVIEW FAMILY CLINIC")
    c.setFont("Helvetica", 9)
    c.drawString(w - 290, 134, "Tenant fit-out (fictional project) \u00b7 2026-014")
    c.drawString(w - 290, 118, "MECHANICAL PLAN - HVAC")
    c.setFont("Helvetica-Bold", 26)
    c.drawString(w - 290, 70, "M-101")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(RED)
    c.drawString(w - 290, 44, "RECORD DRAWING (SAMPLE)")
    c.setFillColor(INK)
    rooms = [(80, 420, 220, 260, "WAITING"), (300, 520, 160, 160, "RECEPTION"), (460, 520, 140, 160, "OFFICE"),
             (600, 520, 140, 160, "STORAGE"), (300, 420, 440, 100, "CORRIDOR"), (80, 220, 170, 200, "EXAM 1"),
             (250, 220, 170, 200, "EXAM 2"), (420, 220, 170, 200, "EXAM 3"), (590, 220, 150, 200, "EXAM 4"),
             (740, 220, 160, 460, "STAFF / BREAK")]
    c.setLineWidth(1.6)
    for x, y, rw, rh, name in rooms:
        c.rect(x, y, rw, rh)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + rw / 2, y + rh - 22 if name != "CORRIDOR" else y + rh - 18, name)
    c.setStrokeColor(colors.HexColor("#1565C0"))
    c.setLineWidth(5)
    c.line(150, 470, 860, 470)
    for x in (165, 335, 505, 665):
        c.line(x, 470, x, 330)
    c.setLineWidth(1)
    c.setFillColor(colors.HexColor("#1565C0"))
    for x in (165, 335, 505, 665, 380, 530, 670):
        c.rect(x - 8, 322 if x in (165, 335, 505, 665) else 590, 16, 16, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(170, 480, "SUPPLY DUCT FROM RTU-1")
    for i, x in enumerate((240, 410, 580)):
        c.drawString(x, 345, f"VAV-{i + 1}")
    c.setFillColor(colors.HexColor("#2E7D32"))
    for i, (x, y) in enumerate(((120, 640), (690, 640), (820, 600))):
        c.circle(x, y, 10, stroke=0, fill=1)
        c.drawString(x + 14, y - 3, f"EF-{i + 1}")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8)
    c.drawString(40, 40, "Sample drawing for a portfolio binder. Not to scale. Not for construction.")
    diagonal_mark(c, w, h, "SAMPLE DRAWING \u2014 FICTIONAL PROJECT", size=60, alpha=0.08, angle=25)
    sample_banner(c, w, h, "SAMPLE DRAWING  \u2014  FICTIONAL PROJECT  \u00b7  NOT FOR CONSTRUCTION",
                  color=colors.HexColor("#B71C1C"))
    c.showPage()
    c.save()


EQUIPMENT = {
    "rtu": {"brand": "AEROCREST CLIMATE SYSTEMS", "color": "#16486E", "product": "AeroCrest RTU-480 Series",
            "subtitle": "Packaged rooftop unit, 3 to 10 nominal tons (sample)", "form": "AC-PD-480-A",
            "sketch": "rtu", "manual_no": "Manual AC-IOM-480 Rev B (sample)",
            "intro": "Sample product description. A real datasheet describes the unit, its options and its "
                     "certifications here. Every figure in this document is invented.",
            "features": ["Single-piece packaged design for rooftop curb mounting (sample text).",
                         "Factory-installed economizer option (sample text).",
                         "Service access panels on one side (sample text)."],
            "specs": [["Nominal capacity", "5 tons (sample)"], ["Heating", "Gas, 120 MBH input (sample)"],
                      ["Electrical", "208-230 V / 3 ph / 60 Hz (sample)"], ["Filters", "(4) 20 x 25 x 2 in (sample)"],
                      ["Operating weight", "780 lb (sample)"], ["Refrigerant", "Sample refrigerant"]],
            "specs2": [["Model", "Cooling (sample)", "Heating (sample)", "Electrical (sample)"],
                       ["RTU-480-036", "3.0 tons", "80 MBH", "208-230/3/60"],
                       ["RTU-480-060", "5.0 tons", "120 MBH", "208-230/3/60"],
                       ["RTU-480-090", "7.5 tons", "180 MBH", "460/3/60"],
                       ["RTU-480-120", "10.0 tons", "240 MBH", "460/3/60"]],
            "dims": "Length 92 in (sample)"},
    "fan": {"brand": "VENTORA AIR MOVEMENT", "color": "#2E6B30", "product": "Ventora EF-12 Inline Exhaust Fan",
            "subtitle": "Inline centrifugal exhaust fan (sample)", "form": "VT-EF12-PD",
            "sketch": "fan", "manual_no": "Manual VT-EF12-IOM (sample)",
            "intro": "Sample product description printed on A4 paper, as many European manufacturers do. "
                     "All values are invented.",
            "features": ["Inline mounting in round duct (sample text).", "Speed controller option (sample text)."],
            "specs": [["Airflow", "420 l/s (sample)"], ["Static pressure", "250 Pa (sample)"],
                      ["Motor", "0.37 kW, 230 V / 1 ph (sample)"], ["Duct connection", "315 mm (sample)"]]},
    "vav": {"brand": "TESSEL AIRFLOW PRODUCTS", "color": "#5A3E85", "product": "Tessel VAV-S Single-Duct Terminal",
            "subtitle": "Pressure-independent VAV terminal unit (sample)", "form": "TA-VAVS-PD",
            "sketch": "vav", "manual_no": "Manual TA-VAVS-IOM (sample)",
            "intro": "Sample product description for a single-duct terminal unit. All values are invented.",
            "features": ["Pressure-independent airflow control (sample text).",
                         "Optional hot-water reheat coil (sample text)."],
            "specs": [["Inlet sizes", "6, 8, 10, 12 in (sample)"], ["Airflow range", "100-2000 cfm (sample)"],
                      ["Casing", "22 ga galvanized steel (sample)"], ["Controls", "Factory-mounted actuator (sample)"]],
            "specs2": [["Inlet size", "Min cfm (sample)", "Max cfm (sample)", "Notes"],
                       ["6 in", "100", "500", "Sample"], ["8 in", "180", "900", "Sample"],
                       ["10 in", "280", "1400", "Sample"], ["12 in", "400", "2000", "Sample"]]},
    "tstat": {"brand": "LUMENWISE CONTROLS", "color": "#8A5A00", "product": "Lumenwise T-200 Thermostat",
              "subtitle": "Programmable thermostat for rooftop units (sample)", "form": "LW-T200-PD",
              "sketch": "tstat", "manual_no": "",
              "intro": "Sample product description for a wall thermostat. All values are invented.",
              "features": ["7-day schedule (sample text).", "Occupancy override button (sample text)."],
              "specs": [["Power", "24 VAC (sample)"], ["Stages", "2 heat / 2 cool (sample)"],
                        ["Display", "Backlit (sample)"]]},
}

MANUAL_CHAPTERS = [
    ("Safety", ["Sample text only. A real manual lists the manufacturer's safety instructions here. Follow the "
                "real manufacturer's instructions for real equipment."]),
    ("Installation", ["Sample text only. A real manual explains rigging, mounting and connections here.",
                      "Sample text only. Wiring diagrams normally follow."]),
    ("Start-up and operation", ["Sample text only. A real manual gives the start-up checklist here."]),
    ("Maintenance", ["Sample text only. The table below shows the kind of schedule a real manual gives; the "
                     "intervals are invented.",
                     [["Task (sample)", "Interval", "Notes"], ["Inspect filters", "Sample", "Sample"],
                      ["Check belts and bearings", "Sample", "Sample"], ["Clean coils", "Sample", "Sample"]]]),
]


def build_om_documents(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    rtu, fan, vav, tstat = EQUIPMENT["rtu"], EQUIPMENT["fan"], EQUIPMENT["vav"], EQUIPMENT["tstat"]
    company = "NORTHGATE MECHANICAL SERVICES (FICTIONAL)"
    table_doc(folder / "01-contact-list.pdf", "Project contacts", "Who to call about the HVAC installation (sample)",
              ["Role", "Company (fictional)", "Contact (fictional)", "Phone", "Email"],
              [["Owner", "Harborview Health Partners", "Pat Example", "555-0101", "pat@example.com"],
               ["General contractor", "Quellmoor Builders", "Robin Sample", "555-0102", "robin@example.com"],
               ["Mechanical subcontractor", "Northgate Mechanical Services", "Alex Placeholder", "555-0103",
                "alex@example.com"],
               ["Controls", "Lumenwise Controls (service)", "Jordan Demo", "555-0104", "jordan@example.com"],
               ["Test and balance", "Balanced Air Testing", "Casey Mock", "555-0105", "casey@example.com"],
               ["Rooftop unit supplier", "AeroCrest Climate Systems", "Service desk", "555-0106", "service@example.com"]],
              [100, 130, 110, 60, 132], company,
              notes=["All names, numbers and email addresses are fictional (555-01xx numbers and example.com "
                     "addresses are reserved for examples)."])
    table_doc(folder / "01-warranty-summary.pdf", "Warranty summary", "Equipment warranties for Division 23 (sample)",
              ["Equipment", "Tag", "Manufacturer (fictional)", "Warranty (sample)", "Starts", "Ends"],
              [["Packaged rooftop unit", "RTU-1", "AeroCrest", "1 yr parts; 5 yr heat exchanger", "2026-09-18",
                "2031-09-18"],
               ["Inline exhaust fans", "EF-1 to EF-3", "Ventora", "2 yr parts", "2026-09-18", "2028-09-18"],
               ["VAV terminal units", "VAV-1 to VAV-4", "Tessel", "1 yr parts", "2026-09-18", "2027-09-18"],
               ["Thermostat", "T-1", "Lumenwise", "1 yr parts", "2026-09-18", "2027-09-18"],
               ["Installation workmanship", "All", "Northgate Mechanical", "1 yr", "2026-09-18", "2027-09-18"]],
              [110, 70, 95, 120, 69, 68], company,
              notes=["Sample summary. The warranty documents in this binder state the actual (sample) terms."])
    datasheet(folder / "rtu-480-datasheet.pdf", rtu)
    manual(folder / "rtu-480-iom-manual.pdf", {**rtu, "chapters": MANUAL_CHAPTERS})
    warranty(folder / "rtu-1-warranty.pdf", {
        "brand": rtu["brand"], "color": rtu["color"],
        "fields": [("Project", "Harborview Family Clinic (fictional)"), ("Equipment", "Packaged rooftop unit RTU-1"),
                   ("Model", "RTU-480-060 (sample)"), ("Serial number", "SAMPLE-0000-0001"),
                   ("Warranty start", "September 18, 2026 (substantial completion)")],
        "coverage": ["Parts: 1 year from start (sample term).", "Heat exchanger: 5 years from start (sample term).",
                     "Labor is not included (sample term)."]})
    datasheet(folder / "ef-12-datasheet-A4.pdf", fan, size=A4)
    manual(folder / "ef-12-manual.pdf", {**fan, "chapters": MANUAL_CHAPTERS[:2] + MANUAL_CHAPTERS[3:]}, size=A4)
    warranty(folder / "ef-warranty.pdf", {
        "brand": fan["brand"], "color": fan["color"],
        "fields": [("Project", "Harborview Family Clinic (fictional)"), ("Equipment", "Exhaust fans EF-1 to EF-3"),
                   ("Model", "EF-12 (sample)"), ("Serial numbers", "SAMPLE-EF-0001 to 0003"),
                   ("Warranty start", "September 18, 2026")],
        "coverage": ["Parts: 2 years from start (sample term)."]}, size=A4)
    datasheet(folder / "vav-s-datasheet.pdf", vav)
    manual(folder / "vav-s-manual.pdf", {**vav, "chapters": MANUAL_CHAPTERS[1:]})
    datasheet(folder / "t200-thermostat-datasheet.pdf", tstat)
    text_doc(folder / "sequence-of-operations.pdf", "Sequence of operations - RTU-1 and VAV system",
             "As installed (sample text)", [
                 ("Occupied mode", ["Sample text only. A real sequence describes how the unit runs when the "
                                    "building is occupied."]),
                 ("Unoccupied mode", ["Sample text only."]),
                 ("Economizer", ["Sample text only."]),
                 ("Alarms", ["Sample text only."])], "NORTHGATE MECHANICAL SERVICES (FICTIONAL)")
    table_doc(folder / "pm-schedule.pdf", "Preventive maintenance schedule", "Summary from the manufacturers' "
              "manuals (sample; intervals invented)",
              ["Equipment", "Task", "Frequency (sample)", "Reference"],
              [["RTU-1", "Replace filters", "Sample", "AeroCrest manual, ch. 4"],
               ["RTU-1", "Inspect belts, clean coils", "Sample", "AeroCrest manual, ch. 4"],
               ["EF-1 to EF-3", "Check bearings and wheel", "Sample", "Ventora manual, ch. 3"],
               ["VAV-1 to VAV-4", "Check actuator and airflow", "Sample", "Tessel manual, ch. 3"],
               ["T-1", "Check schedule and battery", "Sample", "Lumenwise datasheet"]],
              [90, 180, 100, 162], company,
              notes=["Sample document. Real maintenance follows the manufacturers' instructions."])
    table_doc(folder / "spare-parts-list.pdf", "Spare parts and attic stock", "Items handed over to the owner (sample)",
              ["Item", "For", "Quantity", "Location (sample)"],
              [["Filter set 20 x 25 x 2", "RTU-1", "2 sets", "Storage room"],
               ["Fan belt (sample part no.)", "RTU-1", "1", "Storage room"],
               ["Thermostat cover key", "T-1", "2", "Office"]],
              [180, 90, 80, 182], company)
    table_doc(folder / "tab-preliminary-readings.pdf", "Preliminary air balance readings",
              "Taken before final balancing (sample values)",
              ["Item", "Design (sample)", "Measured (sample)", "Notes"],
              [["RTU-1 supply", "2000 cfm", "1940 cfm", "Sample"], ["EF-1", "300 cfm", "290 cfm", "Sample"],
               ["EF-2", "150 cfm", "155 cfm", "Sample"], ["EF-3", "150 cfm", "140 cfm", "Sample"]],
              [140, 110, 110, 172], "BALANCED AIR TESTING (FICTIONAL)",
              notes=["Page 2 is a landscape page stored with a rotation, as scanners often save them."],
              rotated_rows={"title": "Diffuser readings (sample values)",
                            "columns": ["Room", "Diffuser", "Design cfm", "Measured cfm", "Percent", "Notes"],
                            "widths": [140, 90, 100, 110, 90, 182],
                            "rows": [[f"Exam {i}", f"S-{i}", "180", str(170 + i * 3), f"{94 + i}%", "Sample"]
                                     for i in range(1, 5)] +
                                    [["Waiting", "S-5", "250", "244", "98%", "Sample"],
                                     ["Reception", "S-6", "150", "151", "101%", "Sample"]]})
    drawing(folder / "m-101-record-drawing.pdf")


def build_spec_checklist(path):
    table_doc(path, "Specification checklist - Section 23 74 00 (DRAFT)",
              "Prepared for the subcontractor's review. The subcontractor confirms compliance.",
              ["Spec para. (sample)", "Requirement (summary, sample)", "Where shown", "PM check"],
              [["2.1.A", "Packaged rooftop unit, gas heat / DX cooling", "Product data p. 1", "[  ] Yes  [  ] No"],
               ["2.1.B", "Nominal cooling capacity 5 tons", "Product data p. 1", "[  ] Yes  [  ] No"],
               ["2.2.A", "208-230 V / 3 ph / 60 Hz power", "Performance data", "[  ] Yes  [  ] No"],
               ["2.3.C", "Factory economizer", "Product data p. 1", "[  ] Yes  [  ] No"],
               ["1.7.A", "Manufacturer's warranty, 5 yr heat exchanger", "Warranty", "[  ] Yes  [  ] No"]],
              [80, 200, 110, 142], "NORTHGATE MECHANICAL SERVICES (FICTIONAL)",
              notes=["This checklist lists where each requirement appears in the package. It does not confirm "
                     "compliance; the subcontractor's project manager checks each line and signs the cover."])


# ===========================================================================
# Sample sets
# ===========================================================================
def run(cmd: list[str]):
    printable = " ".join(str(c) if " " not in str(c) else f'"{c}"' for c in cmd)
    print(f"\n$ {printable}")
    result = subprocess.run([sys.executable] + [str(c) for c in cmd], text=True)
    if result.returncode != 0:
        raise SystemExit(f"Command failed (exit {result.returncode}). See the messages above.")


def toml_text(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def make_sds_sample(base: Path, business: str, build: bool):
    inputs, outputs = base / "input", base / "output"
    sds = inputs / "sds"
    sds.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    for filename, maker, data in fake_sds_set():
        maker(sds / filename, data)
    rows = [{"Product name (as on label)": p, "Manufacturer / brand": m, "Location / area": loc,
             "Container size": size, "Quantity": qty, "In use?": use, "SDS file": f, "Notes": n}
            for p, m, loc, size, qty, use, f, n in SITE_LIST_ROWS]
    make_templates.write_site_list(inputs / "site-list.xlsx", info={
        "client": "Riverside Auto Care (fictional client)", "site": "1200 Example Avenue, Sampletown, ST 00000",
        "walkthrough": "Photos from the client, September 2026 (fictional)", "prepared_by": business,
        "confirmed_by": "", "confirmed_on": ""}, rows=rows)
    (inputs / "cover.toml").write_text(toml_text([
        "# Cover for the sample SDS binder. Copy templates/binder-cover-sds.toml for real jobs.",
        'type = "sds"',
        'title = "Safety Data Sheet Binder"',
        'subtitle = "Chemical inventory and safety data sheets"',
        f'organization = "{business}"',
        'footer_text = "Riverside Auto Care (fictional) - Safety Data Sheet Binder"',
        'accent_color = "#1F3A5F"',
        'watermark = "SAMPLE"',
        "",
        "[details]",
        '"Prepared for" = "Riverside Auto Care (fictional client)"',
        '"Site" = "1200 Example Avenue, Sampletown, ST 00000"',
        '"Binder date" = "today"',
        '"Revision" = "0 (first issue)"',
        f'"Prepared by" = "{business}"',
        '"Chemical list confirmed by" = ""',
        '"Date confirmed" = ""',
    ]), encoding="utf-8")
    if not build:
        return
    run([SCRIPTS / "extract_sds.py", "--sds-folder", sds, "--site-list", inputs / "site-list.xlsx",
         "--out", outputs / "inventory.xlsx", "--group-by", "location",
         "--client", "Riverside Auto Care (fictional client)"])
    binder = outputs / "SAMPLE_SDS-Binder_Riverside-Auto-Care.pdf"
    run([SCRIPTS / "build_binder.py", "--pdf-folder", sds, "--index", outputs / "inventory.xlsx",
         "--sheet", "Binder Index", "--cover", inputs / "cover.toml", "--out", binder])
    run([SCRIPTS / "verify_binder.py", binder, "--pdf-folder", sds, "--quiet"])


def make_om_sample(base: Path, business: str, build: bool):
    inputs, outputs = base / "input", base / "output"
    docs = inputs / "docs"
    build_om_documents(docs)
    outputs.mkdir(parents=True, exist_ok=True)
    index = [
        ("General Information", "Project contacts", "01-contact-list.pdf", "Prepared by the mechanical subcontractor"),
        ("General Information", "Warranty summary", "01-warranty-summary.pdf", ""),
        ("Packaged Rooftop Unit RTU-1 (23 74 00)", "Product data - AeroCrest RTU-480 series", "rtu-480-datasheet.pdf",
         "Unit as installed: RTU-480-060"),
        ("Packaged Rooftop Unit RTU-1 (23 74 00)", "Installation, operation and maintenance manual",
         "rtu-480-iom-manual.pdf", "Manufacturer's manual with its own bookmarks"),
        ("Packaged Rooftop Unit RTU-1 (23 74 00)", "Manufacturer's warranty - RTU-1", "rtu-1-warranty.pdf",
         "Starts at substantial completion"),
        ("Exhaust Fans EF-1 to EF-3 (23 34 23)", "Product data - Ventora EF-12", "ef-12-datasheet-A4.pdf",
         "A4 page from the manufacturer"),
        ("Exhaust Fans EF-1 to EF-3 (23 34 23)", "Installation and maintenance manual", "ef-12-manual.pdf", ""),
        ("Exhaust Fans EF-1 to EF-3 (23 34 23)", "Manufacturer's warranty - EF-1 to EF-3", "ef-warranty.pdf", ""),
        ("VAV Terminal Units (23 36 00)", "Product data - Tessel VAV-S", "vav-s-datasheet.pdf", ""),
        ("VAV Terminal Units (23 36 00)", "Installation and maintenance manual", "vav-s-manual.pdf", ""),
        ("HVAC Controls (23 09 00)", "Product data - Lumenwise T-200 thermostat", "t200-thermostat-datasheet.pdf", ""),
        ("HVAC Controls (23 09 00)", "Sequence of operations", "sequence-of-operations.pdf", "As installed"),
        ("Maintenance", "Preventive maintenance schedule", "pm-schedule.pdf", ""),
        ("Maintenance", "Spare parts and attic stock", "spare-parts-list.pdf", "Handed over to the owner"),
        ("Testing, Adjusting and Balancing (23 05 93)", "Preliminary air balance readings",
         "tab-preliminary-readings.pdf", "Includes a rotated landscape page"),
        ("Testing, Adjusting and Balancing (23 05 93)", "Final test and balance report", "",
         "To be provided by the balancing contractor"),
        ("Record Drawings", "M-101 Mechanical plan (record drawing)", "m-101-record-drawing.pdf", "11 x 17 sheet"),
    ]
    with open(inputs / "index.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "title", "file", "order", "notes"])
        for order, (section, title, file, notes) in enumerate(index, start=1):
            writer.writerow([section, title, file, order, notes])
    (inputs / "cover.toml").write_text(toml_text([
        "# Cover for the sample O&M handover binder. Copy templates/binder-cover-handover.toml for real jobs.",
        'type = "handover"',
        'title = "Operation & Maintenance Manual"',
        'subtitle = "Division 23 - Heating, Ventilating and Air Conditioning"',
        f'organization = "{business}"',
        'footer_text = "Harborview Family Clinic (fictional) - Division 23 HVAC O&M Manual"',
        'accent_color = "#1F3A5F"',
        'watermark = "SAMPLE"',
        "",
        "[details]",
        '"Project" = "Harborview Family Clinic - Tenant Fit-Out (fictional project)"',
        '"Project number" = "2026-014"',
        '"Owner" = "Harborview Health Partners (fictional)"',
        '"General contractor" = "Quellmoor Builders (fictional)"',
        '"Mechanical subcontractor" = "Northgate Mechanical Services (fictional)"',
        '"Substantial completion" = "September 18, 2026"',
        '"Volume" = "1 of 1"',
        f'"Prepared by" = "{business}"',
        '"Date" = "today"',
    ]), encoding="utf-8")
    today = dt.date.today()
    log_rows = [
        ("23 05 93-001", "0", "23 05 93", "Test and balance agency qualifications", "Certificates", "2026-03-02",
         "2026-02-20", "2026-02-27", "Approved", "Subcontractor", "Filed", "", "23 05 93-001_R0_TAB-Qualifications.pdf"),
        ("23 74 00-001", "0", "23 74 00", "Packaged rooftop unit RTU-1 - product data", "Product data", "2026-03-09",
         "2026-03-03", "2026-03-13", "Approved as noted", "Subcontractor", "Order unit with the noted option",
         "Provide factory-mounted disconnect.", "23 74 00-001_R0_RTU-1_Product-Data.pdf"),
        ("23 34 23-001", "0", "23 34 23", "Exhaust fans EF-1 to EF-3 - product data", "Product data", "2026-03-09",
         "2026-03-04", "2026-03-16", "Approved", "Subcontractor", "Filed", "",
         "23 34 23-001_R0_Exhaust-Fans_Product-Data.pdf"),
        ("23 36 00-001", "0", "23 36 00", "VAV terminal units - product data", "Product data", "2026-03-16",
         "2026-03-11", "2026-03-25", "Revise and resubmit", "Subcontractor", "Resubmitted as Rev 1",
         "Reheat coil data missing for VAV-3 and VAV-4.", "23 36 00-001_R0_VAV_Product-Data.pdf"),
        ("23 36 00-001", "1", "23 36 00", "VAV terminal units - product data (resubmittal)", "Product data",
         "2026-04-06", "2026-04-02", "2026-04-10", "Approved", "Subcontractor", "Filed", "",
         "23 36 00-001_R1_VAV_Product-Data.pdf"),
        ("23 09 00-001", "0", "23 09 00", "HVAC controls - product data and sequence of operations", "Product data",
         "2026-04-13", "2026-04-08", "2026-04-24", "Approved as noted", "Subcontractor", "Update sequence as noted",
         "Add night setback to the sequence.", "23 09 00-001_R0_Controls.pdf"),
        ("23 07 00-001", "0", "23 07 00", "HVAC insulation - product data", "Product data", "2026-04-20", "", "",
         "Not submitted", "Subcontractor", "Chase supplier for datasheets", "", ""),
        ("01 78 23-001", "0", "01 78 23", "Operation and maintenance data - Division 23 HVAC", "O&M manual",
         "2026-10-02", "2026-09-29", "", "Submitted - under review", "General contractor", "Await review comments",
         "Final test and balance report to follow.", "SAMPLE_OM-Manual_Harborview-Clinic_Div-23-HVAC.pdf"),
        ("01 78 36-001", "0", "01 78 36", "Warranties - Division 23 HVAC", "Warranty", "2026-10-02", "2026-09-29", "",
         "Submitted - under review", "General contractor", "Await review comments", "", "01 78 36-001_R0_Warranties.pdf"),
        ("23 05 93-002", "0", "23 05 93", "Final test and balance report", "Test reports", "2026-10-23", "", "",
         "Not submitted", "Subcontractor", "Waiting for balancing contractor", "", ""),
        ("01 78 39-001", "0", "01 78 39", "Record drawings - mechanical", "Record drawings", "2026-10-30", "", "",
         "Not submitted", "Subcontractor", "Collect final mark-ups from site", "", ""),
    ]
    names = ["Submittal No.", "Rev", "Spec section", "Description", "Type", "Date required", "Date submitted",
             "Date returned", "Status", "Ball in court", "Next action", "Reviewer comments / notes", "File name"]
    rows = []
    for values in log_rows:
        row = dict(zip(names, values))
        row["Submitted to"] = "Quellmoor Builders (fictional)"
        rows.append(row)
    make_templates.write_submittal_log(outputs / "SAMPLE_Submittal-Log_Harborview-Clinic.xlsx", project={
        "project": "Harborview Family Clinic - Tenant Fit-Out (fictional project)", "project_no": "2026-014",
        "subcontractor": "Northgate Mechanical Services (fictional)",
        "general_contractor": "Quellmoor Builders (fictional)", "prepared_by": business,
        "updated": today}, rows=rows, today=today)
    if not build:
        return
    binder = outputs / "SAMPLE_OM-Manual_Harborview-Clinic_Div-23-HVAC.pdf"
    run([SCRIPTS / "build_binder.py", "--pdf-folder", docs, "--index", inputs / "index.csv",
         "--cover", inputs / "cover.toml", "--out", binder, "--page-numbers",
         "--stamp-prefix", "Harborview Clinic - Div 23 O&M"])
    run([SCRIPTS / "verify_binder.py", binder, "--pdf-folder", docs, "--quiet"])


def make_submittal_sample(base: Path, business: str, build: bool):
    inputs, outputs = base / "input", base / "output"
    docs = inputs / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    rtu = EQUIPMENT["rtu"]
    build_spec_checklist(docs / "spec-checklist-23-74-00.pdf")
    datasheet(docs / "rtu-480-datasheet.pdf", rtu)
    manual(docs / "rtu-480-iom-manual.pdf", {**rtu, "chapters": MANUAL_CHAPTERS})
    warranty(docs / "rtu-1-warranty.pdf", {
        "brand": rtu["brand"], "color": rtu["color"],
        "fields": [("Project", "Harborview Family Clinic (fictional)"), ("Equipment", "Packaged rooftop unit RTU-1"),
                   ("Model", "RTU-480-060 (sample)"), ("Serial number", "To be issued at delivery"),
                   ("Warranty start", "Substantial completion")],
        "coverage": ["Parts: 1 year from start (sample term).", "Heat exchanger: 5 years from start (sample term)."]})
    with open(inputs / "index.csv", "w", encoding="utf-8", newline="") as handle:
        handle.write("section,title,file,order,notes,pages\n")
        handle.write('Submittal documents,Specification checklist (draft for the PM\'s review),'
                     'spec-checklist-23-74-00.pdf,1,Where each requirement appears in this package,\n')
        handle.write("Submittal documents,Product data - AeroCrest RTU-480 series,rtu-480-datasheet.pdf,2,"
                     "Selected model: RTU-480-060,\n")
        handle.write('Submittal documents,Installation and maintenance manual - chapters 1 and 2,'
                     'rtu-480-iom-manual.pdf,3,"Pages 3-4 of the manufacturer\'s manual only",3-4\n')
        handle.write("Submittal documents,Manufacturer's warranty terms,rtu-1-warranty.pdf,4,,\n")
    (inputs / "cover.toml").write_text(toml_text([
        "# Cover for the sample submittal. Copy templates/binder-cover-submittal.toml for real jobs.",
        'type = "submittal"',
        'title = "Submittal 23 74 00-001"',
        'subtitle = "Packaged rooftop unit RTU-1 - product data"',
        f'organization = "{business}"',
        'footer_text = "Harborview Family Clinic (fictional) - Submittal 23 74 00-001 Rev 0"',
        'accent_color = "#1F3A5F"',
        'watermark = "SAMPLE"',
        "",
        "[details]",
        '"Project" = "Harborview Family Clinic - Tenant Fit-Out (fictional project)"',
        '"Project number" = "2026-014"',
        '"Submittal number" = "23 74 00-001, Revision 0"',
        '"Specification section" = "23 74 00 - Packaged Outdoor HVAC Equipment"',
        '"Subcontractor" = "Northgate Mechanical Services (fictional)"',
        '"Submitted to" = "Quellmoor Builders (fictional general contractor)"',
        '"Architect / engineer" = "Ashgrove Partners Architects (fictional)"',
        '"Date" = "today"',
    ]), encoding="utf-8")
    if not build:
        return
    binder = outputs / "SAMPLE_Submittal_23-74-00-001_R0_RTU-1.pdf"
    run([SCRIPTS / "build_binder.py", "--pdf-folder", docs, "--index", inputs / "index.csv",
         "--cover", inputs / "cover.toml", "--out", binder, "--no-dividers", "--tabs", "none", "--page-numbers"])
    run([SCRIPTS / "verify_binder.py", binder, "--pdf-folder", docs, "--quiet"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Make the fake sample inputs and run the kit on them.")
    parser.add_argument("--business", default="Sample Document Services",
                        help="your business name for the covers (default: %(default)s)")
    parser.add_argument("--only", choices=["sds", "om", "submittal"], help="make just one sample set")
    parser.add_argument("--inputs-only", action="store_true", help="only make the inputs; don't run the kit")
    parser.add_argument("--out-dir", default=str(SAMPLES), help="samples folder (default: the kit's samples/)")
    args = parser.parse_args(argv)
    business = args.business.replace('"', "'")
    out = Path(args.out_dir)
    sets = {"sds": ("sds-binder", make_sds_sample), "om": ("om-handover", make_om_sample),
            "submittal": ("submittal-package", make_submittal_sample)}
    for key, (folder, maker) in sets.items():
        if args.only and key != args.only:
            continue
        base = out / folder
        if base.exists():
            shutil.rmtree(base)
        print(f"\n=== Making sample: {folder} ===")
        maker(base, business, not args.inputs_only)
    print("\nDone. Open the PDFs and spreadsheets in samples/ and check them by eye.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
