#!/usr/bin/env python3
"""Build one indexed, bookmarked PDF binder from a folder of PDFs.

You give it:
  * a folder of PDF files (datasheets, manuals, warranties, safety data sheets...)
  * an index file (.csv or .xlsx) that lists what goes in the binder, in order
  * optionally a cover file (.toml) - copy one from templates/

You get:
  * ONE merged PDF: cover page, table of contents with clickable page
    numbers, a divider page for each section, bookmarks for every section
    and document (plus each document's own bookmarks), placeholder pages for
    documents you are still waiting for, and optional "Page X of Y" numbers
    stamped in the bottom margin
  * <binder name>-index.xlsx: where every document starts and ends

Index columns (header names are not case sensitive):
  section  - section or tab the document goes in (e.g. "Rooftop Units")
  title    - name shown in the contents and bookmarks
  file     - PDF file name inside the folder; leave blank for a document you
             are still waiting for (a placeholder page is inserted)
  order    - optional sort number (1, 2, 10 or 1.1, 1.2...)
  notes    - optional short note shown under the title in the contents
  pages    - optional page selection such as 1-3,5 (default: all pages)
  include  - optional; "no" leaves the row out

Example:
  .venv/bin/python scripts/build_binder.py --pdf-folder jobs/acme/docs --index jobs/acme/index.csv \\
      --cover jobs/acme/cover.toml --out jobs/acme/output/Binder.pdf

Manufacturer documents are copied in as they are. The script never edits
their content. --page-numbers adds a small page number in the bottom margin
of every page; leave it off if the client wants untouched pages.
"""
from __future__ import annotations

import argparse
import logging
import datetime as dt
import difflib
import io
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import xlsxwriter
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Link
    from pypdf.generic import RectangleObject
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas as rl_canvas
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing package '{exc.name}'. Run: pip install -r requirements.txt")

import kitlib

logging.getLogger("pypdf").setLevel(logging.ERROR)   # the scripts report problems in plain words
from kitlib import KitError, pdf_safe

FONT = "Helvetica"
BOLD = "Helvetica-Bold"
ITALIC = "Helvetica-Oblique"
DARK = (0.11, 0.13, 0.16)
GREY = (0.40, 0.43, 0.48)
LIGHT = (0.84, 0.86, 0.89)
PENDING = (0.78, 0.36, 0.02)

INDEX_COLUMNS = {
    "section": ["section", "section name", "tab", "tab name", "division", "group", "category", "chapter"],
    "title": ["title", "document", "document title", "document name", "name", "product name", "product"],
    "file": ["file", "filename", "file name", "pdf", "pdf file", "path", "source file", "sds file"],
    "order": ["order", "sort", "sort order", "seq", "sequence", "position", "no.", "no", "#"],
    "notes": ["notes", "note", "comments", "comment", "remarks"],
    "pages": ["pages", "page range", "pages to include", "page selection"],
    "include": ["include", "include?", "in binder", "use"],
}

TYPE_ALIASES = {
    "sds": "sds", "msds": "sds", "safety": "sds", "hazcom": "sds",
    "submittal": "submittal", "submittals": "submittal",
    "handover": "handover", "om": "handover", "o&m": "handover", "closeout": "handover",
    "general": "general", "binder": "general",
}
TYPE_LABELS = {
    "sds": "Safety Data Sheet Binder",
    "submittal": "Submittal Package",
    "handover": "Operation & Maintenance Manual",
    "general": "Document Binder",
}
DEFAULT_NOTICES = {
    "sds": ("This binder collects manufacturers' safety data sheets exactly as supplied. No sheet "
            "has been edited. The chemical list for this site is confirmed by the employer. For "
            "questions about a product's hazards, see its safety data sheet or contact the manufacturer."),
    "submittal": ("Prepared for review. Manufacturer documents are included as published and have not "
                  "been altered. Compliance with the contract documents is reviewed and confirmed by the "
                  "contractor and the design team; the preparer of this package does not certify compliance."),
    "handover": ("Compiled from manufacturer and contractor documents as supplied. Documents have not been "
                 "altered. Warranty terms are those stated in each warranty document."),
    "general": "Documents are included as supplied and have not been altered.",
}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@dataclass
class Doc:
    row: int
    section: str
    title: str
    file: str
    order: str
    notes: str
    pages_spec: str
    path: Path | None = None
    reader: PdfReader | None = None
    page_indices: list[int] = field(default_factory=list)
    pending: bool = False
    pending_reason: str = ""
    sha256: str = ""
    number: str = ""
    start: int = 0
    end: int = 0

    @property
    def page_count(self) -> int:
        return 1 if self.pending else len(self.page_indices)


@dataclass
class Section:
    name: str
    label: str
    docs: list[Doc]
    divider: int = 0

    @property
    def first_page(self) -> int:
        if self.divider:
            return self.divider
        return self.docs[0].start if self.docs else 0


@dataclass
class Settings:
    kind: str = "general"
    title: str = "Document Binder"
    subtitle: str = ""
    organization: str = ""
    doc_label: str = ""
    accent: tuple = (0.12, 0.23, 0.37)
    accent_hex: str = kitlib.DEFAULT_ACCENT
    logo: Path | None = None
    watermark: str = ""
    notice: str = ""
    footer: str = ""
    details: list = field(default_factory=list)
    page_size: tuple = letter
    section_word: str = "Section"
    tabs: str = "numbers"
    dividers: bool = True
    stamp: bool = False
    stamp_prefix: str = ""
    keep_source_bookmarks: bool = True


class Geometry:
    def __init__(self, size):
        self.W, self.H = float(size[0]), float(size[1])
        self.L = 54.0
        self.R = 54.0
        self.T = 54.0
        self.right = self.W - self.R
        self.width = self.W - self.L - self.R
        self.bottom = 68.0       # body text stays above this line; the footer sits below


# ---------------------------------------------------------------------------
# Small drawing helpers
# ---------------------------------------------------------------------------
def wrap(text, font, size, width, max_lines=None):
    words = pdf_safe(text).split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font, size) <= width:
            current = trial
            continue
        if current:
            lines.append(current)
        while stringWidth(word, font, size) > width and len(word) > 1:
            cut = len(word)
            while cut > 1 and stringWidth(word[:cut], font, size) > width:
                cut -= 1
            lines.append(word[:cut])
            word = word[cut:]
        current = word
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and stringWidth(last + "...", font, size) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    return lines or [""]


def fit_text(text, font, size, width):
    return wrap(text, font, size, width, max_lines=1)[0]


def mix(color, other, amount):
    return tuple(a + (b - a) * amount for a, b in zip(color, other))


def draw_leaders_and_number(c, x_from, right, baseline, number, font, size):
    """Dot leaders and a right-aligned page number in ONE text object, so text
    extraction (and copy/paste) reads 'Title . . . . 12' on one line."""
    number = str(number)
    number_x = right - stringWidth(number, font, size)
    dot = ". "
    step = stringWidth(dot, FONT, 9)
    count = max(0, int((number_x - 5 - x_from) / step))
    text = c.beginText(number_x - 5 - count * step, baseline)
    if count >= 2:
        text.setFont(FONT, 9)
        text.setFillColorRGB(*mix(GREY, (1, 1, 1), 0.35))
        text.textOut(dot * count)
    text.setTextOrigin(number_x, baseline)
    text.setFont(font, size)
    text.setFillColorRGB(*DARK)
    text.textOut(number)
    c.drawText(text)


def draw_watermark(c, s: Settings, g: Geometry):
    if not s.watermark:
        return
    text = pdf_safe(s.watermark)
    c.saveState()
    c.setFillColorRGB(0.70, 0.12, 0.12)
    c.setFillAlpha(0.07)
    c.translate(g.W / 2, g.H / 2)
    c.rotate(36)
    size = 120.0
    while size > 24 and stringWidth(text, BOLD, size) > g.H * 0.85:
        size -= 4
    c.setFont(BOLD, size)
    c.drawCentredString(0, -size / 3, text)
    c.restoreState()


def draw_footer(c, s: Settings, g: Geometry, page_no: int, total: int):
    c.setStrokeColorRGB(*LIGHT)
    c.setLineWidth(0.6)
    c.line(g.L, 46, g.right, 46)
    c.setFont(FONT, 8)
    c.setFillColorRGB(*GREY)
    c.drawString(g.L, 32, fit_text(s.footer, FONT, 8, g.width * 0.72))
    c.drawRightString(g.right, 32, f"Page {page_no} of {total}")


def spaced(c, x, y, text, font, size, space=1.2):
    c.setFont(font, size)
    c.drawString(x, y, pdf_safe(text).upper(), charSpace=space)


def render_page(size, draw):
    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=size, pageCompression=1)
    draw(c)
    c.showPage()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


# ---------------------------------------------------------------------------
# Reading the index and the PDFs
# ---------------------------------------------------------------------------
def parse_pages(spec: str, count: int) -> list[int]:
    """'1-3,5' -> [0, 1, 2, 4]. Blank or 'all' -> every page."""
    spec = (spec or "").strip().lower().replace(" ", "")
    if spec in ("", "all", "*"):
        return list(range(count))
    chosen = []
    for part in spec.replace(";", ",").split(","):
        if not part:
            continue
        if "-" in part:
            first, _, last = part.partition("-")
            a = int(first) if first else 1
            b = int(last) if last else count
        else:
            a = b = int(part)
        if a < 1 or b > count or a > b:
            raise ValueError(f"pages '{spec}' is outside 1-{count}")
        chosen.extend(range(a - 1, b))
    if not chosen:
        raise ValueError(f"pages '{spec}' selects nothing")
    return chosen


def describe_pages(indices: list[int], count: int) -> str:
    if indices == list(range(count)):
        return "all"
    parts, start, prev = [], None, None
    for i in indices + [None]:
        if i is not None and prev is not None and i == prev + 1:
            prev = i
            continue
        if start is not None:
            parts.append(f"{start + 1}" if start == prev else f"{start + 1}-{prev + 1}")
        start = prev = i
    return ",".join(parts)


def open_pdf(path: Path) -> PdfReader:
    try:
        reader = PdfReader(str(path), strict=False)
    except Exception as exc:
        raise KitError(f"could not be read as a PDF ({exc.__class__.__name__}: {exc})") from exc
    if reader.is_encrypted:
        try:
            if not reader.decrypt(""):
                raise KitError("is password-protected. Ask the sender for an unlocked copy")
        except KitError:
            raise
        except Exception as exc:
            raise KitError(f"is encrypted and could not be opened ({exc})") from exc
    try:
        if len(reader.pages) == 0:
            raise KitError("has no pages")
    except KitError:
        raise
    except Exception as exc:
        raise KitError(f"is damaged ({exc.__class__.__name__}: {exc})") from exc
    return reader


def list_pdfs(folder: Path) -> dict[str, Path]:
    files = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() == ".pdf":
            files[path.relative_to(folder).as_posix()] = path
    return files


def find_file(folder: Path, name: str, available: dict[str, Path]) -> Path | None:
    name = name.strip().strip('"').replace("\\", "/")
    tries = [name] if name.lower().endswith(".pdf") else [name, name + ".pdf"]
    for candidate in tries:
        path = folder / candidate
        if path.is_file():
            return path
    lower = {key.lower(): path for key, path in available.items()}
    by_base = {}
    for key, path in available.items():
        by_base.setdefault(Path(key).name.lower(), []).append(path)
    for candidate in tries:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
        matches = by_base.get(Path(candidate).name.lower(), [])
        if len(matches) == 1:
            return matches[0]
    return None


def load_docs(args, s: Settings) -> tuple[list[Doc], list[str], list[str]]:
    rows, info = kitlib.read_table(args.index, INDEX_COLUMNS, required=("title", "file"),
                                   sheet=args.sheet, prefer_sheets=("Binder Index", "Index"))
    folder = Path(args.pdf_folder)
    if not folder.is_dir():
        raise KitError(f"PDF folder not found: {folder}")
    available = list_pdfs(folder)
    docs, problems, warnings = [], [], []
    used, included, left_out = set(), set(), 0
    where = f"{Path(args.index).name}" + (f", sheet '{info['sheet']}'" if info.get("sheet") else "")
    for row in rows:
        if row["include"].strip().lower() in ("no", "n", "false", "0", "exclude", "skip", "x"):
            left_out += 1
            excluded = find_file(folder, row["file"], available) if row["file"].strip() else None
            if excluded is not None:
                used.add(excluded.relative_to(folder).as_posix())
            continue
        title = row["title"].strip() or Path(row["file"]).stem
        if not title:
            continue
        doc = Doc(row=row["_row"], section=row["section"].strip() or "Documents", title=title,
                  file=row["file"].strip(), order=row["order"].strip(), notes=row["notes"].strip(),
                  pages_spec=row["pages"].strip())
        label = f"Row {doc.row} ({where}) '{title}'"
        for text in (doc.title, doc.section, doc.notes):
            if pdf_safe(text).count("?") > text.count("?"):
                warnings.append(f"{label}: some characters can't be drawn with the built-in font and show as '?' "
                                "on the cover, contents and dividers (bookmarks keep them).")
                break
        if not doc.file:
            doc.pending = True
            doc.pending_reason = "not yet received"
            docs.append(doc)
            continue
        path = find_file(folder, doc.file, available)
        if path is not None:
            used.add(path.relative_to(folder).as_posix())
        if path is None:
            close = difflib.get_close_matches(doc.file, list(available), n=1, cutoff=0.5)
            hint = f" Did you mean '{close[0]}'?" if close else ""
            message = f"{label}: file '{doc.file}' is not in {folder}.{hint}"
            if args.missing == "error":
                problems.append(message)
            elif args.missing == "placeholder":
                warnings.append(message + " A placeholder page was inserted.")
                doc.pending, doc.pending_reason = True, "file not found"
                docs.append(doc)
            else:
                warnings.append(message + " Left out.")
            continue
        try:
            reader = open_pdf(path)
            doc.page_indices = parse_pages(doc.pages_spec, len(reader.pages))
        except (KitError, ValueError) as exc:
            message = f"{label}: {path.name} {exc}."
            if args.missing == "error":
                problems.append(message)
            elif args.missing == "placeholder":
                warnings.append(message + " A placeholder page was inserted.")
                doc.pending, doc.pending_reason = True, "file could not be read"
                docs.append(doc)
            else:
                warnings.append(message + " Left out.")
            continue
        doc.path, doc.reader = path, reader
        doc.sha256 = kitlib.sha256_file(path)
        rel = path.relative_to(folder).as_posix()
        if rel in included:
            warnings.append(f"{label}: {rel} is listed more than once.")
        included.add(rel)
        docs.append(doc)
    unused = [name for name in available if name not in used and Path(name).name != Path(args.out).name]
    if unused:
        listing = ", ".join(unused[:8]) + (f" and {len(unused) - 8} more" if len(unused) > 8 else "")
        warnings.append(f"{len(unused)} PDF(s) in the folder are not in the index: {listing}")
    if left_out:
        warnings.append(f"{left_out} row(s) marked include = no were left out on purpose.")
    if not docs and not problems:
        problems.append(f"{where} lists no documents.")
    return docs, problems, warnings


def section_label(index: int, style: str) -> str:
    if style == "none":
        return ""
    if style == "letters":
        label, n = "", index + 1
        while n:
            n, rem = divmod(n - 1, 26)
            label = chr(65 + rem) + label
        return label
    return str(index + 1)


def group_sections(docs: list[Doc], s: Settings, warnings: list[str]) -> list[Section]:
    positions = {id(d): i for i, d in enumerate(docs)}
    with_order = [d for d in docs if d.order]
    if with_order:
        without = [d for d in docs if not d.order]
        if without:
            warnings.append(f"{len(without)} row(s) have no order value; they go at the end of their section.")
        ordered = sorted(with_order, key=lambda d: (kitlib.natural_key(d.order), positions[id(d)])) + without
    else:
        ordered = list(docs)
    sections: list[Section] = []
    by_name: dict[str, Section] = {}
    for doc in ordered:
        key = doc.section.strip().lower()
        if key not in by_name:
            by_name[key] = Section(name=doc.section.strip(), label="", docs=[])
            sections.append(by_name[key])
        by_name[key].docs.append(doc)
    for index, section in enumerate(sections):
        section.label = section_label(index, s.tabs)
        for n, doc in enumerate(section.docs, start=1):
            doc.number = f"{section.label}.{n}" if section.label else ""
    return sections


def section_heading(section: Section, s: Settings) -> str:
    if section.label:
        return f"{s.section_word} {section.label} — {section.name}".strip()
    return section.name


# ---------------------------------------------------------------------------
# Table of contents layout
# ---------------------------------------------------------------------------
@dataclass
class TocItem:
    kind: str                 # "section" or "doc"
    text: str
    number: str = ""
    notes: str = ""
    pending: bool = False
    target: object = None     # Section or Doc
    title_lines: list = field(default_factory=list)
    note_lines: list = field(default_factory=list)


SEC_SIZE, SEC_LEAD, SEC_GAP = 11.0, 15.0, 8.0
DOC_SIZE, DOC_LEAD = 9.8, 12.4
NOTE_SIZE, NOTE_LEAD = 7.8, 9.8
NUM_COL = 40.0
PAGE_COL = 52.0           # room kept on the right for leaders and the page number


def toc_columns(g: Geometry, numbered: bool):
    num_x = g.L + 14
    title_x = num_x + (NUM_COL if numbered else 0)
    title_w = g.right - PAGE_COL - title_x
    return num_x, title_x, title_w


def build_toc_items(sections, s: Settings, g: Geometry) -> list[TocItem]:
    numbered = s.tabs != "none"
    _, title_x, title_w = toc_columns(g, numbered)
    items = []
    for section in sections:
        item = TocItem("section", section_heading(section, s), target=section)
        item.title_lines = wrap(item.text, BOLD, SEC_SIZE, g.right - PAGE_COL - g.L, max_lines=2)
        items.append(item)
        for doc in section.docs:
            item = TocItem("doc", doc.title, number=doc.number, notes=doc.notes, pending=doc.pending, target=doc)
            item.title_lines = wrap(doc.title, FONT, DOC_SIZE, title_w, max_lines=3)
            notes = []
            if doc.pending:
                notes.append(("PENDING — " + doc.pending_reason).upper())
            if doc.notes:
                notes.extend(wrap(doc.notes, FONT, NOTE_SIZE, title_w, max_lines=2))
            item.note_lines = notes
            items.append(item)
    return items


def item_height(item: TocItem) -> float:
    if item.kind == "section":
        return len(item.title_lines) * SEC_LEAD + 5
    return len(item.title_lines) * DOC_LEAD + len(item.note_lines) * NOTE_LEAD + 2.5


def layout_toc(items: list[TocItem], g: Geometry):
    """Split the contents into pages. Returns a list of pages: [(item, top_y), ...]."""
    first_top = g.H - g.T - 80
    next_top = g.H - g.T - 44
    pages, y = [[]], first_top
    for index, item in enumerate(items):
        gap = SEC_GAP if (item.kind == "section" and pages[-1]) else 0
        need = gap + item_height(item)
        if item.kind == "section" and index + 1 < len(items) and items[index + 1].kind == "doc":
            need += item_height(items[index + 1])          # keep a heading with its first entry
        if y - need < g.bottom and pages[-1]:
            pages.append([])
            y, gap = next_top, 0
        y -= gap
        pages[-1].append((item, y))
        y -= item_height(item)
    return pages


def item_target_page(item: TocItem) -> int:
    return item.target.first_page if item.kind == "section" else item.target.start


def draw_toc_page(c, s, g, page_items, page_no, total, first, links):
    numbered = s.tabs != "none"
    num_x, title_x, _ = toc_columns(g, numbered)
    draw_watermark(c, s, g)
    if first:
        c.setFillColorRGB(*s.accent)
        c.setFont(BOLD, 24)
        c.drawString(g.L, g.H - g.T - 26, "Contents")
        c.setFont(FONT, 10.5)
        c.setFillColorRGB(*GREY)
        c.drawString(g.L, g.H - g.T - 45, fit_text(s.footer, FONT, 10.5, g.width))
        c.setFillColorRGB(*s.accent)
        c.rect(g.L, g.H - g.T - 60, 48, 2.5, stroke=0, fill=1)
        c.setFont(FONT, 7.5)
        c.setFillColorRGB(*GREY)
        c.drawRightString(g.right, g.H - g.T - 72, "PAGE")
    else:
        c.setFillColorRGB(*s.accent)
        c.setFont(BOLD, 13)
        c.drawString(g.L, g.H - g.T - 16, "Contents (continued)")
        c.setFont(FONT, 7.5)
        c.setFillColorRGB(*GREY)
        c.drawRightString(g.right, g.H - g.T - 30, "PAGE")
    for item, top in page_items:
        target = item_target_page(item)
        if item.kind == "section":
            base = top - SEC_SIZE
            c.setFillColorRGB(*DARK)
            c.setFont(BOLD, SEC_SIZE)
            for i, line in enumerate(item.title_lines):
                c.drawString(g.L, base - i * SEC_LEAD, line)
            last = base - (len(item.title_lines) - 1) * SEC_LEAD
            end_x = g.L + stringWidth(item.title_lines[-1], BOLD, SEC_SIZE)
            draw_leaders_and_number(c, end_x + 6, g.right, last, target, BOLD, SEC_SIZE)
            c.setStrokeColorRGB(*LIGHT)
            c.setLineWidth(0.5)
            c.line(g.L, last - 5, g.right, last - 5)
            bottom = last - 6
        else:
            base = top - DOC_SIZE - 1
            c.setFillColorRGB(*GREY)
            c.setFont(FONT, DOC_SIZE)
            if numbered and item.number:
                c.drawString(num_x, base, item.number)
            c.setFillColorRGB(*DARK)
            for i, line in enumerate(item.title_lines):
                c.drawString(title_x, base - i * DOC_LEAD, line)
            last = base - (len(item.title_lines) - 1) * DOC_LEAD
            end_x = title_x + stringWidth(item.title_lines[-1], FONT, DOC_SIZE)
            draw_leaders_and_number(c, end_x + 6, g.right, last, target, FONT, DOC_SIZE)
            y = last - NOTE_LEAD
            for line in item.note_lines:
                if line.startswith("PENDING"):
                    c.setFont(BOLD, NOTE_SIZE - 0.6)
                    c.setFillColorRGB(*PENDING)
                else:
                    c.setFont(FONT, NOTE_SIZE)
                    c.setFillColorRGB(*GREY)
                c.drawString(title_x, y, line)
                y -= NOTE_LEAD
            bottom = y + NOTE_LEAD - 3
        links.append(((g.L - 2, bottom, g.right + 2, top + 2), target - 1))
    draw_footer(c, s, g, page_no, total)


# ---------------------------------------------------------------------------
# Cover, dividers and placeholder pages
# ---------------------------------------------------------------------------
def cover_stats(s: Settings, sections, total):
    docs = [d for sec in sections for d in sec.docs]
    pending = sum(1 for d in docs if d.pending)
    included = len(docs) - pending
    noun = "Safety data sheets" if s.kind == "sds" else "Documents"
    stats = [(str(included), noun), (str(pending), "Pending"), (str(len(sections)), "Sections"),
             (str(total), "Pages")]
    return stats


def draw_cover(c, s: Settings, g: Geometry, sections, total, warnings):
    W, H, L, right = g.W, g.H, g.L, g.right
    label_w = 152.0
    rows = [(str(k), str(v)) for k, v in s.details]

    # Plan the page from the bottom up: notice box, then the stamp boxes
    # (submittals) or the "at a glance" figures, then whatever room is left
    # goes to the details. If they don't fit, make the header band shorter,
    # then the details smaller, then drop the figures, and only then rows.
    notice_lines = wrap(s.notice, FONT, 8.2, g.width - 28) if s.notice else []
    notice_h = (len(notice_lines) * 11 + 22) if notice_lines else 0
    notice_y = 50.0
    block_top = notice_y + notice_h + (14 if notice_h else 0)
    box_h = 92.0
    block_h = box_h + 22 if s.kind == "submittal" else 58.0
    title_lines = wrap(s.title, BOLD, 28, g.width, max_lines=3)
    subtitle_lines = wrap(s.subtitle, FONT, 14, g.width, max_lines=2) if s.subtitle else []

    def details_height(size, lead):
        height = 0.0
        for _, value in rows:
            n = len(wrap(value, FONT, size, g.width - label_w, max_lines=3)) if value.strip() else 1
            height += n * lead + 12
        return height

    def room(band, stats_shown):
        top = H - band - 66 - len(title_lines) * 33 - (len(subtitle_lines) * 18 + 1 if subtitle_lines else 0) - 34
        bottom = block_top + (block_h + 18 if (s.kind == "submittal" or stats_shown) else 12)
        return top - bottom

    plan = None
    for band, size, lead in ((212.0, 11.0, 14.0), (150.0, 11.0, 14.0), (150.0, 9.5, 12.0)):
        if details_height(size, lead) <= room(band, True):
            plan = (band, size, lead, True)
            break
    if plan is None and s.kind != "submittal" and details_height(9.5, 12.0) <= room(150.0, False):
        plan = (150.0, 9.5, 12.0, False)
    if plan is None:
        plan = (150.0, 9.5, 12.0, s.kind == "submittal")
        while rows and details_height(9.5, 12.0) > room(150.0, plan[3]):
            dropped = rows.pop()
            warnings.append(f"Cover: not enough room for the detail '{dropped[0]}'. Shorten the details.")
    band, size, lead, show_stats = plan
    show_stats = show_stats and sections is not None      # no figures on a cover-only proof

    c.setFillColorRGB(*s.accent)
    c.rect(0, H - band, W, band, stroke=0, fill=1)
    c.setFillColorRGB(*mix(s.accent, (1, 1, 1), 0.35))
    c.rect(0, H - band - 5, W, 5, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    if s.organization:
        spaced(c, L, H - 58, fit_text(s.organization.upper(), BOLD, 11, g.width - 150), BOLD, 11, 1.4)
    c.setFillColorRGB(*mix(s.accent, (1, 1, 1), 0.78))
    spaced(c, L, H - band + 28, s.doc_label or TYPE_LABELS[s.kind], FONT, 10, 2.0)
    if s.logo:
        try:
            c.drawImage(ImageReader(str(s.logo)), right - 140, H - 104, width=140, height=60,
                        preserveAspectRatio=True, anchor="ne", mask="auto")
        except Exception as exc:
            warnings.append(f"Logo '{s.logo}' could not be drawn ({exc}).")

    y = H - band - 66
    c.setFillColorRGB(*DARK)
    c.setFont(BOLD, 28)
    for line in title_lines:
        c.drawString(L, y, line)
        y -= 33
    if subtitle_lines:
        c.setFont(FONT, 14)
        c.setFillColorRGB(*GREY)
        y -= 1
        for line in subtitle_lines:
            c.drawString(L, y, line)
            y -= 18
    y -= 6
    c.setFillColorRGB(*s.accent)
    c.rect(L, y, 56, 3, stroke=0, fill=1)
    y -= 28

    for label, value in rows:
        c.setFont(BOLD, 7.4)
        c.setFillColorRGB(*GREY)
        c.drawString(L, y + 1, fit_text(label.upper(), BOLD, 7.4, label_w - 10), charSpace=0.6)
        if value.strip():
            lines = wrap(value, FONT, size, g.width - label_w, max_lines=3)
            c.setFont(FONT, size)
            c.setFillColorRGB(*DARK)
            for i, line in enumerate(lines):
                c.drawString(L + label_w, y - i * lead, line)
            used = len(lines) * lead
        else:
            c.setStrokeColorRGB(*GREY)
            c.setLineWidth(0.6)
            c.line(L + label_w, y - 3, right, y - 3)
            used = lead
        y -= used + 12
        if value.strip():
            c.setStrokeColorRGB(*LIGHT)
            c.setLineWidth(0.5)
            c.line(L, y + 8, right, y + 8)

    if s.kind == "submittal":
        top = block_top + block_h
        c.setFont(BOLD, 7.4)
        c.setFillColorRGB(*GREY)
        c.drawString(L, top - 8, "FOR REVIEWER USE", charSpace=0.6)
        box_w = (g.width - 14) / 2
        for i, label in enumerate(("Contractor's review stamp", "Architect / engineer review stamp")):
            x = L + i * (box_w + 14)
            c.setStrokeColorRGB(*mix(GREY, (1, 1, 1), 0.3))
            c.setLineWidth(0.8)
            c.setDash(3, 2)
            c.rect(x, block_top, box_w, box_h, stroke=1, fill=0)
            c.setDash()
            c.setFont(FONT, 8)
            c.setFillColorRGB(*GREY)
            c.drawString(x + 8, block_top + box_h - 14, label)
    elif show_stats:
        stats = cover_stats(s, sections, total)
        cell = g.width / len(stats)
        c.setFillColorRGB(*mix(s.accent, (1, 1, 1), 0.92))
        c.rect(L, block_top, g.width, block_h, stroke=0, fill=1)
        for i, (value, label) in enumerate(stats):
            x = L + i * cell + 16
            c.setFillColorRGB(*(PENDING if label == "Pending" and value != "0" else s.accent))
            c.setFont(BOLD, 20)
            c.drawString(x, block_top + 26, value)
            c.setFillColorRGB(*GREY)
            c.setFont(FONT, 7.6)
            c.drawString(x, block_top + 12, label.upper(), charSpace=0.5)

    if notice_lines:
        c.setFillColorRGB(0.955, 0.96, 0.97)
        c.rect(L, notice_y, g.width, notice_h, stroke=0, fill=1)
        c.setFillColorRGB(*s.accent)
        c.rect(L, notice_y, 3, notice_h, stroke=0, fill=1)
        c.setFont(FONT, 8.2)
        c.setFillColorRGB(*mix(DARK, (1, 1, 1), 0.15))
        ty = notice_y + notice_h - 16
        for line in notice_lines:
            c.drawString(L + 16, ty, line)
            ty -= 11
    draw_watermark(c, s, g)


def draw_divider(c, s: Settings, g: Geometry, section: Section, index: int, total: int, links):
    draw_watermark(c, s, g)
    W, H, L, right = g.W, g.H, g.L, g.right
    # Side tab, stepped down the page like a real binder tab.
    tab_h, tab_w = 66.0, 30.0
    tab_top = H - 86 - (index % 8) * (tab_h + 8)
    c.setFillColorRGB(*s.accent)
    c.rect(W - tab_w, tab_top - tab_h, tab_w, tab_h, stroke=0, fill=1)
    if section.label:
        c.saveState()
        c.setFillColorRGB(1, 1, 1)
        c.translate(W - tab_w / 2 + 4, tab_top - tab_h / 2)
        c.rotate(90)
        c.setFont(BOLD, 13)
        c.drawCentredString(0, 0, section.label)
        c.restoreState()

    y = H - 150
    c.setFillColorRGB(*s.accent)
    if section.label:
        spaced(c, L, y, s.section_word, BOLD, 11, 2.2)
        c.setFont(BOLD, 64)
        c.drawString(L - 3, y - 70, section.label)
        y -= 118
    name_lines = wrap(section.name, BOLD, 26, g.width - 40, max_lines=3)
    c.setFillColorRGB(*DARK)
    c.setFont(BOLD, 26)
    for line in name_lines:
        c.drawString(L, y, line)
        y -= 31
    y -= 4
    c.setFillColorRGB(*s.accent)
    c.rect(L, y, 56, 3, stroke=0, fill=1)
    y -= 34
    c.setFillColorRGB(*GREY)
    c.setFont(BOLD, 7.6)
    c.drawString(L, y, "IN THIS SECTION", charSpace=0.8)
    c.drawRightString(right - 34, y, "PAGE")
    y -= 20
    entry_right = right - 34
    for n, doc in enumerate(section.docs):
        lines = wrap(doc.title, FONT, 10.5, entry_right - (L + 36) - PAGE_COL, max_lines=2)
        needed = len(lines) * 13 + (11 if (doc.notes or doc.pending) else 0) + 8
        remaining = len(section.docs) - n
        if y - needed < g.bottom + 22 and remaining > 0:
            c.setFont(ITALIC, 9)
            c.setFillColorRGB(*GREY)
            c.drawString(L, y - 4, f"+ {remaining} more — see Contents on page 2.")
            break
        top = y + 10
        c.setFont(FONT, 9.5)
        c.setFillColorRGB(*GREY)
        c.drawString(L, y, doc.number)
        c.setFont(FONT, 10.5)
        c.setFillColorRGB(*DARK)
        for i, line in enumerate(lines):
            c.drawString(L + 36, y - i * 13, line)
        last = y - (len(lines) - 1) * 13
        draw_leaders_and_number(c, L + 36 + stringWidth(lines[-1], FONT, 10.5) + 6, entry_right, last,
                                doc.start, FONT, 10.5)
        y = last - 13
        if doc.pending or doc.notes:
            if doc.pending:
                c.setFont(BOLD, 7.4)
                c.setFillColorRGB(*PENDING)
                text = "PENDING — " + doc.pending_reason.upper()
                if doc.notes:
                    text += "  "
                c.drawString(L + 36, y + 2, text)
                offset = stringWidth(text, BOLD, 7.4)
            else:
                offset = 0
            if doc.notes:
                c.setFont(FONT, 7.8)
                c.setFillColorRGB(*GREY)
                c.drawString(L + 36 + offset, y + 2,
                             fit_text(doc.notes, FONT, 7.8, entry_right - (L + 36) - offset - 40))
            y -= 11
        links.append(((L - 2, y + 6, entry_right + 2, top), doc.start - 1))
        y -= 8
    draw_footer(c, s, g, section.divider, total)


def draw_placeholder(c, s: Settings, g: Geometry, section: Section, doc: Doc, total: int):
    draw_watermark(c, s, g)
    L, H = g.L, g.H
    y = H - 120
    c.setFillColorRGB(*PENDING)
    c.roundRect(L, y - 6, 128, 22, 4, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(BOLD, 9)
    c.drawString(L + 12, y + 1, "PENDING DOCUMENT", charSpace=0.6)
    y -= 54
    c.setFillColorRGB(*DARK)
    c.setFont(BOLD, 22)
    for line in wrap(doc.title, BOLD, 22, g.width, max_lines=3):
        c.drawString(L, y, line)
        y -= 27
    c.setFont(FONT, 11)
    c.setFillColorRGB(*GREY)
    where = f"{doc.number}  ·  {section_heading(section, s)}" if doc.number else section.name
    c.drawString(L, y - 2, fit_text(where, FONT, 11, g.width))
    y -= 40
    if s.kind == "sds":
        message = ("The safety data sheet for this product has not been received yet. It has been "
                   "requested from the manufacturer or supplier. Replace this page with the sheet "
                   "when it arrives.")
    else:
        message = ("This document has not been received yet. Replace this page with the document "
                   "when it arrives.")
    if doc.pending_reason and doc.pending_reason != "not yet received":
        message = f"This document could not be included ({doc.pending_reason}). " + message
    lines = wrap(message, FONT, 11, g.width - 40)
    note_lines = wrap("Note: " + doc.notes, ITALIC, 10, g.width - 40, max_lines=4) if doc.notes else []
    box_h = len(lines) * 15 + len(note_lines) * 13 + 74
    c.setStrokeColorRGB(*mix(PENDING, (1, 1, 1), 0.35))
    c.setLineWidth(1)
    c.setDash(4, 3)
    c.rect(L, y - box_h, g.width, box_h, stroke=1, fill=0)
    c.setDash()
    ty = y - 28
    c.setFillColorRGB(*DARK)
    c.setFont(FONT, 11)
    for line in lines:
        c.drawString(L + 20, ty, line)
        ty -= 15
    if note_lines:
        ty -= 4
        c.setFont(ITALIC, 10)
        c.setFillColorRGB(*GREY)
        for line in note_lines:
            c.drawString(L + 20, ty, line)
            ty -= 13
    ty -= 18
    c.setFont(FONT, 9)
    c.setFillColorRGB(*GREY)
    c.drawString(L + 20, ty, "Requested on: ____________________        Received on: ____________________")
    draw_footer(c, s, g, doc.start, total)


# ---------------------------------------------------------------------------
# Page-number stamp for source pages (optional)
# ---------------------------------------------------------------------------
def stamp_page(page, text: str, position: str = "bottom-right"):
    """Write a small page number in the margin of the page, the right way up
    for the reader even on rotated pages. A thin white outline keeps it
    readable on dark or busy backgrounds without covering the page."""
    box = page.cropbox
    x0, y0 = float(box.left), float(box.bottom)
    w, h = float(box.width), float(box.height)
    rotation = (page.rotation or 0) % 360
    visible_w, visible_h = (h, w) if rotation in (90, 270) else (w, h)
    text = pdf_safe(text)
    width = stringWidth(text, FONT, 7.5)
    vertical = visible_h - 18 if position.startswith("top") else 13.0
    if position.endswith("left"):
        u = 24.0 + width
    elif position.endswith("center"):
        u = (visible_w + width) / 2
    else:
        u = visible_w - 24
    v = vertical                          # (u, v): right end of the text as the reader sees the page
    if rotation == 90:
        x, y = x0 + w - v, y0 + u
    elif rotation == 180:
        x, y = x0 + w - u, y0 + h - v
    elif rotation == 270:
        x, y = x0 + v, y0 + h - u
    else:
        x, y = x0 + u, y0 + v
    media = page.mediabox
    size = (max(float(media.right), 1.0) + abs(min(float(media.left), 0.0)),
            max(float(media.top), 1.0) + abs(min(float(media.bottom), 0.0)))

    def draw(c):
        c.saveState()
        c.translate(x, y)
        c.rotate(rotation)
        c.saveState()                         # the outline's render mode must not leak into the fill
        outline = c.beginText(-width, 0)
        outline.setTextRenderMode(1)          # stroke only: a white halo
        outline.setFont(FONT, 7.5)
        c.setStrokeColorRGB(1, 1, 1)
        c.setLineWidth(1.8)
        c.setLineJoin(1)
        outline.textOut(text)
        c.drawText(outline)
        c.restoreState()
        fill = c.beginText(-width, 0)
        fill.setFont(FONT, 7.5)
        fill.setFillColorRGB(0.2, 0.2, 0.2)
        fill.textOut(text)
        c.drawText(fill)
        c.restoreState()

    overlay = render_page(size, draw)
    rect = RectangleObject([float(media.left), float(media.bottom), float(media.right), float(media.top)])
    overlay.mediabox = rect
    overlay.cropbox = rect
    overlay.trimbox = rect
    page.merge_page(overlay)


# ---------------------------------------------------------------------------
# Outline (bookmarks)
# ---------------------------------------------------------------------------
def import_outline(writer, doc: Doc, parent, limit=400) -> int:
    try:
        outline = doc.reader.outline
    except Exception:
        return 0
    if not outline:
        return 0
    mapping = {src: doc.start - 1 + pos for pos, src in enumerate(doc.page_indices)}
    added = 0

    def walk(items, parent_item):
        nonlocal added
        last = parent_item
        for item in items:
            if added >= limit:
                return
            if isinstance(item, list):
                walk(item, last)
                continue
            title = str(getattr(item, "title", "") or "").strip()
            try:
                src_page = doc.reader.get_destination_page_number(item)
            except Exception:
                src_page = None
            if not title or src_page not in mapping:
                last = parent_item
                continue
            last = writer.add_outline_item(title[:200], mapping[src_page], parent=parent_item, is_open=False)
            added += 1

    try:
        walk(outline, parent)
    except Exception:
        pass
    return added


def count_outline(items) -> int:
    total = 0
    for item in items:
        total += count_outline(item) if isinstance(item, list) else 1
    return total


# ---------------------------------------------------------------------------
# Index spreadsheet
# ---------------------------------------------------------------------------
def write_index_xlsx(path: Path, s: Settings, sections, toc_pages, total, out_pdf: Path, args, warnings):
    workbook = xlsxwriter.Workbook(str(path), kitlib.XLSX_OPTIONS)
    f = kitlib.xlsx_formats(workbook, s.accent_hex)
    sheet = workbook.add_worksheet("Index")
    headers = ["Type", "Section No.", "Section", "Doc No.", "Title", "Notes", "Status", "Source file",
               "Pages used", "Page count", "Start page", "End page", "Source SHA-256"]
    widths = [12, 9, 30, 8, 46, 34, 22, 34, 10, 9, 9, 9, 66]
    for col, (head, width) in enumerate(zip(headers, widths)):
        sheet.write(0, col, head, f["header"])
        sheet.set_column(col, col, width)
    sheet.set_row(0, 30)
    row = 1

    def put(values, bold=False):
        nonlocal row
        for col, value in enumerate(values):
            numeric = col in (9, 10, 11) and isinstance(value, int)
            if bold:
                fmt = f["section_int"] if numeric else f["section_row"]
            else:
                fmt = f["int"] if numeric else f["text"]
            sheet.write(row, col, value, fmt)
        row += 1

    put(["Front matter", "", "", "", "Cover", "", "Generated page", "", "", 1, 1, 1, ""])
    if toc_pages:
        put(["Front matter", "", "", "", "Contents", "", "Generated page", "", "", toc_pages, 2,
             1 + toc_pages, ""])
    for section in sections:
        if s.dividers:
            put(["Section", section.label, section.name, "", section_heading(section, s), "",
                 "Divider page", "", "", 1, section.divider, section.divider, ""], bold=True)
        else:
            put(["Section", section.label, section.name, "", section_heading(section, s), "",
                 "No divider", "", "", 0, section.first_page, "", ""], bold=True)
        for doc in section.docs:
            if doc.pending:
                put(["Pending", section.label, section.name, doc.number, doc.title, doc.notes,
                     f"PENDING - {doc.pending_reason}", doc.file, "", 1, doc.start, doc.end, ""])
            else:
                rel = doc.path.relative_to(Path(args.pdf_folder)).as_posix()
                put(["Document", section.label, section.name, doc.number, doc.title, doc.notes,
                     "Included", rel, describe_pages(doc.page_indices, len(doc.reader.pages)),
                     doc.page_count, doc.start, doc.end, doc.sha256])
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, row - 1, len(headers) - 1)
    sheet.conditional_format(1, 6, max(row - 1, 1), 6, {"type": "text", "criteria": "begins with",
                                                          "value": "PENDING", "format": f["st_check"]})

    summary = workbook.add_worksheet("Summary")
    summary.hide_gridlines(2)
    summary.set_column(0, 0, 26)
    summary.set_column(1, 1, 90)
    summary.write(0, 0, "Binder summary", f["title"])
    docs = [d for sec in sections for d in sec.docs]
    pending = [d for d in docs if d.pending]
    facts = [
        ("Binder file", out_pdf.name),
        ("Title", s.title),
        ("Binder type", TYPE_LABELS[s.kind]),
        ("Built on", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Total pages", total),
        ("Sections", len(sections)),
        ("Documents included", len(docs) - len(pending)),
        ("Pending (placeholder pages)", len(pending)),
        ("Contents pages", toc_pages),
        ("Divider pages", len(sections) if s.dividers else 0),
        ("Page numbers stamped", "Yes" if s.stamp else "No"),
        ("Source folder", str(args.pdf_folder)),
        ("Index file used", str(args.index) + (f" (sheet {args.sheet})" if args.sheet else "")),
        ("Cover file used", str(args.cover or "")),
    ]
    r = 2
    for label, value in facts:
        summary.write(r, 0, label, f["label"])
        summary.write(r, 1, value, f["wrap"])
        r += 1
    r += 1
    summary.write(r, 0, "Warnings", f["label"])
    if warnings:
        for warning in warnings:
            summary.write(r, 1, warning, f["wrap"])
            summary.set_row(r, 15 * (len(warning) // 95 + 1))
            r += 1
    else:
        summary.write(r, 1, "None", f["wrap"])
    workbook.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def settings_from(args) -> Settings:
    cover = kitlib.load_cover(args.cover) if args.cover else {}
    s = Settings()
    kind = str(args.type or cover.get("type") or "general").strip().lower()
    if kind not in TYPE_ALIASES:
        raise KitError(f"Unknown binder type '{kind}'. Use sds, submittal, handover or general.")
    s.kind = TYPE_ALIASES[kind]
    s.title = str(args.title or cover.get("title") or TYPE_LABELS[s.kind])
    s.subtitle = str(args.subtitle if args.subtitle is not None else cover.get("subtitle", ""))
    s.organization = str(cover.get("organization", ""))
    s.doc_label = str(cover.get("doc_label", "") or TYPE_LABELS[s.kind])
    s.accent_hex = str(cover.get("accent_color", kitlib.DEFAULT_ACCENT))
    s.accent = kitlib.hex_to_rgb(s.accent_hex)
    logo = str(cover.get("logo", "") or "").strip()
    if logo:
        logo_path = Path(logo)
        if not logo_path.is_absolute():
            logo_path = Path(cover.get("_folder", ".")) / logo_path
        s.logo = logo_path if logo_path.is_file() else None
        if s.logo is None:
            print(f"Warning: logo file not found: {logo_path}", file=sys.stderr)
    s.watermark = str(args.watermark if args.watermark is not None else cover.get("watermark", ""))
    s.notice = str(cover.get("notice", DEFAULT_NOTICES[s.kind]))
    details = cover.get("details", {}) or {}
    if isinstance(details, dict):
        s.details = [(k, kitlib.resolve_today(str(v))) for k, v in details.items()]
    elif isinstance(details, list):
        s.details = [(str(d.get("label", "")), kitlib.resolve_today(str(d.get("value", ""))))
                     for d in details if isinstance(d, dict)]
    s.footer = str(cover.get("footer_text", "") or s.title)
    size_name = str(args.page_size or cover.get("page_size", "letter")).lower()
    if size_name not in ("letter", "a4"):
        raise KitError("page size must be letter or a4")
    s.page_size = letter if size_name == "letter" else A4
    s.section_word = args.section_word
    s.tabs = args.tabs
    s.dividers = not args.no_dividers
    s.stamp = args.page_numbers
    s.stamp_prefix = args.stamp_prefix or ""
    s.keep_source_bookmarks = not args.no_source_bookmarks
    return s


def build(args) -> int:
    s = settings_from(args)
    g = Geometry(s.page_size)
    out = Path(args.out)
    if out.suffix.lower() != ".pdf":
        raise KitError("--out must end in .pdf")
    index_out = Path(args.index_out) if args.index_out else out.with_name(out.stem + "-index.xlsx")
    if index_out.resolve() == Path(args.index).resolve():
        raise KitError("--index-out would overwrite your input index. Choose another name.")
    warnings: list[str] = []

    if args.cover_only:
        out.parent.mkdir(parents=True, exist_ok=True)
        page = render_page(s.page_size, lambda c: draw_cover(c, s, g, None, 1, warnings))
        writer = PdfWriter()
        writer.add_page(page)
        with open(out, "wb") as handle:
            writer.write(handle)
        print(f"Cover preview written: {out}")
        for w in warnings:
            print(f"  Warning: {w}")
        return 0

    docs, problems, load_warnings = load_docs(args, s)
    warnings.extend(load_warnings)
    if problems:
        print("The binder was NOT built. Fix these and run again:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("Tip: use --missing placeholder to insert placeholder pages instead.", file=sys.stderr)
        return 1

    sections = group_sections(docs, s, warnings)

    # Pass 1: how many contents pages? Then give every page its final number.
    items = build_toc_items(sections, s, g)
    toc_layout = layout_toc(items, g) if not args.no_toc else []
    toc_pages = len(toc_layout)
    page = 1 + toc_pages + 1
    for section in sections:
        if s.dividers:
            section.divider = page
            page += 1
        for doc in section.docs:
            doc.start = page
            doc.end = page + doc.page_count - 1
            page = doc.end + 1
    total = page - 1

    # Pass 2: draw the generated pages and assemble the binder.
    writer = PdfWriter()
    links: list[tuple[int, tuple, int]] = []
    writer.add_page(render_page(s.page_size, lambda c: draw_cover(c, s, g, sections, total, warnings)))
    for i, page_items in enumerate(toc_layout):
        page_links: list = []
        writer.add_page(render_page(s.page_size, lambda c: draw_toc_page(
            c, s, g, page_items, 2 + i, total, i == 0, page_links)))
        links.extend((1 + i, rect, target) for rect, target in page_links)
    if len(writer.pages) != 1 + toc_pages:
        raise KitError("Internal error: contents page count changed between passes.")

    for index, section in enumerate(sections):
        if s.dividers:
            page_links = []
            writer.add_page(render_page(s.page_size, lambda c: draw_divider(
                c, s, g, section, index, total, page_links)))
            links.extend((section.divider - 1, rect, target) for rect, target in page_links)
        for doc in section.docs:
            before = len(writer.pages)
            if doc.pending:
                writer.add_page(render_page(s.page_size, lambda c: draw_placeholder(c, s, g, section, doc, total)))
            else:
                writer.append(doc.reader, pages=doc.page_indices, import_outline=False)
            added = len(writer.pages) - before
            if before + 1 != doc.start or added != doc.page_count:
                raise KitError(f"Internal error: page numbers for '{doc.title}' did not line up.")

    if len(writer.pages) != total:
        raise KitError(f"Internal error: expected {total} pages, got {len(writer.pages)}.")

    if s.stamp:
        for section in sections:
            for doc in section.docs:
                if doc.pending:
                    continue
                for number in range(doc.start, doc.end + 1):
                    label = f"{s.stamp_prefix}  Page {number} of {total}".strip()
                    stamp_page(writer.pages[number - 1], label, args.stamp_position)

    # Bookmarks
    writer.add_outline_item("Cover", 0)
    if toc_pages:
        writer.add_outline_item("Contents", 1)
    imported = 0
    for section in sections:
        parent = writer.add_outline_item(section_heading(section, s), section.first_page - 1, bold=True)
        for doc in section.docs:
            title = f"{doc.number} {doc.title}".strip() + (" (pending)" if doc.pending else "")
            item = writer.add_outline_item(title, doc.start - 1, parent=parent, is_open=False)
            if s.keep_source_bookmarks and not doc.pending:
                imported += import_outline(writer, doc, item)

    for page_index, rect, target in links:
        writer.add_annotation(page_index, Link(rect=rect, target_page_index=target, border=[0, 0, 0]))

    writer.add_metadata({
        "/Title": pdf_safe(s.title),
        "/Author": pdf_safe(s.organization),
        "/Subject": pdf_safe(s.subtitle or TYPE_LABELS[s.kind]),
        "/Creator": "pdf-binder kit (build_binder.py)",
    })
    writer.page_mode = "/UseOutlines"
    try:
        writer.create_viewer_preferences()
        writer.viewer_preferences.display_doctitle = True
    except Exception:
        pass

    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.name + ".partial")
    with open(temp, "wb") as handle:
        writer.write(handle)
    try:
        os.replace(temp, out)
    except PermissionError as exc:
        raise KitError(f"Could not replace {out}. Close it in your PDF viewer and run again.") from exc

    # Self-check: reopen the file and confirm page count and bookmarks.
    check = PdfReader(str(out))
    expected_marks = 1 + (1 if toc_pages else 0) + len(sections) + len(docs) + imported
    found_marks = count_outline(check.outline)
    ok = len(check.pages) == total and found_marks == expected_marks
    try:
        write_index_xlsx(index_out, s, sections, toc_pages, total, out, args, warnings)
    except PermissionError as exc:
        raise KitError(f"Could not write {index_out}. Close it in Excel and run again.") from exc

    pending = sum(1 for d in docs if d.pending)
    print(f"Binder built: {out}")
    print(f"  Pages: {total}  (cover 1, contents {toc_pages}, dividers {len(sections) if s.dividers else 0}, "
          f"documents {sum(d.page_count for d in docs if not d.pending)}, placeholders {pending})")
    print(f"  Sections: {len(sections)}   Documents: {len(docs)} ({pending} pending)")
    print(f"  Bookmarks: {found_marks} ({imported} copied from the documents' own bookmarks)")
    print(f"  Page numbers stamped: {'yes' if s.stamp else 'no'}")
    print(f"  Index: {index_out}")
    print("  Self-check: " + ("page count and bookmarks OK" if ok else
                              f"MISMATCH (pages {len(check.pages)}/{total}, bookmarks {found_marks}/{expected_marks})"))
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
    print("Next: run verify_binder.py on the binder, then open it and check it by eye.")
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge a folder of PDFs into one indexed, bookmarked binder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example (client files go in the kit's jobs/ folder, which git ignores):\n"
               "  .venv/bin/python scripts/build_binder.py --pdf-folder jobs/acme/docs --index jobs/acme/index.csv "
               "--cover jobs/acme/cover.toml --out jobs/acme/output/Binder.pdf")
    parser.add_argument("--pdf-folder", required=True, help="folder that holds the PDF files")
    parser.add_argument("--index", required=True, help="index file (.csv or .xlsx)")
    parser.add_argument("--sheet", help="sheet to read in an .xlsx index (default: 'Binder Index', "
                                        "'Index' or the first sheet with the right columns)")
    parser.add_argument("--out", required=True, help="binder PDF to create")
    parser.add_argument("--cover", help="cover file (.toml or .json); see templates/binder-cover-*.toml")
    parser.add_argument("--type", help="binder type: sds, submittal, handover or general (overrides the cover file)")
    parser.add_argument("--title", help="binder title (overrides the cover file)")
    parser.add_argument("--subtitle", help="subtitle (overrides the cover file)")
    parser.add_argument("--watermark", help="faint diagonal text on generated pages, e.g. SAMPLE or DRAFT")
    parser.add_argument("--page-size", choices=["letter", "a4"], help="size of generated pages (default letter)")
    parser.add_argument("--page-numbers", action="store_true",
                        help="stamp 'Page X of Y' in the bottom margin of every document page")
    parser.add_argument("--stamp-prefix", help="text before the stamped page number, e.g. 'Project 2041 O&M'")
    parser.add_argument("--stamp-position", default="bottom-right",
                        choices=["bottom-right", "bottom-center", "bottom-left", "top-right"],
                        help="where the stamped page number goes (default bottom-right)")
    parser.add_argument("--no-dividers", action="store_true", help="leave out section divider pages")
    parser.add_argument("--no-toc", action="store_true", help="leave out the contents pages")
    parser.add_argument("--tabs", choices=["numbers", "letters", "none"], default="numbers",
                        help="number sections 1, 2, 3 or A, B, C (default numbers)")
    parser.add_argument("--section-word", default="Section", help="word before the section number, e.g. Tab")
    parser.add_argument("--missing", choices=["error", "placeholder", "skip"], default="error",
                        help="what to do when a listed file is missing or unreadable (default: stop)")
    parser.add_argument("--no-source-bookmarks", action="store_true",
                        help="don't copy each document's own bookmarks into the binder")
    parser.add_argument("--index-out", help="index spreadsheet to write (default: <binder>-index.xlsx)")
    parser.add_argument("--cover-only", action="store_true", help="only draw the cover page (to proof it)")
    args = parser.parse_args(argv)
    try:
        return build(args)
    except KitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
