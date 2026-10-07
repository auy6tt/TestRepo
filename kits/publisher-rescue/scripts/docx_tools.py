"""Helpers on top of python-docx for formatting it has no direct API for:
borders, shading, columns, page-number fields, tick boxes and the theme.

Word is strict about the order of elements inside its XML, so every helper
inserts its element in the position the Office Open XML standard requires.
"""

from __future__ import annotations

import itertools

from lxml import etree

from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

# Elements that must come AFTER the one being inserted (schema order).
_PPR_AFTER_PBDR = (
    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi",
    "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing",
    "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
    "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle",
    "w:rPr", "w:sectPr", "w:pPrChange",
)
_PPR_AFTER_SHD = _PPR_AFTER_PBDR[1:]
_RPR_AFTER_SPACING = (
    "w:w", "w:kern", "w:position", "w:sz", "w:szCs", "w:highlight", "w:u", "w:effect",
    "w:bdr", "w:shd", "w:fitText", "w:vertAlign", "w:rtl", "w:cs", "w:em", "w:lang",
    "w:eastAsianLayout", "w:specVanish", "w:oMath",
)
_TCPR_AFTER_BORDERS = (
    "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
    "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge", "w:tcPrChange",
)
_TCPR_AFTER_SHD = _TCPR_AFTER_BORDERS[1:]
_TCPR_AFTER_TCMAR = _TCPR_AFTER_BORDERS[3:]
_TBLPR_AFTER_BORDERS = ("w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
                        "w:tblCaption", "w:tblDescription", "w:tblPrChange")
_TBLPR_AFTER_CELLMAR = _TBLPR_AFTER_BORDERS[3:]
_TRPR_ORDER = ("w:cnfStyle", "w:divId", "w:gridBefore", "w:gridAfter", "w:wBefore",
               "w:wAfter", "w:cantSplit", "w:trHeight", "w:tblHeader",
               "w:tblCellSpacing", "w:jc", "w:hidden")


def _put(parent, tag: str, element, successors) -> None:
    """Replace `tag` in `parent` with `element`, keeping schema order."""
    old = parent.find(qn(tag))
    if old is not None:
        parent.remove(old)
    parent.insert_element_before(element, *successors)


def _border_el(tag: str, size_eighths: int, color: str, space: int = 0,
               style: str = "single"):
    el = OxmlElement(tag)
    el.set(qn("w:val"), style)
    el.set(qn("w:sz"), str(size_eighths))
    el.set(qn("w:space"), str(space))
    el.set(qn("w:color"), color)
    return el


# ---------------------------------------------------------------------------
# Paragraphs and runs
# ---------------------------------------------------------------------------

def paragraph_border(pPr, **edges) -> None:
    """edges: top=(size_in_eighths_of_a_point, "RRGGBB", space_pt), bottom=..."""
    pbdr = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right", "between"):
        if edge in edges and edges[edge]:
            size, color, space = edges[edge]
            pbdr.append(_border_el(f"w:{edge}", size, color, space))
    _put(pPr, "w:pBdr", pbdr, _PPR_AFTER_PBDR)


def paragraph_shading(pPr, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _put(pPr, "w:shd", shd, _PPR_AFTER_SHD)


def letter_spacing(rPr, points: float) -> None:
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:val"), str(int(round(points * 20))))
    _put(rPr, "w:spacing", spacing, _RPR_AFTER_SPACING)


def theme_fonts(rPr, which: str) -> None:
    """Point a run or style at the theme's heading ("major") or body ("minor")
    font, so Design > Fonts in Word changes it everywhere."""
    rfonts = rPr.find(qn("w:rFonts"))
    if rfonts is None:
        return
    rfonts.set(qn("w:asciiTheme"), f"{which}HAnsi")
    rfonts.set(qn("w:hAnsiTheme"), f"{which}HAnsi")
    rfonts.set(qn("w:eastAsiaTheme"), f"{which}EastAsia")
    rfonts.set(qn("w:cstheme"), f"{which}Bidi")


def theme_color(rPr, theme: str) -> None:
    """Tie an existing colour to a theme colour (accent1, accent2, text2 ...)."""
    color = rPr.find(qn("w:color"))
    if color is not None:
        color.set(qn("w:themeColor"), theme)


def shrink_paragraph(paragraph) -> None:
    """Make an empty paragraph (such as a section break) almost invisible."""
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing = Pt(1)
    pPr = paragraph._p.get_or_add_pPr()
    rpr = pPr.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        pPr.insert_element_before(rpr, "w:sectPr", "w:pPrChange")
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "2")
    rpr.append(size)


def add_field(paragraph, instruction: str, placeholder: str = "1"):
    """Insert a simple field such as PAGE or NUMPAGES."""
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), instruction)
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = placeholder
    run.append(text)
    field.append(run)
    paragraph._p.append(field)
    return field


_CONTROL_IDS = itertools.count(41001)


def add_checkbox(paragraph, checked: bool = False, size_pt: float | None = None) -> None:
    """A real Word tick box (content control) that can be clicked on screen."""
    sdt = OxmlElement("w:sdt")
    sdt_pr = OxmlElement("w:sdtPr")
    r_pr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:eastAsia", "w:hAnsi"):
        fonts.set(qn(attr), "MS Gothic")
    r_pr.append(fonts)
    sdt_pr.append(r_pr)
    sid = OxmlElement("w:id")
    sid.set(qn("w:val"), str(next(_CONTROL_IDS)))
    sdt_pr.append(sid)
    w14 = "http://schemas.microsoft.com/office/word/2010/wordml"
    box = etree.SubElement(sdt_pr, f"{{{w14}}}checkbox", nsmap={"w14": w14})
    etree.SubElement(box, f"{{{w14}}}checked").set(f"{{{w14}}}val", "1" if checked else "0")
    state = etree.SubElement(box, f"{{{w14}}}checkedState")
    state.set(f"{{{w14}}}val", "2612")
    state.set(f"{{{w14}}}font", "MS Gothic")
    state = etree.SubElement(box, f"{{{w14}}}uncheckedState")
    state.set(f"{{{w14}}}val", "2610")
    state.set(f"{{{w14}}}font", "MS Gothic")
    sdt.append(sdt_pr)
    content = OxmlElement("w:sdtContent")
    run = OxmlElement("w:r")
    run_pr = OxmlElement("w:rPr")
    run_fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:eastAsia", "w:hAnsi"):
        run_fonts.set(qn(attr), "MS Gothic")
    run_fonts.set(qn("w:hint"), "eastAsia")
    run_pr.append(run_fonts)
    if size_pt:
        for tag in ("w:sz", "w:szCs"):
            size = OxmlElement(tag)
            size.set(qn("w:val"), str(int(size_pt * 2)))
            run_pr.append(size)
    run.append(run_pr)
    text = OxmlElement("w:t")
    text.text = "☒" if checked else "☐"
    run.append(text)
    content.append(run)
    sdt.append(content)
    paragraph._p.append(sdt)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def cell_shading(cell, fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _put(tcPr, "w:shd", shd, _TCPR_AFTER_SHD)


def cell_margins(cell, top=0, left=0, bottom=0, right=0) -> None:
    """Inner padding of one cell, in points."""
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for edge, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(int(value * 20)))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    _put(tcPr, "w:tcMar", mar, _TCPR_AFTER_TCMAR)


def cell_borders(cell, **edges) -> None:
    """edges: top=(size_eighths, "RRGGBB") ... or None for no border."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        spec = edges.get(edge)
        if spec:
            borders.append(_border_el(f"w:{edge}", spec[0], spec[1]))
        else:
            borders.append(_border_el(f"w:{edge}", 0, "auto", style="nil"))
    _put(tcPr, "w:tcBorders", borders, _TCPR_AFTER_BORDERS)


def table_borders(table, color: str | None = None, size_eighths: int = 4,
                  inside_h: bool = False) -> None:
    """No borders at all (default), or thin borders in one colour."""
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if color and (edge != "insideV") and (edge != "insideH" or inside_h):
            borders.append(_border_el(f"w:{edge}", size_eighths, color))
        else:
            borders.append(_border_el(f"w:{edge}", 0, "auto", style="nil"))
    _put(tblPr, "w:tblBorders", borders, _TBLPR_AFTER_BORDERS)


def table_cell_padding(table, top=0, left=5.4, bottom=0, right=5.4) -> None:
    """Default inner padding for every cell, in points."""
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(int(value * 20)))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    _put(tblPr, "w:tblCellMar", mar, _TBLPR_AFTER_CELLMAR)


def table_widths(table, widths) -> None:
    """Fix column widths (python-docx Length values) so Word, LibreOffice
    and Google Docs all lay the table out the same way."""
    table.autofit = False
    total = sum(int(w) for w in widths)
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.insert_element_before(
            tblW, "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd",
            "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption",
            "w:tblDescription", "w:tblPrChange")
    tblW.set(qn("w:w"), str(int(total / 635)))  # EMU to twentieths of a point
    tblW.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for col, width in zip(grid.findall(qn("w:gridCol")), widths):
        col.set(qn("w:w"), str(int(int(width) / 635)))
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = width


def row_cant_split(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.insert_element_before(OxmlElement("w:cantSplit"),
                                   *_TRPR_ORDER[_TRPR_ORDER.index("w:cantSplit") + 1:])


def repeat_header_row(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:tblHeader")) is None:
        trPr.insert_element_before(OxmlElement("w:tblHeader"),
                                   *_TRPR_ORDER[_TRPR_ORDER.index("w:tblHeader") + 1:])


# ---------------------------------------------------------------------------
# Sections, styles, theme, properties
# ---------------------------------------------------------------------------

def set_columns(section, number: int, space_pt: float = 18) -> None:
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.insert_element_before(
            cols, "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
            "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
            "w:printerSettings", "w:sectPrChange")
    cols.set(qn("w:num"), str(number))
    cols.set(qn("w:space"), str(int(space_pt * 20)))


def get_or_add_style(doc, name: str, kind=WD_STYLE_TYPE.PARAGRAPH, base: str | None = None):
    styles = doc.styles
    try:
        style = styles[name]
    except KeyError:
        style = styles.add_style(name, kind)
        if base:
            style.base_style = styles[base]
    style.hidden = False
    style.quick_style = True
    return style


def style_text(style, font: str | None = None, theme: str | None = None,
               size: float | None = None, bold: bool | None = None,
               italic: bool | None = None, color: str | None = None,
               color_theme: str | None = None, caps: bool | None = None,
               spacing: float | None = None) -> None:
    """Set character formatting on a style. theme: "major" or "minor"."""
    f = style.font
    if font:
        f.name = font
        rPr = style.element.get_or_add_rPr()
        rfonts = rPr.find(qn("w:rFonts"))
        for attr in ("w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), font)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
        if theme:
            theme_fonts(rPr, theme)
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color:
        f.color.rgb = RGBColor.from_string(color)
        rPr = style.element.get_or_add_rPr()
        color_el = rPr.find(qn("w:color"))
        for attr in ("w:themeColor", "w:themeShade", "w:themeTint"):
            if color_el.get(qn(attr)) is not None:
                del color_el.attrib[qn(attr)]
        if color_theme:
            theme_color(rPr, color_theme)
    if caps is not None:
        f.all_caps = caps
    if spacing is not None:
        letter_spacing(style.element.get_or_add_rPr(), spacing)


def set_theme(doc, heading_font: str, body_font: str, colors: dict) -> None:
    """Update the document theme so Word's Design tab and built-in styles
    match the template. colors: {"dk2": "1F3A5F", "accent1": ..., ...}."""
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    for part in doc.part.package.iter_parts():
        if not str(part.partname).endswith("/theme/theme1.xml"):
            continue
        root = etree.fromstring(part.blob)
        scheme = root.find(".//a:clrScheme", ns)
        scheme.set("name", "Publisher Rescue")
        for slot, value in colors.items():
            el = scheme.find(f"a:{slot}", ns)
            if el is None:
                continue
            for child in list(el):
                el.remove(child)
            etree.SubElement(el, f"{{{ns['a']}}}srgbClr").set("val", value)
        fonts = root.find(".//a:fontScheme", ns)
        fonts.set("name", "Publisher Rescue")
        fonts.find("a:majorFont/a:latin", ns).set("typeface", heading_font)
        fonts.find("a:minorFont/a:latin", ns).set("typeface", body_font)
        part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                                    standalone=True)


def set_properties(doc, title: str, subject: str = "", keywords: str = "") -> None:
    props = doc.core_properties
    props.title = title
    props.subject = subject
    props.keywords = keywords
    props.author = ""
    props.last_modified_by = ""
    props.comments = ""
    props.revision = 1


def bullet_color(doc, color: str) -> None:
    """Colour the bullets of the built-in 'List Bullet' style."""
    numbering = doc.part.numbering_part.element
    for abstract in numbering.findall(qn("w:abstractNum")):
        lvl = abstract.find(qn("w:lvl"))
        pstyle = lvl.find(qn("w:pStyle")) if lvl is not None else None
        if pstyle is None or pstyle.get(qn("w:val")) != "ListBullet":
            continue
        rpr = lvl.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            lvl.append(rpr)
        col = rpr.find(qn("w:color"))
        if col is None:
            col = OxmlElement("w:color")
            # rFonts comes first in rPr; colour goes after it
            rpr.append(col)
        col.set(qn("w:val"), color)
        ind = lvl.find(qn("w:pPr") + "/" + qn("w:ind"))
        if ind is not None:
            ind.set(qn("w:left"), "284")
            ind.set(qn("w:hanging"), "227")
        tab = lvl.find(qn("w:pPr") + "/" + qn("w:tabs") + "/" + qn("w:tab"))
        if tab is not None:
            tab.set(qn("w:pos"), "284")
