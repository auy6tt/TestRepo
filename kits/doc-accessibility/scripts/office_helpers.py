"""Small helpers for making accessible Word files with python-docx.

Used by build_templates.py, build_samples.py and make_report.py. Every helper
here exists to keep the structure right: real heading styles, table header
rows that repeat, alt text on pictures, a document title and a language.
"""
from __future__ import annotations

import datetime as dt
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


def set_properties(document, title: str = "", author: str = "", language: str = "en-US",
                   subject: str = "", when: dt.datetime | None = None) -> None:
    """Title, author and language in File > Properties, and the default text language."""
    props = document.core_properties
    props.title = title
    props.author = author
    props.last_modified_by = author
    props.subject = subject
    props.comments = ""
    props.keywords = ""
    props.language = language or ""
    stamp = when or dt.datetime.now().replace(microsecond=0)
    props.created = stamp
    props.modified = stamp
    props.revision = 1
    if language:
        set_default_language(document, language)


def set_default_language(document, language: str) -> None:
    styles = document.styles.element
    defaults = styles.find(qn("w:docDefaults"))
    if defaults is None:
        defaults = OxmlElement("w:docDefaults")
        styles.insert(0, defaults)
    rpr_default = defaults.find(qn("w:rPrDefault"))
    if rpr_default is None:
        rpr_default = OxmlElement("w:rPrDefault")
        defaults.insert(0, rpr_default)
    rpr = rpr_default.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        rpr_default.append(rpr)
    lang = rpr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rpr.append(lang)
    lang.set(qn("w:val"), language)


def set_base_font(document, name: str = "Calibri", size: int = 11) -> None:
    style = document.styles["Normal"]
    style.font.name = name
    style.font.size = Pt(size)


def mark_header_row(row) -> None:
    """Make a table row a real header row that repeats on each page."""
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:tblHeader")) is None:
        header = OxmlElement("w:tblHeader")
        header.set(qn("w:val"), "true")
        tr_pr.append(header)


def add_table(document, headers: list[str], rows: list[list[str]], header_row: bool = True,
              style: str = "Table Grid", widths: list[float] | None = None):
    table = document.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = style
    for col, text in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(text))
        run.bold = True
    for r, values in enumerate(rows, start=1):
        for col, text in enumerate(values):
            table.cell(r, col).text = str(text)
    if header_row:
        mark_header_row(table.rows[0])
    if widths:
        for row in table.rows:
            for col, width in enumerate(widths):
                row.cells[col].width = Inches(width)
    return table


def add_picture(document, image_path: str | Path, width_in: float, alt_text: str | None):
    """Add a picture. alt_text=None leaves it without alt text (to show the problem)."""
    document.add_picture(str(image_path), width=Inches(width_in))
    doc_pr = document.inline_shapes[-1]._inline.docPr
    doc_pr.attrib.pop("descr", None)
    doc_pr.attrib.pop("title", None)
    if alt_text:
        doc_pr.set("descr", alt_text)
    return document.inline_shapes[-1]


def add_page_number_footer(document, prefix: str = "Page ") -> None:
    for section in document.sections:
        paragraph = section.footer.paragraphs[0]
        paragraph.text = ""
        if prefix:
            paragraph.add_run(prefix)
        run = paragraph.add_run()
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        inner = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = "1"
        inner.append(text)
        field.append(inner)
        run._r.append(field)


def patch_app_properties(docx_path: str | Path, application: str, pages: int | None = None) -> None:
    """Rewrite docProps/app.xml so 'made with' and the page count are honest."""
    path = Path(docx_path)
    with tempfile.TemporaryDirectory() as tmp:
        temp_file = Path(tmp) / path.name
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(temp_file, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == "docProps/app.xml":
                    xml = data.decode("utf-8")
                    xml = re.sub(r"<Application>.*?</Application>", f"<Application>{application}</Application>", xml)
                    if pages is not None:
                        xml = re.sub(r"<Pages>\d+</Pages>", f"<Pages>{pages}</Pages>", xml)
                    xml = re.sub(r"<Template>.*?</Template>", "<Template>Normal.dotm</Template>", xml)
                    data = xml.encode("utf-8")
                target.writestr(item, data)
        shutil.move(str(temp_file), str(path))
