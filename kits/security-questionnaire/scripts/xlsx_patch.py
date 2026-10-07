"""Edit an .xlsx/.xlsm file at the XML level and leave everything else untouched.

Why not just use openpyxl to save? openpyxl rebuilds the whole workbook and
drops what it does not understand: shapes, form controls, some drop-down
lists, threaded comments, slicers. A buyer's questionnaire must come back
looking exactly as they sent it, so this module changes only:

  * the cells we fill (plain text; each cell keeps its existing style);
  * the sheet we add (the review sheet) or remove (when finalising);
  * the few workbook files that list sheets, styles and content types.

Every other file inside the .xlsx package is copied byte for byte.
"""
from __future__ import annotations

import copy
import posixpath
import re
import time
import zipfile

from lxml import etree

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_STRICT = "http://purl.oclc.org/ooxml/spreadsheetml/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
M = "{%s}" % NS_MAIN
R_ID = "{%s}id" % NS_REL
REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CT_SHEET = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
DEFAULT_DECLARATION = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
MAX_CELL_CHARS = 32767
_PARSER = etree.XMLParser(remove_blank_text=False, huge_tree=True, resolve_entities=False)
_ILLEGAL_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
_BAD_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")


class XlsxError(Exception):
    """The file cannot be edited safely."""


# --------------------------------------------------------------------------
# Cell references
# --------------------------------------------------------------------------

def col_letter(n: int) -> str:
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def col_number(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def split_ref(ref: str) -> tuple[str, int]:
    m = re.fullmatch(r"\$?([A-Za-z]{1,3})\$?(\d+)", ref.strip())
    if not m:
        raise XlsxError(f"not a cell reference: {ref}")
    return m.group(1).upper(), int(m.group(2))


def quote_sheet(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def absolute_range(ref: str) -> str:
    parts = []
    for part in ref.split(":"):
        letters, row = split_ref(part)
        parts.append(f"${letters}${row}")
    return ":".join(parts)


# --------------------------------------------------------------------------
# Cell-level helpers
# --------------------------------------------------------------------------

def _set_text(cell, text: str) -> None:
    """Make `cell` hold `text` as an inline string, keeping its style."""
    text = _ILLEGAL_XML.sub("", text)[:MAX_CELL_CHARS]
    for child in list(cell):
        if child.tag in (M + "v", M + "is", M + "f"):
            cell.remove(child)
    for attr in ("t", "cm", "vm"):
        cell.attrib.pop(attr, None)
    cell.set("t", "inlineStr")
    is_el = etree.Element(M + "is")
    t = etree.SubElement(is_el, M + "t")
    t.text = text
    if text != text.strip() or "\n" in text or "  " in text:
        t.set(XML_SPACE, "preserve")
    ext = cell.find(M + "extLst")
    if ext is not None:
        ext.addprevious(is_el)
    else:
        cell.append(is_el)


def _column_style_lookup(root):
    ranges = []
    cols = root.find(M + "cols")
    if cols is not None:
        for col in cols:
            if col.tag == M + "col" and col.get("style"):
                ranges.append((int(col.get("min", "0")), int(col.get("max", "0")), col.get("style")))

    def lookup(cnum: int):
        for lo, hi, style in ranges:
            if lo <= cnum <= hi:
                return style
        return None
    return lookup


def _new_cell(row, rnum: int, cnum: int, col_style):
    cell = etree.Element(M + "c")
    cell.set("r", f"{col_letter(cnum)}{rnum}")
    # Same rule Excel uses when you type into an empty cell: row format first, then column format.
    style = row.get("s") if row.get("customFormat") in ("1", "true") else col_style(cnum)
    if style and style != "0":
        cell.set("s", style)
    return cell


def _get_cell(row, rnum: int, cnum: int, col_style):
    cells = [c for c in row if c.tag == M + "c"]
    prev = 0
    for c in cells:  # make implicit positions explicit before inserting anything
        if c.get("r") is None:
            prev += 1
            c.set("r", f"{col_letter(prev)}{rnum}")
        else:
            prev = col_number(split_ref(c.get("r"))[0])
    for c in cells:
        n = col_number(split_ref(c.get("r"))[0])
        if n == cnum:
            return c
        if n > cnum:
            new = _new_cell(row, rnum, cnum, col_style)
            c.addprevious(new)
            return new
    new = _new_cell(row, rnum, cnum, col_style)
    if cells:
        cells[-1].addnext(new)
    else:
        row.insert(0, new)
    return new


def _widen_spans(row, cnum: int) -> None:
    spans = row.get("spans")
    if not spans:
        return
    nums = [int(x) for part in spans.split() for x in part.split(":") if x.isdigit()]
    if nums:
        row.set("spans", f"{min(nums + [cnum])}:{max(nums + [cnum])}")


def _update_dimension(root, cells: list[tuple[int, int]]) -> None:
    dim = root.find(M + "dimension")
    if dim is None or not cells:
        return
    ref = dim.get("ref", "A1")
    try:
        parts = [split_ref(p) for p in ref.split(":")]
    except XlsxError:
        return
    rows = [p[1] for p in parts] + [r for r, _c in cells]
    cols = [col_number(p[0]) for p in parts] + [c for _r, c in cells]
    dim.set("ref", f"{col_letter(min(cols))}{min(rows)}:{col_letter(max(cols))}{max(rows)}")


def write_cells(root, values: dict[str, str]) -> list[str]:
    """Write text into a worksheet tree. Returns refs skipped because they hold a formula."""
    sheet_data = root.find(M + "sheetData")
    if sheet_data is None:
        raise XlsxError("worksheet has no sheetData element")
    rows = [r for r in sheet_data if r.tag == M + "row"]
    last = 0
    for row in rows:
        if row.get("r") is None:
            last += 1
            row.set("r", str(last))
        else:
            last = int(row.get("r"))
    by_num = {int(r.get("r")): r for r in rows}
    col_style = _column_style_lookup(root)
    targets = []
    for ref, text in values.items():
        letters, rnum = split_ref(ref)
        targets.append((rnum, col_number(letters), f"{letters}{rnum}", text))
    targets.sort()
    skipped, written = [], []
    for rnum, cnum, ref, text in targets:
        row = by_num.get(rnum)
        if row is None:
            row = etree.Element(M + "row")
            row.set("r", str(rnum))
            later = [n for n in by_num if n > rnum]
            if later:
                by_num[min(later)].addprevious(row)
            else:
                sheet_data.append(row)
            by_num[rnum] = row
        cell = _get_cell(row, rnum, cnum, col_style)
        if cell.find(M + "f") is not None:
            skipped.append(ref)
            continue
        _set_text(cell, text)
        written.append((rnum, cnum))
        if row.get("customHeight") not in ("1", "true"):
            row.attrib.pop("ht", None)  # let Excel/LibreOffice size the row to the new text
        _widen_spans(row, cnum)
    _update_dimension(root, written)
    return skipped


# --------------------------------------------------------------------------
# Package
# --------------------------------------------------------------------------

class XlsxPackage:
    """An .xlsx/.xlsm package opened for careful editing."""

    def __init__(self, path):
        try:
            with zipfile.ZipFile(path) as z:
                self._infos = [i for i in z.infolist()]
                self._data = {i.filename: z.read(i.filename) for i in self._infos}
        except zipfile.BadZipFile as exc:
            raise XlsxError(f"{path} is not a valid .xlsx file (it is not a zip package)") from exc
        self._trees: dict[str, etree._Element] = {}
        self._modified: set[str] = set()
        self._removed: set[str] = set()
        self._added: list[str] = []
        self._style_cache: dict[tuple, int | None] = {}
        if "[Content_Types].xml" not in self._data or "_rels/.rels" not in self._data:
            raise XlsxError(f"{path} is not a valid .xlsx package")
        wb = None
        for rel in self._tree("_rels/.rels"):
            if rel.get("Type", "").endswith("/officeDocument"):
                wb = rel.get("Target", "").lstrip("/")
        if not wb or wb not in self._data:
            raise XlsxError("workbook part not found")
        self.workbook_part = wb
        root = self._tree(wb)
        if root.tag.startswith("{%s}" % NS_STRICT):
            raise XlsxError("this file uses the 'Strict Open XML' format. Open it in Excel and save it as a normal "
                            "'Excel Workbook (.xlsx)' first.")
        self.workbook_rels = self._rels_path(wb)
        self.signed = any(n.startswith("_xmlsignatures/") for n in self._data)

    # ---- low-level part access
    @staticmethod
    def _rels_path(part: str) -> str:
        folder, name = posixpath.split(part)
        return posixpath.join(folder, "_rels", name + ".rels")

    def _exists(self, part: str) -> bool:
        return (part in self._data or part in self._added) and part not in self._removed

    def _tree(self, part: str):
        if part not in self._trees:
            if part not in self._data:
                raise XlsxError(f"missing part {part}")
            self._trees[part] = etree.fromstring(self._data[part], _PARSER)
        return self._trees[part]

    def _touch(self, part: str) -> None:
        self._modified.add(part)

    def _resolve(self, source_part: str, target: str) -> str:
        if target.startswith("/"):
            return target.lstrip("/")
        return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))

    def _serialize(self, part: str) -> bytes:
        original = self._data.get(part, b"")
        m = re.match(rb"<\?xml[^>]*\?>\s*", original)
        decl = m.group(0) if m and re.search(rb"encoding=[\"']utf-8[\"']", m.group(0), re.I) else DEFAULT_DECLARATION
        return decl + etree.tostring(self._trees[part], encoding="UTF-8", xml_declaration=False)

    # ---- sheets
    def sheets(self) -> list[dict]:
        root = self._tree(self.workbook_part)
        rels = {r.get("Id"): r for r in self._tree(self.workbook_rels)}
        out = []
        sheets_el = root.find(M + "sheets")
        for s in (sheets_el if sheets_el is not None else []):
            if s.tag != M + "sheet":
                continue
            rel = rels.get(s.get(R_ID))
            part = self._resolve(self.workbook_part, rel.get("Target")) if rel is not None else None
            kind = rel.get("Type", "").rsplit("/", 1)[-1] if rel is not None else ""
            out.append({"name": s.get("name"), "sheetId": s.get("sheetId"), "rid": s.get(R_ID),
                        "part": part, "kind": kind, "state": s.get("state", "visible"), "el": s})
        return out

    def sheet_names(self) -> list[str]:
        return [s["name"] for s in self.sheets()]

    def _sheet(self, name: str) -> dict:
        for s in self.sheets():
            if s["name"] == name:
                if s["kind"] != "worksheet" or not s["part"]:
                    raise XlsxError(f"sheet '{name}' is not a normal worksheet")
                return s
        raise XlsxError(f"no sheet named '{name}'")

    def set_cells(self, sheet_name: str, values: dict[str, str]) -> list[str]:
        """Write text into cells, e.g. {'E12': 'Yes'}. Returns refs skipped because they hold formulas."""
        if not values:
            return []
        part = self._sheet(sheet_name)["part"]
        skipped = write_cells(self._tree(part), values)
        self._touch(part)
        return skipped

    # ---- styles for the added sheet
    def _styles_part(self) -> str | None:
        for rel in self._tree(self.workbook_rels):
            if rel.get("Type") == REL_BASE + "styles":
                part = self._resolve(self.workbook_part, rel.get("Target"))
                return part if part in self._data else None
        return None

    def style_index(self, spec: dict) -> int | None:
        """Add a cell style (bold, color, fill, size, underline, wrap, valign, numfmt) and return its index."""
        key = tuple(sorted(spec.items()))
        if key in self._style_cache:
            return self._style_cache[key]
        part = self._styles_part()
        idx = None
        if part:
            root = self._tree(part)
            fonts, fills, xfs = root.find(M + "fonts"), root.find(M + "fills"), root.find(M + "cellXfs")
            if fonts is not None and fills is not None and xfs is not None and len(fonts):
                base = fonts[0]
                font = etree.SubElement(fonts, M + "font")
                if spec.get("bold"):
                    etree.SubElement(font, M + "b")
                if spec.get("underline"):
                    etree.SubElement(font, M + "u")
                sz = base.find(M + "sz")
                etree.SubElement(font, M + "sz", val=str(spec.get("size") or (sz.get("val") if sz is not None else "11")))
                if spec.get("color"):
                    etree.SubElement(font, M + "color", rgb="FF" + spec["color"])
                elif base.find(M + "color") is not None:
                    font.append(copy.deepcopy(base.find(M + "color")))
                name = base.find(M + "name")
                etree.SubElement(font, M + "name", val=name.get("val") if name is not None else "Calibri")
                for tag in ("family", "charset", "scheme"):
                    el = base.find(M + tag)
                    if el is None:
                        continue
                    if tag == "family" and el.get("val", "") not in {str(n) for n in range(1, 15)}:
                        continue  # some tools write family="0", which is not valid
                    font.append(copy.deepcopy(el))
                fonts.set("count", str(len(fonts)))
                fill_id = 0
                if spec.get("fill"):
                    fill = etree.SubElement(fills, M + "fill")
                    pattern = etree.SubElement(fill, M + "patternFill", patternType="solid")
                    etree.SubElement(pattern, M + "fgColor", rgb="FF" + spec["fill"])
                    etree.SubElement(pattern, M + "bgColor", indexed="64")
                    fills.set("count", str(len(fills)))
                    fill_id = len(fills) - 1
                numfmt = int(spec.get("numfmt", 0))  # a built-in format id, e.g. 2 = "0.00"
                xf = etree.SubElement(xfs, M + "xf", numFmtId=str(numfmt), fontId=str(len(fonts) - 1),
                                      fillId=str(fill_id), borderId="0")
                if root.find(M + "cellStyleXfs") is not None:
                    xf.set("xfId", "0")
                if numfmt:
                    xf.set("applyNumberFormat", "1")
                xf.set("applyFont", "1")
                if fill_id:
                    xf.set("applyFill", "1")
                xf.set("applyAlignment", "1")
                align = etree.SubElement(xf, M + "alignment", vertical=spec.get("valign", "top"))
                if spec.get("wrap"):
                    align.set("wrapText", "1")
                xfs.set("count", str(len(xfs)))
                self._touch(part)
                idx = len(xfs) - 1
        self._style_cache[key] = idx
        return idx

    # ---- adding and removing sheets
    def _free_sheet_part(self) -> str:
        folder = posixpath.join(posixpath.dirname(self.workbook_part), "worksheets")
        n = 1
        while self._exists(posixpath.join(folder, f"sheet{n}.xml")) or posixpath.join(folder, f"sheet{n}.xml") in self._data:
            n += 1
        return posixpath.join(folder, f"sheet{n}.xml")

    def _free_rid(self, rels) -> str:
        used = {r.get("Id") for r in rels}
        n = 1 + max([int(m.group(1)) for i in used if i and (m := re.fullmatch(r"rId(\d+)", i))] or [0])
        while f"rId{n}" in used:
            n += 1
        return f"rId{n}"

    def _add_defined_name(self, name: str, text: str, local_sheet: int, hidden: bool = True) -> None:
        wb = self._tree(self.workbook_part)
        dn = wb.find(M + "definedNames")
        if dn is None:
            dn = etree.Element(M + "definedNames")
            for tag in ("externalReferences", "functionGroups", "sheets"):
                anchor = wb.find(M + tag)
                if anchor is not None:
                    anchor.addnext(dn)
                    break
        el = etree.SubElement(dn, M + "definedName", name=name, localSheetId=str(local_sheet))
        if hidden:
            el.set("hidden", "1")
        el.text = text

    def add_sheet(self, name: str, rows: list[list], *, widths=(), freeze_rows: int = 0, freeze_cols: int = 0,
                  autofilter: str | None = None, links=(), lists=(), merges=(), row_heights=None,
                  print_area: str | None = None, print_title_rows: str | None = None,
                  tab_color: str | None = None) -> None:
        """Append a new worksheet at the end of the workbook.

        rows: list of rows; each cell is None, a str/int/float, or (value, style_dict).
        links: (cell_ref, location, display) internal hyperlinks.
        lists: (sqref, [allowed values]) drop-down lists.
        merges: ranges to merge, e.g. "A1:J1". row_heights: {row number: height in points}.
        print_area: e.g. "A1:J40". print_title_rows: rows repeated on each printed page, e.g. "7:7".
        """
        if not name or len(name) > 31 or _BAD_SHEET_CHARS.search(name) or name.startswith("'") or name.endswith("'"):
            raise XlsxError(f"invalid sheet name: {name!r}")
        if any(s["name"].lower() == name.lower() for s in self.sheets()):
            raise XlsxError(f"the workbook already has a sheet named '{name}'")
        row_heights = row_heights or {}

        ws = etree.Element(M + "worksheet", nsmap={None: NS_MAIN, "r": NS_REL})
        pr = etree.SubElement(ws, M + "sheetPr")
        if tab_color:
            etree.SubElement(pr, M + "tabColor", rgb="FF" + tab_color)
        etree.SubElement(pr, M + "pageSetUpPr", fitToPage="1")
        n_cols = max([len(r) for r in rows] + [1])
        etree.SubElement(ws, M + "dimension", ref=f"A1:{col_letter(n_cols)}{max(len(rows), 1)}")
        view = etree.SubElement(etree.SubElement(ws, M + "sheetViews"), M + "sheetView", workbookViewId="0")
        if freeze_rows or freeze_cols:
            top_left = f"{col_letter(freeze_cols + 1)}{freeze_rows + 1}"
            pane = etree.SubElement(view, M + "pane")
            if freeze_cols:
                pane.set("xSplit", str(freeze_cols))
            if freeze_rows:
                pane.set("ySplit", str(freeze_rows))
            active = "bottomRight" if freeze_rows and freeze_cols else ("bottomLeft" if freeze_rows else "topRight")
            pane.set("topLeftCell", top_left)
            pane.set("activePane", active)
            pane.set("state", "frozen")
            if freeze_rows and freeze_cols:
                etree.SubElement(view, M + "selection", pane="topRight", activeCell=f"{col_letter(freeze_cols + 1)}1",
                                 sqref=f"{col_letter(freeze_cols + 1)}1")
                etree.SubElement(view, M + "selection", pane="bottomLeft", activeCell=f"A{freeze_rows + 1}",
                                 sqref=f"A{freeze_rows + 1}")
            etree.SubElement(view, M + "selection", pane=active, activeCell=top_left, sqref=top_left)
        etree.SubElement(ws, M + "sheetFormatPr", defaultRowHeight="15")
        if widths:
            cols = etree.SubElement(ws, M + "cols")
            for i, width in enumerate(widths, start=1):
                etree.SubElement(cols, M + "col", min=str(i), max=str(i), width=str(width), customWidth="1")
        data = etree.SubElement(ws, M + "sheetData")
        for r, row in enumerate(rows, start=1):
            row_el = etree.Element(M + "row", r=str(r))
            if r in row_heights:
                row_el.set("ht", str(row_heights[r]))
                row_el.set("customHeight", "1")
            for c, cell in enumerate(row, start=1):
                value, style = cell if isinstance(cell, tuple) else (cell, None)
                if (value is None or value == "") and not style:
                    continue
                c_el = etree.SubElement(row_el, M + "c", r=f"{col_letter(c)}{r}")
                if style:
                    idx = self.style_index(style)
                    if idx is not None:
                        c_el.set("s", str(idx))
                if value is None or value == "":
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    etree.SubElement(c_el, M + "v").text = repr(value) if isinstance(value, float) else str(value)
                else:
                    _set_text(c_el, str(value))
            if len(row_el) or r in row_heights:
                data.append(row_el)
        if autofilter:
            etree.SubElement(ws, M + "autoFilter", ref=autofilter)
        if merges:
            mc = etree.SubElement(ws, M + "mergeCells", count=str(len(merges)))
            for ref in merges:
                etree.SubElement(mc, M + "mergeCell", ref=ref)
        if lists:
            dvs = etree.SubElement(ws, M + "dataValidations", count=str(len(lists)))
            for sqref, values in lists:
                dv = etree.SubElement(dvs, M + "dataValidation", type="list", allowBlank="1",
                                      showErrorMessage="1", sqref=sqref)
                etree.SubElement(dv, M + "formula1").text = '"' + ",".join(values) + '"'
        if links:
            hl = etree.SubElement(ws, M + "hyperlinks")
            for ref, location, display in links:
                etree.SubElement(hl, M + "hyperlink", ref=ref, location=location, display=display)
        etree.SubElement(ws, M + "pageMargins", left="0.4", right="0.4", top="0.5", bottom="0.5",
                         header="0.3", footer="0.3")
        etree.SubElement(ws, M + "pageSetup", orientation="landscape", fitToWidth="1", fitToHeight="0")

        part = self._free_sheet_part()
        self._trees[part] = ws
        self._added.append(part)
        self._modified.add(part)

        rels = self._tree(self.workbook_rels)
        rid = self._free_rid(rels)
        etree.SubElement(rels, "{%s}Relationship" % NS_PKG, Id=rid, Type=REL_BASE + "worksheet",
                         Target=posixpath.relpath(part, posixpath.dirname(self.workbook_part)))
        self._touch(self.workbook_rels)

        wb = self._tree(self.workbook_part)
        sheets_el = wb.find(M + "sheets")
        ids = [int(s.get("sheetId")) for s in sheets_el if (s.get("sheetId") or "").isdigit()]
        new = etree.SubElement(sheets_el, M + "sheet", name=name, sheetId=str(max(ids + [0]) + 1))
        new.set(R_ID, rid)
        index = len([s for s in sheets_el if s.tag == M + "sheet"]) - 1
        if autofilter:
            self._add_defined_name("_xlnm._FilterDatabase", f"{quote_sheet(name)}!{absolute_range(autofilter)}", index)
        if print_area:
            self._add_defined_name("_xlnm.Print_Area", f"{quote_sheet(name)}!{absolute_range(print_area)}", index,
                                   hidden=False)
        if print_title_rows:
            first, last = print_title_rows.split(":")
            self._add_defined_name("_xlnm.Print_Titles", f"{quote_sheet(name)}!${first}:${last}", index, hidden=False)
        self._touch(self.workbook_part)

        ct = self._tree("[Content_Types].xml")
        etree.SubElement(ct, "{%s}Override" % NS_CT, PartName="/" + part, ContentType=CT_SHEET)
        self._touch("[Content_Types].xml")

    def _all_rel_targets(self, exclude: set[str]) -> set[str]:
        targets = set()
        for name in list(self._data) + self._added:
            if not name.endswith(".rels") or name in exclude or name in self._removed:
                continue
            source = name.replace("_rels/", "")[:-5]
            for rel in self._tree(name):
                if rel.get("TargetMode") == "External":
                    continue
                targets.add(self._resolve(source, rel.get("Target", "")))
        return targets

    def _remove_part(self, part: str, protected: set[str]) -> None:
        """Remove a part, its .rels file, and anything only it pointed to."""
        if not self._exists(part) or part in protected:
            return
        self._removed.add(part)
        rels = self._rels_path(part)
        children = []
        if self._exists(rels):
            for rel in self._tree(rels):
                if rel.get("TargetMode") != "External":
                    children.append(self._resolve(part, rel.get("Target", "")))
            self._removed.add(rels)
        still_used = self._all_rel_targets(exclude=set())
        for child in children:
            if child not in still_used:
                self._remove_part(child, protected)
        ct = self._tree("[Content_Types].xml")
        for el in list(ct):
            if el.get("PartName", "").lstrip("/") in self._removed:
                ct.remove(el)
        self._touch("[Content_Types].xml")

    def remove_sheet(self, name: str) -> None:
        sheets = self.sheets()
        idx = next((i for i, s in enumerate(sheets) if s["name"] == name), None)
        if idx is None:
            raise XlsxError(f"no sheet named '{name}'")
        if len(sheets) == 1:
            raise XlsxError("cannot remove the only sheet")
        target = sheets[idx]
        had_formulas = bool(target["part"] and self._exists(target["part"])
                            and self._tree(target["part"]).find(".//" + M + "f") is not None)
        wb = self._tree(self.workbook_part)
        wb.find(M + "sheets").remove(target["el"])
        rels = self._tree(self.workbook_rels)
        for rel in list(rels):
            if rel.get("Id") == target["rid"]:
                rels.remove(rel)
        self._touch(self.workbook_rels)

        dn = wb.find(M + "definedNames")
        if dn is not None:
            ref_re = re.compile(r"(?:^|[^A-Za-z0-9_.'])(?:" + re.escape(quote_sheet(name)) + "|" + re.escape(name) + r")!")
            for d in list(dn):
                local = d.get("localSheetId")
                if (local is not None and local.isdigit() and int(local) == idx) or ref_re.search(d.text or ""):
                    dn.remove(d)
                elif local is not None and local.isdigit() and int(local) > idx:
                    d.set("localSheetId", str(int(local) - 1))
            if len(dn) == 0:
                wb.remove(dn)

        remaining = [s for s in self.sheets()]
        visible = [i for i, s in enumerate(remaining) if s["state"] == "visible"] or [0]
        for view in wb.iter(M + "workbookView"):
            for attr in ("activeTab", "firstSheet"):
                value = view.get(attr)
                if value is None or not value.isdigit():
                    continue
                v = int(value)
                if v == idx:
                    v = visible[0]
                elif v > idx:
                    v -= 1
                if attr == "activeTab" and v not in visible:
                    v = visible[0]
                view.set(attr, str(v))
        self._touch(self.workbook_part)

        protected = {s["part"] for s in remaining if s["part"]}
        self._remove_part(target["part"], protected)

        if had_formulas:  # Excel rebuilds the calculation chain if it is missing
            for rel in list(rels):
                if rel.get("Type") == REL_BASE + "calcChain":
                    self._remove_part(self._resolve(self.workbook_part, rel.get("Target")), set())
                    rels.remove(rel)

        # Keep exactly one selected tab (otherwise Excel may open with no tab or grouped tabs).
        selected = []
        for s in remaining:
            if s["kind"] == "worksheet" and s["part"] and self._exists(s["part"]):
                view = self._tree(s["part"]).find(f"{M}sheetViews/{M}sheetView")
                if view is not None and view.get("tabSelected") in ("1", "true"):
                    selected.append(s)
        if not selected:
            active = 0
            for view in wb.iter(M + "workbookView"):
                active = int(view.get("activeTab", "0") or 0)
                break
            if active < len(remaining) and remaining[active]["kind"] == "worksheet":
                view = self._tree(remaining[active]["part"]).find(f"{M}sheetViews/{M}sheetView")
                if view is not None:
                    view.set("tabSelected", "1")
                    self._touch(remaining[active]["part"])

    def tidy_font_order(self) -> None:
        """Put <font> children in the order the standard requires (openpyxl writes name/color first)."""
        part = self._styles_part()
        if not part:
            return
        order = ["b", "i", "strike", "condense", "extend", "outline", "shadow", "u", "vertAlign", "sz", "color",
                 "name", "family", "charset", "scheme"]
        rank = {M + t: i for i, t in enumerate(order)}
        for font in self._tree(part).iter(M + "font"):
            children = list(font)
            ordered = sorted(children, key=lambda el: rank.get(el.tag, len(order)))
            if ordered != children:
                for el in children:
                    font.remove(el)
                font.extend(ordered)
                self._touch(part)

    # ---- save
    def save(self, path) -> None:
        names = [i.filename for i in self._infos if i.filename not in self._removed]
        names += [n for n in self._added if n not in self._removed]
        names.sort(key=lambda n: 0 if n == "[Content_Types].xml" else 1)
        infos = {i.filename: i for i in self._infos}
        now = time.localtime()[:6]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name in names:
                if name in self._modified:
                    data = self._serialize(name)
                else:
                    data = self._data[name]
                old = infos.get(name)
                info = zipfile.ZipInfo(name, date_time=old.date_time if old else now)
                info.compress_type = old.compress_type if old else zipfile.ZIP_DEFLATED
                if old is not None:
                    info.external_attr = old.external_attr
                z.writestr(info, data)
