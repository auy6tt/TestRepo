#!/usr/bin/env python3
"""Read safety data sheet (SDS) PDFs and build a chemical inventory spreadsheet.

For each PDF in a folder it looks for:
  product name, manufacturer or supplier, revision or issue date, signal word,
  hazard statement codes (H200-H420) and pictogram names
It flags sheets that are older than a set number of years, sheets dated
before OSHA's 2024 HazCom update, old-style MSDS forms, scans with no text,
and anything it is unsure about ("Needs review"). It never changes a PDF.

Optional: give it the client's on-site chemical list (--site-list) and it
matches each product to a sheet and flags products with no sheet and sheets
for products that are not on the list.

Output: inventory.xlsx with these sheets
  Inventory    one row per product / sheet, with status and review notes
  Chemical List a plain printable list for the employer to confirm
  Binder Index ready for build_binder.py (--sheet "Binder Index")
  Summary      counts by status
  Settings     age limit and cutoff date used by the status formulas
  Read me      how to read and check the inventory

Example:
  python scripts/extract_sds.py --sds-folder work/sds --site-list work/site-list.xlsx \\
      --out work/inventory.xlsx --group-by location

The spreadsheet records what the sheets SAY. It is not a hazard assessment.
A person checks every flagged row against the PDF, and the client confirms
the final list.
"""
from __future__ import annotations

import argparse
import logging
import datetime as dt
import difflib
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

try:
    import xlsxwriter
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing package '{exc.name}'. Run: pip install -r requirements.txt")

try:
    import pdfplumber
except ImportError:  # optional, but recommended
    pdfplumber = None

import kitlib

logging.getLogger("pypdf").setLevel(logging.ERROR)   # the scripts report problems in plain words
from kitlib import KitError

RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
MAX_PAGES = 40
DEFAULT_CUTOFF = "2024-07-19"   # the date OSHA's 2024 HazCom update took effect

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
PRODUCT_LABELS = [
    r"product\s*name", r"trade\s*name", r"product\s*/\s*trade\s*name", r"commercial\s*(?:product\s*)?name",
    r"material\s*name", r"chemical\s*product\s*name", r"name\s*of\s*(?:the\s*)?product", r"substance\s*name",
    r"mixture\s*name", r"product\s*title", r"ghs\s*product\s*identifier",
    r"product\s*identifier(?:\s*used\s*on\s*the\s*label)?",
    r"identity\s*(?:\(\s*as\s*used\s*on\s*label\s*(?:and|&)\s*list\s*\))?",
    r"product(?=\s*:)", r"material(?=\s*:)",
]
SUPPLIER_LABELS = [
    r"manufacturer\s*/\s*(?:supplier|distributor|importer)", r"supplier\s*/\s*manufacturer",
    r"manufacturer'?s?\s*name", r"manufacturer(?:\s*(?:information|details|identification))?",
    r"manufactured\s*(?:by|for)", r"supplier'?s?\s*(?:name|information|details)?", r"supplied\s*by",
    r"distributor(?:\s*name)?", r"distributed\s*by", r"importer", r"company\s*name",
    r"company(?:\s*(?:identification|information|details))?", r"responsible\s*party",
    r"details\s*of\s*the\s*supplier(?:\s*of\s*the\s*safety\s*data\s*sheet)?",
    r"name,?\s*address,?\s*(?:and|&)\s*telephone(?:\s*number)?(?:\s*of\s*the\s*[a-z ,]*party)?",
]
DATE_LABELS = [
    (1, r"(?:m?sds\s*)?revision\s*date|date\s*of\s*(?:last\s*|latest\s*)?revision|last\s*revised|"
        r"date\s*revised|rev(?:\.|ision)?\s*date|revised(?:\s*on)?|last\s*updated|date\s*updated|updated\s*on|"
        r"revision(?=\s*[:#]?\s*(?:\d{1,4}[/.\-]\d|[a-z]{3,9}\.?\s+\d))"),
    (2, r"(?:m?sds\s*)?issue\s*date|date\s*of\s*(?:m?sds\s*)?issue|issued(?:\s*on)?|issuing\s*date|date\s*issued|"
        r"effective\s*date|version\s*date|release\s*date|publication\s*date|"
        r"date\s*of\s*(?:m?sds\s*)?preparation|preparation\s*date|date\s*prepared|prepared(?:\s*on)?|"
        r"creation\s*date|date\s*of\s*compilation|compilation\s*date|m?sds\s*date"),
    (3, r"date(?=\s*[:#])"),
    (4, r"print(?:ed)?\s*date|date\s*printed|date\s*of\s*print(?:ing)?|printed\s*on"),
]
DATE_EXCLUDE = re.compile(r"supersed|previous|replaces|first\s*issue|original\s*issue|initial\s*(?:issue|date)|"
                          r"date\s*of\s*first|expir|birth|manufactur(?:e|ing)\s*date|lot\s*|batch", re.I)
OTHER_LABELS_STRONG = [
    r"recommended\s*uses?", r"relevant\s*identified\s*uses?", r"uses?\s*advised\s*against",
    r"restrictions?\s*on\s*use", r"product\s*(?:code|no\.?|number|id|type|use|form|category)",
    r"item\s*(?:no\.?|number|code)", r"part\s*(?:no\.?|number)", r"catalog(?:ue)?\s*(?:no\.?|number)",
    r"other\s*means\s*of\s*identification", r"emergency\s*(?:telephone|phone|contact|number)",
    r"cas\s*(?:no\.?|number|#)", r"(?:m?sds)\s*(?:no\.?|number|#|id|code)", r"un\s*(?:no\.?|number)",
    r"chemical\s*(?:family|nature|formula|characterization)", r"signal\s*words?", r"hazard\s*statements?",
    r"precautionary\s*statements?", r"(?:hazard\s*)?pictograms?", r"label\s*elements", r"other\s*hazards",
    r"supplemental\s*(?:hazard\s*)?information", r"street\s*address", r"mailing\s*address",
    r"telephone\s*(?:no\.?|number)", r"print(?:ed)?\s*date", r"version\s*(?:no\.?|number)",
]
OTHER_LABELS_WEAK = [
    r"address", r"street", r"city", r"(?:tele)?phone", r"tel\.?", r"fax", r"e-?mail", r"web\s*site|website|url",
    r"emergency", r"synonyms?", r"cas", r"version", r"formula", r"contact(?:\s*person)?", r"prepared\s*by",
    r"supersedes", r"page", r"classification", r"brand", r"country", r"zip", r"postal\s*code", r"uses?",
    r"product\s*code", r"sku",
]
STOP_RE = re.compile(
    r"\s(?:\|\s|(?:product\s*(?:code|no\.?|number|id)|item\s*(?:no\.?|number|code)|part\s*(?:no\.?|number)|"
    r"recommended\s*use|restrictions?\s*on\s*use|other\s*means\s*of\s*identification|cas\s*(?:no\.?|#|number)|"
    r"revision\s*date|issue\s*date|print\s*date|m?sds\s*(?:no\.?|#|number)|page\s*\d+\s*of)|"
    r"(?:synonyms?|version|supersedes|(?:tele)?phone|tel\.?|fax|e-?mail|emergency(?:\s*(?:telephone|phone|number))?|"
    r"address|cas)\s*[:#])", re.I)

SECTION_KEYWORDS = {
    1: r"identif|identity|product|company", 2: r"hazard", 3: r"composition|ingredient", 4: r"first",
    5: r"fire", 6: r"accidental|release|spill", 7: r"handling|storage", 8: r"exposure|protection",
    9: r"physical|chemical\s*prop", 10: r"stability|reactivity", 11: r"toxicolog", 12: r"ecolog",
    13: r"disposal", 14: r"transport", 15: r"regulat", 16: r"other",
}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}
HEAD_SECTION = re.compile(r"^(?:section|sect\.?|sec\.?)\s*[-:#.]?\s*(\d{1,2}|[ivx]{1,4})(?![\w])\s*[-:.)—–]*\s*(.*)$",
                          re.I)
HEAD_NUMBER = re.compile(r"^(\d{1,2})\s*[.:)]?\s+([A-Za-z].{2,90})$")

HCODE_RE = re.compile(r"(?<![A-Za-z0-9])H\s?(2\d\d|3\d\d|4[0-2]\d)(?!\d)")
SUFFIX_RE = re.compile(r"(FD|Fd|Df|fd|F|D|f|d|i)(?![A-Za-z])")
VALID_SUFFIX = {"350": {"i"}, "360": {"F", "D", "FD", "Fd", "Df"}, "361": {"f", "d", "fd"}}

# Standard GHS hazard statement wording, used only when a sheet prints the
# statements without their H-codes (common on US sheets). Longest first.
H_PHRASES = [
    ("H300+H310+H330", "fatal if swallowed,? in contact with skin,? or if inhaled"),
    ("H301+H311+H331", "toxic if swallowed,? in contact with skin,? or if inhaled"),
    ("H302+H312+H332", "harmful if swallowed,? in contact with skin,? or if inhaled"),
    ("H300+H310", "fatal if swallowed or in contact with skin"),
    ("H300+H330", "fatal if swallowed or (?:if )?inhaled"),
    ("H310+H330", "fatal in contact with skin or (?:if )?inhaled"),
    ("H301+H311", "toxic if swallowed or in contact with skin"),
    ("H301+H331", "toxic if swallowed or (?:if )?inhaled"),
    ("H311+H331", "toxic in contact with skin or (?:if )?inhaled"),
    ("H302+H312", "harmful if swallowed or in contact with skin"),
    ("H302+H332", "harmful if swallowed or (?:if )?inhaled"),
    ("H312+H332", "harmful in contact with skin or (?:if )?inhaled"),
    ("H315+H320", "causes skin and eye irritation"),
    ("H200", "unstable explosives?"),
    ("H201", "explosive;? mass explosion hazard"),
    ("H202", "explosive;? severe projection hazard"),
    ("H203", "explosive;? fire,? blast or projection hazard"),
    ("H204", "fire or projection hazard"),
    ("H205", "may mass explode in fire"),
    ("H220", "extremely flammable gas"),
    ("H221", "(?<!extremely )flammable gas"),
    ("H222", "extremely flammable aerosol"),
    ("H223", "(?<!extremely )flammable aerosol"),
    ("H224", "extremely flammable liquid and vapou?r"),
    ("H225", "highly flammable liquid and vapou?r"),
    ("H226", "(?<!extremely )(?<!highly )flammable liquid and vapou?r"),
    ("H227", "combustible liquid"),
    ("H228", "flammable solid"),
    ("H229", "pressuri[sz]ed container:? may burst if heated"),
    ("H231", "may react explosively even in the absence of air at elevated pressure and/or temperature"),
    ("H230", "may react explosively even in the absence of air"),
    ("H232", "may ignite spontaneously if exposed to air"),
    ("H240", "heating may cause an explosion"),
    ("H241", "heating may cause a fire or explosion"),
    ("H242", "heating may cause a fire"),
    ("H250", "catches fire spontaneously if exposed to air"),
    ("H251", "self-?heating;? may catch fire"),
    ("H252", "self-?heating in large quantities;? may catch fire"),
    ("H260", "in contact with water releases? flammable gases which may ignite spontaneously"),
    ("H261", "in contact with water releases? flammable gas"),
    ("H270", "may cause or intensify fire;? oxidi[sz]er"),
    ("H271", "may cause fire or explosion;? strong oxidi[sz]er"),
    ("H272", "may intensify fire;? oxidi[sz]er"),
    ("H280", "contains gas under pressure;? may explode if heated"),
    ("H281", "contains refrigerated gas;? may cause cryogenic burns or injury"),
    ("H290", "may be corrosive to metals"),
    ("H304", "may be fatal if swallowed and enters? airways"),
    ("H305", "may be harmful if swallowed and enters? airways"),
    ("H303", "may be harmful if swallowed"),
    ("H313", "may be harmful in contact with skin"),
    ("H333", "may be harmful if inhaled"),
    ("H300", "fatal if swallowed"),
    ("H301", "toxic if swallowed"),
    ("H302", "harmful if swallowed"),
    ("H310", "fatal in contact with skin"),
    ("H311", "toxic in contact with skin"),
    ("H312", "harmful in contact with skin"),
    ("H314", "causes severe skin burns and eye damage"),
    ("H316", "causes mild skin irritation"),
    ("H315", "causes skin irritation"),
    ("H317", "may cause an allergic skin reaction"),
    ("H318", "causes serious eye damage"),
    ("H319", "causes serious eye irritation"),
    ("H320", "causes eye irritation"),
    ("H330", "fatal if inhaled"),
    ("H331", "toxic if inhaled"),
    ("H332", "harmful if inhaled"),
    ("H334", "may cause allergy or asthma symptoms or breathing difficulties if inhaled"),
    ("H335", "may cause respiratory irritation"),
    ("H336", "may cause drowsiness or dizziness"),
    ("H340", "may cause genetic defects"),
    ("H341", "suspected of causing genetic defects"),
    ("H350i", "may cause cancer by inhalation"),
    ("H350", "may cause cancer"),
    ("H351", "suspected of causing cancer"),
    ("H360", "may damage fertility or the unborn child"),
    ("H360F", "may damage fertility"),
    ("H360D", "may damage the unborn child"),
    ("H361", "suspected of damaging fertility or the unborn child"),
    ("H361f", "suspected of damaging fertility"),
    ("H361d", "suspected of damaging the unborn child"),
    ("H362", "may cause harm to breast-?fed children"),
    ("H372", r"causes damage to organs?(?: \([^)]*\))? through prolonged or repeated exposure"),
    ("H373", r"may cause damage to organs?(?: \([^)]*\))? through prolonged or repeated exposure"),
    ("H370", "causes damage to organs?"),
    ("H371", "may cause damage to organs?"),
    ("H410", "very toxic to aquatic life with long[- ]lasting effects"),
    ("H411", "toxic to aquatic life with long[- ]lasting effects"),
    ("H412", "harmful to aquatic life with long[- ]lasting effects"),
    ("H413", "may cause long[- ]lasting harmful effects to aquatic life"),
    ("H400", "very toxic to aquatic life"),
    ("H401", "toxic to aquatic life"),
    ("H402", "harmful to aquatic life"),
    ("H420", "harms public health and the environment by destroying ozone in the upper atmosphere"),
]
KNOWN_CODES = {code for combo, _ in H_PHRASES for code in combo.split("+")} | {
    "H206", "H207", "H208", "H282", "H283", "H284"}
H_PHRASE_RES = [(code, re.compile(pattern)) for code, pattern in H_PHRASES]   # text is matched with single spaces

PICTOGRAMS = {
    "GHS01": "Exploding bomb", "GHS02": "Flame", "GHS03": "Flame over circle", "GHS04": "Gas cylinder",
    "GHS05": "Corrosion", "GHS06": "Skull and crossbones", "GHS07": "Exclamation mark",
    "GHS08": "Health hazard", "GHS09": "Environment",
}
PICTO_NAME_RES = [
    ("GHS01", re.compile(r"exploding\s*bomb", re.I)),
    ("GHS03", re.compile(r"flame\s*over\s*(?:a\s*)?circle", re.I)),
    ("GHS02", re.compile(r"\bflames?\b(?!\s*over)", re.I)),
    ("GHS04", re.compile(r"gas\s*cylinder", re.I)),
    ("GHS05", re.compile(r"\bcorrosion\b|\bcorrosive\b", re.I)),
    ("GHS06", re.compile(r"skull\s*(?:and|&)\s*cross\s*-?\s*bones", re.I)),
    ("GHS07", re.compile(r"exclamation\s*(?:mark|point)", re.I)),
    ("GHS08", re.compile(r"health\s*hazard", re.I)),
    ("GHS09", re.compile(r"\benvironment(?:al)?\b", re.I)),
]
PICTO_CODE_RE = re.compile(r"\bGHS\s*0?([1-9])\b", re.I)
NOT_CLASSIFIED_RE = re.compile(
    r"not\s+(?:a\s+)?(?:classified\s+as\s+)?hazardous|not\s+classified|does\s+not\s+meet\s+the\s+criteria\s+for\s+"
    r"classification|no\s+(?:ghs\s+)?hazard\s+classification|not\s+considered\s+hazardous|"
    r"no\s+hazards?\s+(?:identified|classification)", re.I)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_PATTERNS = [
    ("ymd", re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b")),
    ("num", re.compile(r"\b(\d{1,2})([-/.])(\d{1,2})[-/.](\d{4}|\d{2})\b")),
    ("dmy_text", re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[\s\-./]*" + MON + r"[\s\-./,]*(\d{4}|\d{2})\b", re.I)),
    ("mdy_text", re.compile(r"\b" + MON + r"[\s\-./]*(\d{1,2})(?:st|nd|rd|th)?,?[\s\-./]+(\d{4})\b", re.I)),
    ("ymd_text", re.compile(r"\b(\d{4})[\s\-./]*" + MON + r"[\s\-./]*(\d{1,2})\b", re.I)),
    ("my_text", re.compile(r"\b" + MON + r"[\s\-./,]*(\d{4})\b", re.I)),
]


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
@dataclass
class Found:
    value: object = None
    conf: str = "none"
    how: str = ""
    issue: str = ""


@dataclass
class DateFound(Found):
    label: str = ""
    raw: str = ""
    alt: dt.date | None = None
    group: int = 0


@dataclass
class SheetResult:
    path: Path
    rel: str
    pages: int = 0
    engine: str = ""
    chars: int = 0
    product: Found = field(default_factory=Found)
    supplier: Found = field(default_factory=Found)
    date: DateFound = field(default_factory=DateFound)
    signal: Found = field(default_factory=Found)
    hcodes: Found = field(default_factory=Found)
    pictos: Found = field(default_factory=Found)
    version: Found = field(default_factory=Found)
    flags: set = field(default_factory=set)
    notes: list = field(default_factory=list)
    review: list = field(default_factory=list)
    manual: dict = field(default_factory=dict)     # field -> note, for details entered by hand
    checked: str = ""                              # set when a person marked the whole sheet as checked


# ---------------------------------------------------------------------------
# Text extraction and clean-up
# ---------------------------------------------------------------------------
_TRANS = str.maketrans({" ": " ", "‐": "-", "‑": "-", "‒": "-", "–": "-",
                        "—": "-", "−": "-", "‘": "'", "’": "'", "“": '"',
                        "”": '"', "\t": " ", "​": "", "﻿": "", "­": ""})


def fix_letter_spacing(line: str) -> str:
    """'S E C T I O N  2' -> 'SECTION 2'."""
    tokens = [t for t in line.split(" ") if t]
    if len(tokens) < 5 or sum(1 for t in tokens if len(t) == 1) / len(tokens) < 0.75:
        return line
    parts = re.split(r" {2,}", line.strip())
    if len(parts) > 1:
        return " ".join(p.replace(" ", "") for p in parts)
    return line.replace(" ", "")


def normalize_text(raw: str) -> list[str]:
    text = unicodedata.normalize("NFKC", raw or "").translate(_TRANS)
    lines = []
    for line in text.splitlines():
        line = fix_letter_spacing(line.rstrip())
        line = re.sub(r" {3,}", " | ", line.strip())
        line = re.sub(r" {2}", " ", line).strip(" |")
        if line:
            lines.append(line)
    return lines


def horizontal(obj) -> bool:
    """True for ordinary left-to-right text. Drops diagonal stamps such as
    'UNCONTROLLED COPY' or 'SAMPLE', whose letters would otherwise be mixed
    into the real lines of text."""
    if obj.get("object_type") != "char":
        return True
    matrix = obj.get("matrix") or (1, 0, 0, 1, 0, 0)
    a, b, c, d = matrix[:4]
    return a > 0 and d > 0 and abs(b) <= 0.05 * abs(a) and abs(c) <= 0.05 * abs(d)


def read_pages(path: Path, engine: str) -> list[str]:
    if engine == "pdfplumber":
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages[:MAX_PAGES]:
                pages.append(page.filter(horizontal).extract_text(x_tolerance=1.5, y_tolerance=3) or "")
        return pages
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    mode = "layout" if engine == "pypdf-layout" else "plain"
    return [(page.extract_text(extraction_mode=mode) or "") for page in reader.pages[:MAX_PAGES]]


def largest_text_line(path: Path) -> str:
    """Biggest upright text on page 1 (often the product name on the title)."""
    if pdfplumber is None:
        return ""
    try:
        with pdfplumber.open(str(path)) as pdf:
            chars = [c for c in pdf.pages[0].chars if horizontal(c) and c["text"].strip()]
    except Exception:
        return ""
    if not chars:
        return ""
    lines: dict[tuple, list] = {}
    for c in chars:
        key = (round(c["size"]), round(c["top"] / 3))
        lines.setdefault(key, []).append(c)
    ranked = sorted(lines.items(), key=lambda kv: (-kv[0][0], kv[0][1]))
    for (size, _), group in ranked[:6]:
        group.sort(key=lambda c: c["x0"])
        text, last = "", None
        for c in group:
            if last is not None and c["x0"] - last > c["size"] * 0.25:
                text += " "
            text += c["text"]
            last = c["x1"]
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 3 and not re.search(
                r"safety\s*data\s*sheet|material\s*safety|^\s*m?sds\s*$|according\s*to|page\s*\d|revision|"
                r"version|sample|not\s+a\s+real|confidential|section\s*\d", text, re.I):
            return text
    return ""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
def label_rx(label: str):
    return re.compile(r"^(?:\(?\d{1,2}(?:\.\d{1,2}){0,2}\)?\.?\s*)?(?:%s)(?![A-Za-z])\s*\.?\s*(?:[:#=]\s*|-\s+)?(.*)$"
                      % label, re.I)


ANY_LABEL_STRONG = re.compile(
    r"^(?:\(?\d{1,2}(?:\.\d{1,2}){0,2}\)?\.?\s*)?(?:%s)(?![A-Za-z])"
    % "|".join(PRODUCT_LABELS[:-2] + SUPPLIER_LABELS + [p for _, p in DATE_LABELS[:2]] + OTHER_LABELS_STRONG),
    re.I)
ANY_LABEL_WEAK = re.compile(
    r"^(?:\(?\d{1,2}(?:\.\d{1,2}){0,2}\)?\.?\s*)?(?:%s)\s*(?:[:#]|$)" % "|".join(
        OTHER_LABELS_WEAK + [r"product", r"material", r"date", r"supplier", r"manufacturer", r"company",
                             r"distributor"]), re.I)


def is_label(text: str) -> bool:
    return bool(ANY_LABEL_STRONG.match(text) or ANY_LABEL_WEAK.match(text))


def segments(line: str):
    yield line
    for part in line.split(" | ")[1:]:
        yield part


def clean_value(text: str) -> str:
    text = text.strip().lstrip(":#=-").strip()
    match = STOP_RE.search(" " + text)
    if match and match.start() > 1:
        text = (" " + text)[:match.start()].strip()
    return text.strip(" ,;|*").strip()


def valid_product(text: str):
    text = clean_value(text)
    if not (2 <= len(text) <= 150) or len(re.findall(r"[A-Za-z]", text)) < 2:
        return None
    if re.match(r"(?:not\s+(?:available|applicable|determined|known)|n/?a\b|none\b|see\s|unknown\b|"
                r"mixture\b|substance\b|safety\s*data|material\s*safety)", text, re.I):
        return None
    if is_label(text):
        return None
    return text


def valid_supplier(text: str):
    text = clean_value(text)
    text = re.split(r"\s(?=\d{2,6}\s+\w+.*\b(?:street|st\.?|avenue|ave\.?|road|rd\.?|drive|dr\.?|blvd|"
                    r"boulevard|lane|ln\.?|way|parkway|pkwy|suite|highway|hwy)\b)", text, maxsplit=1, flags=re.I)[0]
    text = re.split(r"\s(?:p\.?\s?o\.?\s*box\b|tel\b|phone\b|fax\b|www\.|https?:|\S+@)", text, maxsplit=1,
                    flags=re.I)[0]
    text = text.strip(" ,;|")
    if not (2 <= len(text) <= 120) or len(re.findall(r"[A-Za-z]", text)) < 2:
        return None
    if re.match(r"(?:\d|\+|\(\d|not\s+(?:available|applicable)|n/?a\b|see\s|same\s+as|address|emergency|"
                r"telephone|phone|fax|e-?mail|www|http)", text, re.I):
        return None
    if is_label(text):
        return None
    return text


def find_labelled(lines, labels, validate, lo=0, hi=None, lookahead=2) -> Found:
    hi = len(lines) if hi is None else min(hi, len(lines))
    for label in labels:
        rx = label_rx(label)
        for i in range(lo, hi):
            for segment in segments(lines[i]):
                match = rx.match(segment)
                if not match:
                    continue
                rest = match.group(1).strip()
                label_text = segment[:match.start(1)].strip(" :#=-")
                if rest:
                    value = validate(rest)
                    if value:
                        return Found(value, "high", f"labelled '{label_text}'")
                    if not is_label(clean_value(rest)):
                        continue
                for j in range(i + 1, min(i + 1 + lookahead, hi)):
                    candidate = lines[j].split(" | ")[0]
                    if is_label(candidate):
                        break
                    value = validate(candidate)
                    if value:
                        conf = "high" if (not rest and j == i + 1) else "medium"
                        return Found(value, conf, f"line after '{label_text}'")
                    break
    return Found()


def find_sections(lines):
    heads = []
    for i, line in enumerate(lines):
        match = HEAD_SECTION.match(line)
        roman = False
        if match:
            token = match.group(1).lower()
            if token.isdigit():
                number = int(token)
            else:
                number, roman = ROMAN.get(token), True
            title = match.group(2).strip()
            if number and 1 <= number <= 16:
                letters = re.sub(r"[^A-Za-z]", "", title)
                if (not title or roman or re.search(SECTION_KEYWORDS[number], title, re.I)
                        or (letters and letters.isupper())):
                    heads.append((i, number, title, roman))
            continue
        match = HEAD_NUMBER.match(line)
        if match:
            number, title = int(match.group(1)), match.group(2)
            if 1 <= number <= 16 and re.search(SECTION_KEYWORDS[number], title, re.I) and len(line) < 95 \
                    and not re.search(r"[.;]\s*\w+\s+\w+.*[.]$", title):
                heads.append((i, number, title, False))
    return heads


def section_range(heads, lines, number):
    """(start, end) line range of a section, or None. Picks the longest match
    so a contents list at the top of a sheet doesn't fool it."""
    best = None
    for k, (i, n, title, roman) in enumerate(heads):
        if n != number or roman:
            continue
        end = len(lines)
        for i2, n2, _, r2 in heads[k + 1:]:
            if n2 > number and not r2:
                end = i2
                break
        if best is None or (end - i) > (best[1] - best[0]):
            best = (i, end)
    return best


def hazards_range(lines, heads):
    found = section_range(heads, lines, 2)
    if found and found[1] - found[0] > 1:
        return found, True
    for i, line in enumerate(lines):
        if re.search(r"hazards?\s*(?:\(s\)\s*)?identification", line, re.I):
            for j in range(i + 1, len(lines)):
                if re.search(r"composition|information\s+on\s+ingredients|section\s*3", lines[j], re.I):
                    return (i, j), True
            return (i, min(len(lines), i + 80)), True
    return (0, len(lines)), False


# ----- dates -----------------------------------------------------------------
def year4(text: str, today: dt.date) -> int:
    value = int(text)
    if len(text) == 2:
        value += 2000 if value <= (today.year % 100) + 1 else 1900
    return value


def make_date(y, m, d):
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def date_convention(lines, default: str) -> str:
    dmy = mdy = 0
    for line in lines:
        for match in DATE_PATTERNS[1][1].finditer(line):
            a, sep, b = int(match.group(1)), match.group(2), int(match.group(3))
            if a > 12 and b <= 12:
                dmy += 2
            elif b > 12 and a <= 12:
                mdy += 2
            elif sep == ".":
                dmy += 1
    if dmy and not mdy:
        return "DMY"
    if mdy and not dmy:
        return "MDY"
    return default


def first_date(text: str, convention: str, today: dt.date):
    """Earliest date in text -> (date, raw, alternative reading or None)."""
    best = None
    for kind, rx in DATE_PATTERNS:
        for match in rx.finditer(text):
            if best is not None and match.start() >= best[0]:
                break
            result = None
            if kind == "ymd":
                result = (make_date(int(match.group(1)), int(match.group(2)), int(match.group(3))), None)
            elif kind == "num":
                a, sep, b, y = int(match.group(1)), match.group(2), int(match.group(3)), year4(match.group(4), today)
                order = "DMY" if (a > 12 or sep == "." and b <= 12 and convention != "MDY") else \
                    ("MDY" if b > 12 else convention)
                first = make_date(y, b, a) if order == "DMY" else make_date(y, a, b)
                alt = None
                if a <= 12 and b <= 12 and a != b and sep != ".":
                    alt = make_date(y, a, b) if order == "DMY" else make_date(y, b, a)
                result = (first, alt)
            elif kind == "dmy_text":
                result = (make_date(year4(match.group(3), today), MONTHS[match.group(2)[:3].lower()],
                                    int(match.group(1))), None)
            elif kind == "mdy_text":
                result = (make_date(int(match.group(3)), MONTHS[match.group(1)[:3].lower()], int(match.group(2))), None)
            elif kind == "ymd_text":
                result = (make_date(int(match.group(1)), MONTHS[match.group(2)[:3].lower()], int(match.group(3))), None)
            elif kind == "my_text":
                result = (make_date(int(match.group(2)), MONTHS[match.group(1)[:3].lower()], 1), None)
            if result and result[0] and 1970 <= result[0].year <= today.year + 1:
                best = (match.start(), result[0], match.group(0), result[1])
                break
    if best is None:
        return None
    return best[1], best[2], best[3]


def find_date(lines, convention, today) -> DateFound:
    candidates = []
    for i, line in enumerate(lines):
        for group, pattern in DATE_LABELS:
            for match in re.finditer(r"(?<![A-Za-z])(?:%s)(?![A-Za-z])" % pattern, line, re.I):
                if group == 3 and re.search(r"(?:print(?:ed)?|revision|issue|supersedes?|expiry)\s*$",
                                            line[:match.start()], re.I):
                    continue
                window_start = max(0, match.start() - 30)
                after = line[match.end():match.end() + 60]
                found = first_date(after, convention, today)
                if found is None and not after.strip(" :#-|.") and i + 1 < len(lines):
                    found = first_date(lines[i + 1][:60], convention, today)
                if not found:
                    continue
                pre = line[window_start:match.end()] + after[:max(0, after.find(found[1]))]
                if DATE_EXCLUDE.search(pre):
                    continue
                candidates.append((group, found[0], found[1], found[2], match.group(0).strip(" :")))
    if not candidates:
        for line in lines[:15] + lines[-30:]:
            found = first_date(line, convention, today)
            if found:
                return DateFound(found[0], "low", "unlabelled date near the top or bottom of the sheet",
                                 "no labelled revision or issue date", label="Unlabelled date", raw=found[1],
                                 alt=found[2])
        return DateFound(issue="no revision or issue date found")
    best_group = min(c[0] for c in candidates)
    group = [c for c in candidates if c[0] == best_group]
    dates = sorted({c[1] for c in group})
    chosen = max(group, key=lambda c: c[1])
    label = re.sub(r"\s+", " ", chosen[4]).strip(" :#.").capitalize()
    conf = {1: "high", 2: "high", 3: "medium", 4: "low"}[best_group]
    issue = ""
    if best_group == 3:
        issue = "only a plain 'Date' label was found"
    if best_group == 4:
        issue = "only a print date was found; the sheet's own revision date may differ"
    if len(dates) > 1:
        conf = "medium" if conf == "high" else conf
        issue = (issue + "; " if issue else "") + "several dates under this label (" + \
            ", ".join(d.isoformat() for d in dates[-4:]) + "); the latest was used"
    return DateFound(chosen[1], conf, f"labelled '{chosen[4]}'", issue, label=label, raw=chosen[2], alt=chosen[3],
                     group=best_group)


# ----- signal word, hazard codes, pictograms ----------------------------------
def find_signal(lines, hz_lo, hz_hi, hz_found) -> Found:
    rx = label_rx(r"signal\s*words?")
    for lo, hi in ((hz_lo, hz_hi), (0, len(lines))):
        for i in range(lo, hi):
            match = rx.match(lines[i])
            if not match:
                continue
            value = match.group(1).strip()
            if not value and i + 1 < len(lines):
                value = lines[i + 1]
            low = value.lower()
            has_danger, has_warning = "danger" in low, "warning" in low
            if has_danger and has_warning:
                return Found(None, "low", "labelled 'Signal word'", "both DANGER and WARNING after the label")
            if has_danger:
                return Found("Danger", "high", "labelled 'Signal word'")
            if has_warning:
                return Found("Warning", "high", "labelled 'Signal word'")
            if re.match(r"(?:none|no\s+signal\s+word|not\s+(?:applicable|required|classified)|n/?a\b|-)", low):
                return Found("None", "high", "labelled 'Signal word'")
    standalone = set()
    for i in range(hz_lo, hz_hi):
        word = re.sub(r"[^a-z]", "", lines[i].lower())
        if word in ("danger", "warning"):
            standalone.add(word.title())
    if len(standalone) == 1:
        return Found(standalone.pop(), "high" if hz_found else "medium", "unlabelled signal word in Section 2")
    if len(standalone) == 2:
        return Found(None, "low", "Section 2", "both DANGER and WARNING appear without a label")
    hz_text = " ".join(lines[hz_lo:hz_hi])
    if NOT_CLASSIFIED_RE.search(hz_text):
        return Found("None", "high", "sheet says the product is not classified as hazardous")
    return Found(issue="no signal word found")


def find_hcodes(lines, lo, hi) -> Found:
    text = " ".join(lines[lo:hi])
    codes = []
    for match in HCODE_RE.finditer(text):
        number = match.group(1)
        tail = SUFFIX_RE.match(text, match.end())
        suffix = tail.group(1) if tail and tail.group(1) in VALID_SUFFIX.get(number, set()) else ""
        code = f"H{number}{suffix}"
        if code not in codes:
            codes.append(code)
    if codes:
        unknown = [c for c in codes if c.rstrip("FDfdi") not in KNOWN_CODES and c not in KNOWN_CODES]
        issue = f"unrecognised code(s) {', '.join(unknown)}" if unknown else ""
        return Found(codes, "high" if not unknown else "medium", "printed", issue)
    joined = []
    for k in range(lo, hi):
        line = lines[k]
        if joined and joined[-1].endswith("-") and line[:1].islower():
            joined[-1] = joined[-1][:-1] + line
        else:
            joined.append(line)
    plain = re.sub(r"\s+", " ", " ".join(joined).lower())
    plain = plain.replace("vapor", "vapour").replace("vapouur", "vapour")
    found = []
    for combo, rx in H_PHRASE_RES:
        while True:
            match = rx.search(plain)
            if not match:
                break
            for code in combo.split("+"):
                if code not in found:
                    found.append(code)
            plain = plain[:match.start()] + "#" * (match.end() - match.start()) + plain[match.end():]
    if found:
        found.sort(key=lambda c: (int(c[1:4]), c))
        return Found(found, "medium", "matched from statement wording",
                     "codes are not printed on the sheet; they were matched from the hazard statement wording")
    return Found([], "high", "none found")


def find_pictograms(lines, lo, hi) -> Found:
    codes = []
    for line in lines[lo:hi]:
        for match in PICTO_CODE_RE.finditer(line):
            code = f"GHS0{match.group(1)}"
            if code not in codes:
                codes.append(code)
    label = label_rx(r"(?:ghs\s*)?(?:hazard\s*)?(?:pictograms?|symbols?)(?:\s*\(s\))?")
    stop = re.compile(r"^(?:\(?\d{1,2}(?:\.\d{1,2}){0,2}\)?\.?\s*)?(?:signal|hazard\s*statements?|"
                      r"precautionary|other\s*hazards|supplement|classification|contains|label\s*elements|"
                      r"prevention|response|storage|disposal)", re.I)
    labelled = False
    for i in range(lo, hi):
        match = label.match(lines[i])
        if not match:
            continue
        labelled = True
        window = [match.group(1)]
        for j in range(i + 1, min(i + 4, hi)):
            if stop.match(lines[j]):
                break
            window.append(lines[j])
        text = " ".join(window)
        if re.match(r"\s*(?:none|not\s+(?:applicable|required)|n/?a\b|no\s+(?:pictograms?|symbols?))", text, re.I):
            return Found([], "high", "none stated")
        for code, rx in PICTO_NAME_RES:
            if rx.search(text):
                if code not in codes:
                    codes.append(code)
                if code == "GHS03":
                    text = rx.sub(" ", text)
        break
    if codes:
        codes.sort()
        return Found(codes, "high", "named in text")
    if labelled:
        return Found([], "medium", "not named in text", "pictogram label found but the symbols seem to be images")
    return Found([], "low", "not in text")


def find_version(lines) -> Found:
    rx = re.compile(r"\b(?:version|rev(?:ision)?)\s*(?:no\.?|number|#)?\s*[:#]?\s*(\d{1,3}(?:\.\d{1,3}){0,3})\b(?![/.\-]\d)",
                    re.I)
    for line in lines[:80] + lines[-40:]:
        match = rx.search(line)
        if match:
            return Found(match.group(1), "high", "labelled version")
    return Found()


# ---------------------------------------------------------------------------
# One sheet
# ---------------------------------------------------------------------------
def parse_text(lines, convention_default, today):
    heads = find_sections(lines)
    s1 = section_range(heads, lines, 1)
    id_lo, id_hi = (0, s1[1]) if s1 else (0, min(len(lines), 90))
    (hz_lo, hz_hi), hz_found = hazards_range(lines, heads)
    result = {
        "heads": heads,
        "hazards_found": hz_found,
        "product": find_labelled(lines, PRODUCT_LABELS, valid_product, id_lo, id_hi),
        "supplier": find_labelled(lines, SUPPLIER_LABELS, valid_supplier, id_lo, id_hi, lookahead=3),
        "date": find_date(lines, date_convention(lines, convention_default), today),
        "signal": find_signal(lines, hz_lo, hz_hi, hz_found),
        "hcodes": find_hcodes(lines, hz_lo, hz_hi),
        "pictos": find_pictograms(lines, hz_lo, hz_hi),
        "version": find_version(lines),
    }
    if result["supplier"].value is None:
        suffix = re.compile(r"\b(?:inc|llc|ltd|limited|corp|corporation|company|co|gmbh|plc|llp|s\.?a|b\.?v|"
                            r"industries|chemicals?|products|manufacturing|group|laboratories|labs)\b\.?", re.I)
        for line in lines[id_lo:id_hi]:
            part = line.split(" | ")[0]
            if suffix.search(part) and valid_supplier(part) and not re.search(r"safety\s*data", part, re.I):
                result["supplier"] = Found(valid_supplier(part), "low", "line with a company name in Section 1",
                                           "no manufacturer or supplier label found")
                break
    return result


def score(parsed) -> int:
    return sum(RANK[parsed[k].conf] for k in ("product", "supplier", "date", "signal"))


def analyse(path: Path, folder: Path, args, today) -> SheetResult:
    res = SheetResult(path=path, rel=path.relative_to(folder).as_posix())
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            reader.decrypt("")
        res.pages = len(reader.pages)
    except Exception as exc:
        res.flags.add("unreadable")
        res.review.append(f"PDF could not be opened ({exc.__class__.__name__}); open it by hand")
        return res
    engines = (["pdfplumber"] if pdfplumber else []) + ["pypdf", "pypdf-layout"]
    best, best_lines = None, []
    for engine in engines:
        try:
            lines = normalize_text("\n".join(read_pages(path, engine)))
        except Exception:
            continue
        letters = len(re.findall(r"[A-Za-z]", " ".join(lines)))
        if letters < 200:
            if best is None:
                best_lines, res.chars = lines, letters
            continue
        parsed = parse_text(lines, args.date_order, today)
        if best is None or score(parsed) > score(best):
            best, best_lines, res.engine, res.chars = parsed, lines, engine, letters
        if score(best) >= 12:
            break
    if best is None:
        res.flags.add("no_text")
        res.review.append("no readable text (scanned image?). Read the sheet and type the details in, or run OCR")
        return res
    for key in ("product", "supplier", "date", "signal", "hcodes", "pictos", "version"):
        setattr(res, key, best[key])

    lines = best_lines
    full = "\n".join(lines)
    if res.product.value is None:
        fallback = largest_text_line(path)
        if fallback:
            res.product = Found(fallback, "low", "largest heading on page 1", "no product name label found")
        else:
            res.product = Found(path.stem.replace("_", " ").replace("-", " "), "low", "file name",
                                "no product name found in the text")

    heads = best["heads"]
    roman = any(r for _, _, _, r in heads)
    numbers = {n for _, n, _, r in heads if not r}
    titled_msds = bool(re.search(r"material\s+safety\s+data\s+sheet", full[:3000], re.I))
    if roman or re.search(r"osha\s*(?:form\s*)?174", full, re.I) or (titled_msds and 16 not in numbers):
        res.flags.add("old_format")
    elif titled_msds:
        res.review.append("titled 'Material Safety Data Sheet': it may be an older format; check for a current SDS")
    if not best["hazards_found"] and "old_format" not in res.flags:
        res.review.append("Section 2 (hazards) not found, so codes and signal word may be unreliable")
    if sum(1 for _, n, _, r in heads if n == 1 and not r) > 1 and sum(1 for _, n, _, r in heads if n == 16) > 1:
        res.flags.add("multi")
        res.review.append("the file may hold more than one SDS; split it so each product has its own file")
    english = re.search(r"identification|hazard|composition|first[- ]aid|safety\s*data\s*sheet", full, re.I)
    if not english:
        res.flags.add("not_english")
        res.review.append("the sheet may not be in English; an English version is usually needed")

    # Review decisions, field by field.
    for name, label in (("product", "Product name"), ("supplier", "Manufacturer/supplier")):
        found = getattr(res, name)
        if found.value is None:
            res.review.append(f"{label}: not found")
        elif found.conf != "high":
            res.review.append(f"{label}: {found.issue or 'found as ' + found.how}; check")
    if res.date.value is None:
        res.review.append("SDS date: " + (res.date.issue or "not found"))
    else:
        if res.date.conf != "high":
            res.review.append(f"SDS date: {res.date.issue}; check")
        if res.date.value > today + dt.timedelta(days=31):
            res.review.append(f"SDS date {res.date.value.isoformat()} is in the future; check")
        if res.date.alt:
            outcome = lambda d: (age_years(d, today) > args.max_age_years, bool(args.cutoff and d < args.cutoff))
            if outcome(res.date.value) != outcome(res.date.alt):
                res.review.append(
                    f"SDS date '{res.date.raw}' could be {res.date.value:%b %d, %Y} or {res.date.alt:%b %d, %Y} "
                    "and the answer changes the age check; read the sheet")
            else:
                res.notes.append(f"date '{res.date.raw}' read as {res.date.value:%B %d, %Y}")
    if "old_format" not in res.flags:
        if res.signal.value is None:
            res.review.append("Signal word: " + (res.signal.issue or "not found"))
        elif res.signal.conf != "high":
            res.review.append(f"Signal word: {res.signal.how}; check")
        if res.hcodes.how == "matched from statement wording":
            res.review.append("H-codes: not printed on the sheet; matched from the statement wording; check Section 2")
        elif res.hcodes.issue:
            res.review.append(f"H-codes: {res.hcodes.issue}; check")
        if res.signal.value in ("Danger", "Warning") and not res.hcodes.value:
            res.review.append("H-codes: the sheet has a signal word but no hazard statements were found; check Section 2")
        if res.hcodes.value and res.signal.value == "None":
            res.review.append("Signal word says none but hazard codes were found; check Section 2")
    return res


def age_years(day: dt.date, today: dt.date) -> float:
    return (today - day).days / 365.25


# ---------------------------------------------------------------------------
# Manual entries: details a person read off the sheet (the PDF is not changed)
# ---------------------------------------------------------------------------
MANUAL_COLUMNS = {
    "file": ["sds file", "file", "file name", "pdf"],
    "field": ["field", "what"],
    "value": ["value", "correct value"],
    "note": ["note", "notes", "checked by", "comment"],
}
MANUAL_FIELDS = {
    "product": "product", "product name": "product", "manufacturer": "supplier", "supplier": "supplier",
    "manufacturer / supplier": "supplier", "date": "date", "sds date": "date", "revision date": "date",
    "issue date": "date", "signal": "signal", "signal word": "signal", "codes": "hcodes", "h-codes": "hcodes",
    "hazard codes": "hcodes", "hazard statement codes": "hcodes", "pictograms": "pictos", "version": "version",
    "reviewed": "reviewed", "checked": "reviewed",
}
REVIEW_PREFIXES = {"product": ("Product name",), "supplier": ("Manufacturer/supplier",), "date": ("SDS date",),
                   "signal": ("Signal word",), "hcodes": ("H-codes", "Signal word says none"), "pictos": (),
                   "version": ()}


def apply_manual(results, path, args, today) -> list[str]:
    rows, _ = kitlib.read_table(path, MANUAL_COLUMNS, required=("file", "field"))
    by_rel = {r.rel.lower(): r for r in results}
    by_name: dict[str, list] = {}
    for r in results:
        by_name.setdefault(Path(r.rel).name.lower(), []).append(r)
    problems = []
    for row in rows:
        key = row["file"].strip().replace("\\", "/").lower()
        r = by_rel.get(key) or by_rel.get(key + ".pdf")
        if r is None:
            names = by_name.get(Path(key).name, []) or by_name.get(Path(key).name + ".pdf", [])
            r = names[0] if len(names) == 1 else None
        where = f"{Path(path).name} row {row['_row']}"
        if r is None:
            problems.append(f"{where}: no SDS file called '{row['file']}'")
            continue
        name = MANUAL_FIELDS.get(row["field"].strip().lower())
        if name is None:
            problems.append(f"{where}: unknown field '{row['field']}' (use product, manufacturer, date, signal word, "
                            "codes, pictograms, version or reviewed)")
            continue
        value, note = row["value"].strip(), row["note"].strip()
        how = "entered by hand" + (f" ({note})" if note else "")
        if name == "reviewed":
            if value.lower() in ("yes", "y", "true", "1", "done", "ok", "checked"):
                r.checked = note or "yes"
            continue
        if name == "date":
            found = first_date(value, args.date_order, today)
            if not found:
                problems.append(f"{where}: can't read the date '{value}' (use YYYY-MM-DD)")
                continue
            r.date = DateFound(found[0], "high", how, label=r.date.label or "Entered by hand", raw=value,
                               group=r.date.group or 1)
        elif name == "hcodes":
            codes = [] if value.lower() in ("", "none", "n/a") else (find_hcodes([value], 0, 1).value or [])
            r.hcodes = Found(codes, "high", "entered by hand")
        elif name == "pictos":
            codes = sorted({f"GHS0{d}" for d in re.findall(r"GHS\s*0?([1-9])", value, re.I)} |
                           {code for code, rx in PICTO_NAME_RES if rx.search(value)})
            r.pictos = Found(codes, "high", "entered by hand")
        elif name == "signal":
            low = value.lower()
            word = "Danger" if "danger" in low else "Warning" if "warning" in low else "None"
            r.signal = Found(word, "high", how)
        else:
            setattr(r, name, Found(value, "high", how))
        r.manual[name] = note
        r.review = [x for x in r.review if not x.startswith(REVIEW_PREFIXES.get(name, ()) or ("\0",))]
    return problems


# ---------------------------------------------------------------------------
# Site list matching
# ---------------------------------------------------------------------------
SITE_COLUMNS = {
    "product": ["product name (as on label)", "product name", "product", "chemical", "chemical name", "name",
                "trade name", "item", "material", "description"],
    "manufacturer": ["manufacturer / brand", "manufacturer", "supplier", "brand", "company", "maker", "vendor"],
    "location": ["location / area", "location", "area", "room", "work area", "department", "where used",
                 "storage location"],
    "container": ["container size", "container", "size", "package"],
    "quantity": ["quantity", "qty", "amount", "count", "number of containers"],
    "file": ["sds file", "sds file name", "file", "filename", "file name", "pdf"],
    "notes": ["notes", "note", "comments", "remarks"],
    "in_use": ["in use?", "in use", "still used", "active"],
}
STOPWORDS = {"sds", "msds", "safety", "data", "sheet", "the", "and", "of", "for", "w", "with", "us", "usa",
             "en", "english", "ghs", "rev", "version", "pdf", "a", "an"}


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    text = text.replace("&", " and ")
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in STOPWORDS]


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    sa, sb = set(ta), set(tb)
    overlap = len(sa & sb)
    containment = overlap / min(len(sa), len(sb))
    jaccard = overlap / len(sa | sb)
    sequence = difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    return max(sequence, 0.5 * containment + 0.5 * jaccard)


def match_site_list(site_rows, results, folder):
    by_rel = {r.rel.lower(): r for r in results}
    by_name = {}
    for r in results:
        by_name.setdefault(Path(r.rel).name.lower(), []).append(r)
    matches = []
    for row in site_rows:
        wanted = row["file"].strip()
        if wanted:
            key = wanted.replace("\\", "/").lower()
            hit = by_rel.get(key) or by_rel.get(key + ".pdf")
            if hit is None:
                names = by_name.get(Path(key).name, []) or by_name.get(Path(key).name + ".pdf", [])
                hit = names[0] if len(names) == 1 else None
            if hit:
                matches.append((row, hit, 1.0, "named in the site list"))
            else:
                matches.append((row, None, 0.0, f"SDS file named in the site list was not found: {wanted}"))
            continue
        scored = []
        for r in results:
            name_score = similarity(row["product"], str(r.product.value or ""))
            file_score = similarity(row["product"], Path(r.rel).stem)
            s = max(name_score, file_score)
            if row["manufacturer"] and r.supplier.value:
                if similarity(row["manufacturer"], str(r.supplier.value)) >= 0.6:
                    s = min(1.0, s + 0.05)
            scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        if not scored or scored[0][0] < 0.55:
            matches.append((row, None, scored[0][0] if scored else 0.0, "no matching SDS found"))
            continue
        top, hit = scored[0]
        close_second = len(scored) > 1 and scored[1][0] >= 0.55 and top - scored[1][0] < 0.05
        if top >= 0.8 and not close_second:
            matches.append((row, hit, top, "matched by name"))
        else:
            reason = "two sheets match about equally well" if close_second else "possible match"
            matches.append((row, hit, top, f"{reason} (score {top:.2f}); confirm this is the right sheet"))
    return matches


# ---------------------------------------------------------------------------
# Spreadsheet
# ---------------------------------------------------------------------------
INV_HEADERS = [
    ("No.", 5), ("Status", 21), ("Product name (from SDS)", 34), ("Manufacturer / supplier", 28),
    ("SDS date", 11.5), ("Date type", 13), ("Age (years)", 8), ("Older than limit?", 9),
    ("Before update cutoff?", 9), ("Signal word", 10), ("Hazard statement codes", 26), ("Codes source", 15),
    ("Pictograms (from text)", 26), ("SDS version", 8), ("Site list product", 28), ("Location / area", 18),
    ("Container / qty", 14), ("SDS file", 32), ("Pages", 6), ("Needs review", 8), ("Review notes", 60),
    ("Issue", 18), ("Checked by / date", 14),
]
COL = {name: i for i, (name, _) in enumerate(INV_HEADERS)}


def col_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def status_of(issue, review, date, args, today):
    if issue == "MISSING SDS":
        return "MISSING SDS"
    if issue == "OLD MSDS FORMAT":
        return "REPLACE: OLD FORMAT"
    if review:
        return "REVIEW"
    if date and (age_years(date, today) > args.max_age_years or (args.cutoff and date < args.cutoff)):
        return "CHECK FOR NEWER SDS"
    if issue == "NOT ON SITE LIST":
        return "NOT ON SITE LIST"
    return "OK"


def build_rows(results, matches, site_used):
    """One inventory row per site-list product (plus unmatched sheets), or one per sheet."""
    rows = []
    if not site_used:
        for r in sorted(results, key=lambda r: str(r.product.value or r.rel).lower()):
            rows.append({"result": r, "site": None, "match_note": ""})
        return rows
    used = set()
    for site, r, _, note in matches:
        rows.append({"result": r, "site": site, "match_note": note if (r is None or "confirm" in note
                                                                       or "not found" in note) else ""})
        if r is not None:
            used.add(id(r))
    for r in sorted((r for r in results if id(r) not in used), key=lambda r: str(r.product.value or r.rel).lower()):
        rows.append({"result": r, "site": None, "match_note": "not on the site list; ask the client whether "
                                                                "this product is still used"})
    return rows


def write_inventory(workbook, f, rows, args, today, client: str):
    ws = workbook.get_worksheet_by_name("Inventory")
    settings = workbook.get_worksheet_by_name("Settings")

    # Settings sheet: the status formulas read these three cells.
    settings.hide_gridlines(2)
    settings.set_column(0, 0, 34)
    settings.set_column(1, 1, 16)
    settings.set_column(2, 2, 90)
    settings.write(0, 0, "Settings used by the status formulas", f["title"])
    settings.write(2, 0, "Age limit (years)", f["label"])
    settings.write_number(2, 1, args.max_age_years, f["input"])
    settings.write(2, 2, "Sheets older than this are flagged 'CHECK FOR NEWER SDS'. OSHA sets no expiry date for "
                         "safety data sheets; this only prompts a check for a newer version.", f["note"])
    settings.write(3, 0, "Update cutoff date", f["label"])
    if args.cutoff:
        settings.write_datetime(3, 1, dt.datetime.combine(args.cutoff, dt.time()), f["input_date"])
    else:
        settings.write_blank(3, 1, None, f["input_date"])
    settings.write(3, 2, "Sheets dated before this are flagged too. Default: 2024-07-19, when OSHA's 2024 Hazard "
                         "Communication update took effect. Clear the cell to turn this check off.", f["note"])
    settings.write(4, 0, "Check ages as of", f["label"])
    if args.as_of_fixed:
        settings.write_datetime(4, 1, dt.datetime.combine(today, dt.time()), f["input_date"])
    else:
        # The cached result of a date formula must be Excel's date serial number.
        settings.write_formula(4, 1, "=TODAY()", f["input_date"], (today - dt.date(1899, 12, 30)).days)
    settings.write_string(4, 2, "The formula =TODAY() keeps ages current each time the file is opened. Type a date "
                                "to freeze them.", f["note"])
    settings.write(6, 0, "Client / site", f["label"])
    settings.write(6, 1, client or "", f["wrap"])
    settings.write(7, 0, "Created", f["label"])
    settings.write(7, 1, dt.datetime.now().strftime("%Y-%m-%d %H:%M"), f["wrap"])

    for col, (name, width) in enumerate(INV_HEADERS):
        ws.write(0, col, name, f["header"])
        ws.set_column(col, col, width)
    ws.set_row(0, 42)
    c = {name: col_letter(i) for name, i in COL.items()}
    counts: dict[str, int] = {}
    listing = []
    for n, entry in enumerate(rows, start=1):
        r, site = entry["result"], entry["site"]
        row = n
        excel_row = row + 1
        review = list(r.review) if r else []
        if entry["match_note"] and r is not None and "ask the client" not in entry["match_note"]:
            review.insert(0, "Site list match: " + entry["match_note"])
        if r is not None and r.checked:
            review = []
        issue = ""
        if r is None:
            issue = "MISSING SDS"
        elif "old_format" in r.flags:
            issue = "OLD MSDS FORMAT"
        elif site is None and args.site_list:
            issue = "NOT ON SITE LIST"
        notes = list(r.notes) if r else []
        if r is None:
            notes = [entry["match_note"] or "no SDS file found for this product"]
        elif r.manual or r.checked:
            friendly = {"product": "product name", "supplier": "manufacturer", "date": "date", "signal": "signal word",
                        "hcodes": "codes", "pictos": "pictograms", "version": "version"}
            done = ", ".join(friendly.get(k, k) for k in sorted(r.manual))
            notes.insert(0, "Checked by hand" + (f" ({r.checked})" if r.checked not in ("", "yes") else "") +
                         (f"; entered by hand: {done}" if done else ""))
        if r is not None and "old_format" in r.flags:
            review.insert(0, "old MSDS format (not the 16-section SDS); request the current SDS from the manufacturer")
        if issue == "NOT ON SITE LIST":
            notes.insert(0, entry["match_note"])
        needs_review = bool(review) and r is not None
        date = r.date.value if r else None
        status = status_of(issue, needs_review, date, args, today)
        counts[status] = counts.get(status, 0) + 1
        if issue != "NOT ON SITE LIST":
            listing.append({"row": excel_row,
                            "product": (r.product.value if r and r.product.value else (site or {}).get("product", "")),
                            "supplier": (r.supplier.value or "") if r else (site or {}).get("manufacturer", ""),
                            "location": (site or {}).get("location", ""), "date": date, "file": bool(r)})

        def put(name, value, fmt=None, uncertain=False, missing=False, comment=None, manual=None):
            col = COL[name]
            if manual is not None:
                fmt, comment = f["checked"], "Entered by hand" + (f": {manual}" if manual else "")
                uncertain = missing = False
            if missing:
                fmt = f["missing"]
            elif uncertain:
                fmt = f["uncertain"]
            ws.write(row, col, value if value is not None else "", fmt or f["text"])
            if comment:
                ws.write_comment(row, col, comment, {"x_scale": 2, "y_scale": 1.4})

        put("No.", n, f["int"])
        status_formula = (
            f'=IF({c["Issue"]}{excel_row}="MISSING SDS","MISSING SDS",'
            f'IF({c["Issue"]}{excel_row}="OLD MSDS FORMAT","REPLACE: OLD FORMAT",'
            f'IF({c["Needs review"]}{excel_row}="YES","REVIEW",'
            f'IF(OR({c["Older than limit?"]}{excel_row}="YES",{c["Before update cutoff?"]}{excel_row}="YES"),'
            f'"CHECK FOR NEWER SDS",IF({c["Issue"]}{excel_row}="NOT ON SITE LIST","NOT ON SITE LIST","OK")))))')
        ws.write_formula(row, COL["Status"], status_formula, f["bold"], status)
        if r is not None:
            pc = r.product
            put("Product name (from SDS)", pc.value, uncertain=pc.conf != "high", missing=pc.value is None,
                comment=None if pc.conf == "high" else f"Found as: {pc.how}. {pc.issue}".strip(),
                manual=r.manual.get("product"))
            sc = r.supplier
            put("Manufacturer / supplier", sc.value, uncertain=sc.conf != "high", missing=sc.value is None,
                comment=None if sc.conf == "high" else (f"Found as: {sc.how}. {sc.issue}" if sc.value else
                                                        "Not found on the sheet"), manual=r.manual.get("supplier"))
            dc = r.date
            date_uncertain = dc.value is not None and (dc.conf != "high" or any(x.startswith("SDS date") for x in review))
            if dc.value and "date" in r.manual:
                ws.write_datetime(row, COL["SDS date"], dt.datetime.combine(dc.value, dt.time()), f["checked_date"])
                ws.write_comment(row, COL["SDS date"], "Entered by hand" + (f": {r.manual['date']}" if r.manual["date"]
                                                                            else ""))
            elif dc.value:
                ws.write_datetime(row, COL["SDS date"], dt.datetime.combine(dc.value, dt.time()),
                                  f["uncertain_date"] if date_uncertain else f["date"])
                if date_uncertain:
                    ws.write_comment(row, COL["SDS date"], f"Read from '{dc.raw}' ({dc.how}). {dc.issue}".strip(),
                                     {"x_scale": 2, "y_scale": 1.4})
            else:
                put("SDS date", "", missing=True, comment=dc.issue or "No date found")
            put("Date type", dc.label)
            sg = r.signal
            signal_uncertain = sg.value is not None and sg.conf != "high"
            put("Signal word", sg.value if sg.value is not None else "",
                uncertain=signal_uncertain, missing=sg.value is None and "old_format" not in r.flags,
                comment=(f"{sg.how}. {sg.issue}".strip() if (sg.value is None or sg.conf != "high") else None),
                manual=r.manual.get("signal"))
            hc = r.hcodes
            codes_text = ", ".join(hc.value or [])
            source = {"printed": "Printed on SDS", "matched from statement wording": "From wording (verify)",
                      "none found": "None found", "entered by hand": "Entered by hand"}.get(hc.how, hc.how)
            if r.checked and hc.how == "matched from statement wording":
                source = "From wording (checked)"
            put("Hazard statement codes", codes_text, uncertain=(hc.how == "matched from statement wording" or
                bool(hc.issue)) and not r.checked, manual=r.manual.get("hcodes"))
            put("Codes source", source)
            pic = r.pictos
            if pic.value:
                put("Pictograms (from text)", "; ".join(f"{code} {PICTOGRAMS[code]}" for code in pic.value),
                    manual=r.manual.get("pictos"))
            elif pic.how == "none stated":
                put("Pictograms (from text)", "None (stated on the sheet)")
            else:
                put("Pictograms (from text)", "Not named in text - check the sheet", f["muted"])
            put("SDS version", r.version.value or "", f["center"])
            put("SDS file", r.rel, f["text"])
            put("Pages", r.pages, f["int"])
        else:
            for name in ("Product name (from SDS)", "Date type", "Signal word", "Hazard statement codes",
                         "Codes source", "Pictograms (from text)", "SDS version", "SDS file", "Pages"):
                put(name, "")
            put("Manufacturer / supplier", (site or {}).get("manufacturer", ""), f["muted"])
            put("SDS date", "")
        if site is not None:
            put("Site list product", site["product"])
            put("Location / area", site["location"])
            qty = " x ".join(x for x in (site["quantity"], site["container"]) if x)
            put("Container / qty", qty)
        else:
            for name in ("Site list product", "Location / area", "Container / qty"):
                put(name, "")
        put("Needs review", "YES" if needs_review else "", f["center"])
        put("Review notes", "; ".join(review + notes))
        put("Issue", issue)
        put("Checked by / date", "", f["input"])

        e = c["SDS date"] + str(excel_row)
        age = round(age_years(date, today), 1) if date else ""
        ws.write_formula(row, COL["Age (years)"],
                         f'=IF(ISNUMBER({e}),ROUND((Settings!$B$5-{e})/365.25,1),"")', f["num1"], age)
        older = ("YES" if age_years(date, today) > args.max_age_years else "no") if date else ""
        ws.write_formula(row, COL["Older than limit?"],
                         f'=IF(ISNUMBER({e}),IF((Settings!$B$5-{e})/365.25>Settings!$B$3,"YES","no"),"")',
                         f["center"], older)
        before = ("YES" if date < args.cutoff else "no") if (date and args.cutoff) else ""
        ws.write_formula(row, COL["Before update cutoff?"],
                         f'=IF(AND(ISNUMBER({e}),ISNUMBER(Settings!$B$4)),IF({e}<Settings!$B$4,"YES","no"),"")',
                         f["center"], before)

    last = len(rows)
    status_range = (1, COL["Status"], max(last, 1), COL["Status"])
    for value, key in (("OK", "st_ok"), ("REVIEW", "st_review"), ("CHECK FOR NEWER SDS", "st_check"),
                       ("MISSING SDS", "st_bad"), ("REPLACE: OLD FORMAT", "st_bad"), ("NOT ON SITE LIST", "st_info")):
        ws.conditional_format(*status_range, {"type": "cell", "criteria": "==", "value": f'"{value}"',
                                              "format": f[key]})
    for name in ("Older than limit?", "Before update cutoff?", "Needs review"):
        ws.conditional_format(1, COL[name], max(last, 1), COL[name],
                              {"type": "cell", "criteria": "==", "value": '"YES"', "format": f["st_check"]})
    ws.freeze_panes(1, 3)
    ws.autofilter(0, 0, max(last, 1), len(INV_HEADERS) - 1)
    ws.set_landscape()
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(0)
    return counts, listing


def write_chemical_list(workbook, f, listing, client):
    """A plain, printable list for the employer's written programme. Each cell
    reads from the Inventory sheet, so corrections there flow through."""
    sheet = workbook.get_worksheet_by_name("Chemical List")
    sheet.hide_gridlines(2)
    widths = [5, 42, 32, 24, 12, 11]
    for col, width in enumerate(widths):
        sheet.set_column(col, col, width)
    sheet.write(0, 0, "Hazardous chemical list", f["title"])
    sheet.write(1, 0, client or "", f["subtitle"])
    sheet.write(2, 0, "Confirmed by the employer: ______________________________     Date: ______________", f["label"])
    headers = ["No.", "Product name", "Manufacturer / supplier", "Location / area", "SDS date", "SDS on file"]
    for col, name in enumerate(headers):
        sheet.write(4, col, name, f["header"])
    inv = {name: col_letter(i) for name, i in COL.items()}
    for n, item in enumerate(listing, start=1):
        row, src = 4 + n, item["row"]
        sheet.write_number(row, 0, n, f["int"])
        sheet.write_formula(row, 1, f'=IF(Inventory!{inv["Product name (from SDS)"]}{src}<>"",'
                                    f'Inventory!{inv["Product name (from SDS)"]}{src},'
                                    f'Inventory!{inv["Site list product"]}{src}&"")', f["text"], item["product"] or "")
        sheet.write_formula(row, 2, f'=Inventory!{inv["Manufacturer / supplier"]}{src}&""', f["text"], item["supplier"])
        sheet.write_formula(row, 3, f'=Inventory!{inv["Location / area"]}{src}&""', f["text"], item["location"])
        cached = (item["date"] - dt.date(1899, 12, 30)).days if item["date"] else ""
        sheet.write_formula(row, 4, f'=IF(ISNUMBER(Inventory!{inv["SDS date"]}{src}),Inventory!{inv["SDS date"]}{src},"")',
                            f["date"], cached)
        sheet.write_formula(row, 5, f'=IF(Inventory!{inv["SDS file"]}{src}="","MISSING","Yes")', f["center"],
                            "Yes" if item["file"] else "MISSING")
    last = 4 + len(listing)
    sheet.conditional_format(5, 5, max(last, 5), 5, {"type": "cell", "criteria": "==", "value": '"MISSING"',
                                                     "format": f["st_bad"]})
    sheet.write(last + 2, 0, "Product names and dates are as printed on each safety data sheet. Sheets are kept in "
                             "the SDS binder.", f["subtitle"])
    sheet.freeze_panes(5, 0)
    sheet.repeat_rows(4)
    sheet.fit_to_pages(1, 0)
    sheet.set_paper(1)
    sheet.print_area(0, 0, last + 2, len(headers) - 1)


def write_binder_index(workbook, f, rows, group_by: str):
    sheet = workbook.get_worksheet_by_name("Binder Index")
    headers = [("Section", 26), ("Title", 44), ("File", 36), ("Order", 7), ("Notes", 60), ("Include", 9)]
    for col, (name, width) in enumerate(headers):
        sheet.write(0, col, name, f["header"])
        sheet.set_column(col, col, width)
    entries, seen = [], {}
    for entry in rows:
        r, site = entry["result"], entry["site"]
        location = (site or {}).get("location", "") if site else ""
        if r is not None and id(r) in seen:
            if location and location not in seen[id(r)]["locations"]:
                seen[id(r)]["locations"].append(location)
            continue
        if r is None:
            title = site["product"]
            note_bits = [site["manufacturer"]] if site["manufacturer"] else []
            note_bits.append("SDS requested - not yet received")
            item = {"title": title, "file": "", "notes": note_bits, "locations": [location] if location else [],
                    "include": "yes", "other": False}
        else:
            title = r.product.value if (r.product.conf == "high" or site is None) else site["product"]
            bits = []
            if r.supplier.value:
                bits.append(str(r.supplier.value))
            if r.date.value:
                word = "Revised" if r.date.group == 1 else "Dated"
                bits.append(f"{word} {kitlib.short_date(r.date.value)}")
            not_on_list = site is None and entry["match_note"].startswith("not on the site list")
            item = {"title": title, "file": r.rel, "notes": bits, "locations": [location] if location else [],
                    "include": "no" if not_on_list else "yes", "other": not_on_list}
            seen[id(r)] = item
        entries.append(item)

    def section_for(item):
        if item["other"]:
            return "Not on site list"
        if group_by == "location" and item["locations"]:
            return item["locations"][0]
        return "Safety Data Sheets"

    order_sections = []
    for item in entries:
        name = section_for(item)
        if name not in order_sections:
            order_sections.append(name)
    if "Not on site list" in order_sections:
        order_sections.remove("Not on site list")
        order_sections.append("Not on site list")
    row, order = 1, 1
    for name in order_sections:
        members = sorted((i for i in entries if section_for(i) == name), key=lambda i: str(i["title"]).lower())
        for item in members:
            notes = list(item["notes"])
            if group_by != "location" and item["locations"]:
                notes.append("Location: " + ", ".join(item["locations"]))
            elif len(item["locations"]) > 1:
                notes.append("Also used in: " + ", ".join(item["locations"][1:]))
            sheet.write(row, 0, name, f["text"])
            sheet.write(row, 1, item["title"], f["text"])
            sheet.write(row, 2, item["file"], f["text"])
            sheet.write_number(row, 3, order, f["int"])
            sheet.write(row, 4, " · ".join(notes), f["text"])
            sheet.write(row, 5, item["include"], f["center"])
            row += 1
            order += 1
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(row - 1, 1), len(headers) - 1)
    return row - 1


def write_summary(workbook, f, counts, total, client, args, today):
    sheet = workbook.get_worksheet_by_name("Summary")
    sheet.hide_gridlines(2)
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 1, 12)
    sheet.set_column(2, 2, 80)
    sheet.write(0, 0, "Chemical inventory summary", f["title"])
    sheet.write(1, 0, client or "", f["subtitle"])
    explain = {
        "OK": "Sheet found, details read clearly, not older than the limit.",
        "CHECK FOR NEWER SDS": "Older than the age limit or dated before the update cutoff. Look for a newer "
                               "version on the manufacturer's website.",
        "REVIEW": "Something was unclear. Open the PDF and check the highlighted cells.",
        "MISSING SDS": "On the site list but no sheet was found. Get the current SDS.",
        "REPLACE: OLD FORMAT": "An old-style MSDS. Get the current 16-section SDS.",
        "NOT ON SITE LIST": "A sheet was supplied but the product is not on the client's list. Ask the client.",
    }
    sheet.write(3, 0, "Status", f["header"])
    sheet.write(3, 1, "Count", f["header"])
    sheet.write(3, 2, "What to do", f["header"])
    row = 4
    for status, text in explain.items():
        sheet.write(row, 0, status, f["bold"])
        sheet.write_formula(row, 1, f'=COUNTIF(Inventory!$B:$B,"{status}")', f["int"], counts.get(status, 0))
        sheet.write(row, 2, text, f["text"])
        row += 1
    sheet.write(row, 0, "Total rows", f["bold"])
    sheet.write_formula(row, 1, f"=SUM(B5:B{row})", f["int"], total)
    for value, key in (("OK", "st_ok"), ("REVIEW", "st_review"), ("CHECK FOR NEWER SDS", "st_check"),
                       ("MISSING SDS", "st_bad"), ("REPLACE: OLD FORMAT", "st_bad"), ("NOT ON SITE LIST", "st_info")):
        sheet.conditional_format(4, 0, row - 1, 0, {"type": "cell", "criteria": "==", "value": f'"{value}"',
                                                    "format": f[key]})
    row += 2
    sheet.write(row, 0, "Checked as of", f["label"])
    sheet.write(row, 1, today.isoformat())
    sheet.write(row + 1, 0, "Age limit (years)", f["label"])
    sheet.write(row + 1, 1, args.max_age_years)
    sheet.write(row + 2, 0, "Update cutoff date", f["label"])
    sheet.write(row + 2, 1, args.cutoff.isoformat() if args.cutoff else "off")


READ_ME = [
    "This workbook lists what each safety data sheet (SDS) says. It is not a hazard assessment and it does not "
    "classify any chemical. Nothing in the PDFs was changed.",
    "## How to use it",
    "1. Open the Inventory sheet and filter the Status column.",
    "2. REVIEW rows: open the PDF named in 'SDS file' and check every highlighted cell. Amber = the script was "
    "unsure. Red = not found. Hover over a cell with a red corner to see why. Fix the cell, then clear "
    "'Needs review' (the status updates by itself) and put your initials in 'Checked by / date'.",
    "3. CHECK FOR NEWER SDS rows: look for a newer sheet on the manufacturer's or supplier's website and "
    "replace the PDF. Then run extract_sds.py again.",
    "4. MISSING SDS rows: get the current SDS from the manufacturer, supplier or distributor.",
    "5. REPLACE: OLD FORMAT rows: the file is an old-style MSDS. Get the current 16-section SDS.",
    "6. NOT ON SITE LIST rows: ask the client whether the product is still used on site.",
    "7. Send the finished list to the client to confirm. The client confirms the on-site list; you don't. The "
    "'Chemical List' sheet is a plain printable version (it reads from the Inventory sheet).",
    "8. Check the 'Binder Index' sheet (titles, sections, include = yes/no), then build the binder with "
    "build_binder.py --sheet \"Binder Index\".",
    "## Columns",
    "Hazard statement codes come from Section 2 only (codes in Section 3 belong to individual ingredients). "
    "'From wording (verify)' means the sheet printed the statements without codes and the codes were matched from "
    "the standard wording.",
    "Pictograms are listed only when the sheet names them in text. Most sheets show them as images, so "
    "'Not named in text' is normal: look at the sheet.",
    "Age, 'Older than limit?', 'Before update cutoff?' and Status are formulas that read the Settings sheet.",
    "## Rules",
    "Never edit or 'correct' a safety data sheet. If a sheet looks wrong, ask the manufacturer for a corrected one.",
    "Don't classify chemicals or give safety advice. Hazard questions go to the sheet, the manufacturer or the "
    "employer's safety adviser. A qualified person trains staff.",
    "OSHA sets the compliance dates for its revised Hazard Communication Standard. Check the current dates on "
    "osha.gov (the employer date is reported as 20 November 2026 for single-substance chemicals).",
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read SDS PDFs and build inventory.xlsx (plus a Binder Index for build_binder.py).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python scripts/extract_sds.py --sds-folder sds --site-list site-list.xlsx "
               "--out inventory.xlsx --group-by location")
    parser.add_argument("--sds-folder", required=True, help="folder with the SDS PDF files")
    parser.add_argument("--out", required=True, help="inventory spreadsheet to create (.xlsx)")
    parser.add_argument("--site-list", help="client's on-site chemical list (.xlsx or .csv)")
    parser.add_argument("--sheet", help="sheet name in the site list (default: first sheet with a product column)")
    parser.add_argument("--manual", help="details you read off sheets yourself (.csv or .xlsx; see "
                                         "templates/sds-manual-entries-template.csv); applied on every run")
    parser.add_argument("--max-age-years", type=float, default=3.0,
                        help="flag sheets older than this many years (default 3)")
    parser.add_argument("--update-cutoff", default=DEFAULT_CUTOFF,
                        help="flag sheets dated before this date, YYYY-MM-DD, or 'none' (default %(default)s)")
    parser.add_argument("--date-order", choices=["MDY", "DMY"], default="MDY",
                        help="how to read dates like 03/05/2024 when the sheet doesn't make it clear (default MDY)")
    parser.add_argument("--group-by", choices=["none", "location"], default="none",
                        help="binder sections: one section, or one per site-list location")
    parser.add_argument("--client", default="", help="client and site name for the spreadsheet")
    parser.add_argument("--as-of", help="check ages as of this date (YYYY-MM-DD) instead of today")
    parser.add_argument("--recursive", action="store_true", help="also read PDFs in subfolders")
    args = parser.parse_args(argv)

    try:
        today = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
        args.as_of_fixed = bool(args.as_of)
        args.cutoff = None if args.update_cutoff.lower() in ("none", "off", "") else \
            dt.date.fromisoformat(args.update_cutoff)
    except ValueError as exc:
        print(f"Error: dates must look like 2024-07-19 ({exc})", file=sys.stderr)
        return 1
    folder = Path(args.sds_folder)
    if not folder.is_dir():
        print(f"Error: folder not found: {folder}", file=sys.stderr)
        return 1
    out = Path(args.out)
    if out.suffix.lower() != ".xlsx":
        print("Error: --out must end in .xlsx", file=sys.stderr)
        return 1
    pattern = "**/*" if args.recursive else "*"
    files = sorted(p for p in folder.glob(pattern) if p.is_file())
    pdfs = [p for p in files if p.suffix.lower() == ".pdf"]
    others = [p for p in files if p.suffix.lower() not in (".pdf",) and not p.name.startswith(".")]
    if not pdfs:
        print(f"Error: no PDF files in {folder}", file=sys.stderr)
        return 1
    if pdfplumber is None:
        print("Note: pdfplumber is not installed; using pypdf only. Install it for better results.")

    site_rows = []
    if args.site_list:
        try:
            site_rows, _ = kitlib.read_table(args.site_list, SITE_COLUMNS, required=("product",), sheet=args.sheet)
        except KitError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        site_rows = [r for r in site_rows if r["product"] and
                     r["in_use"].strip().lower() not in ("no", "n", "false", "0")]

    results = []
    for number, path in enumerate(pdfs, start=1):
        print(f"Reading {number}/{len(pdfs)}: {path.name}")
        results.append(analyse(path, folder, args, today))
    if args.manual:
        try:
            problems = apply_manual(results, args.manual, args, today)
        except KitError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        for problem in problems:
            print(f"Warning: {problem}")

    matches = match_site_list(site_rows, results, folder) if site_rows else []
    rows = build_rows(results, matches, bool(site_rows))
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        workbook = xlsxwriter.Workbook(str(out), kitlib.XLSX_OPTIONS)
        f = kitlib.xlsx_formats(workbook)
        for name in ("Inventory", "Chemical List", "Binder Index", "Summary", "Settings"):
            workbook.add_worksheet(name)
        counts, listing = write_inventory(workbook, f, rows, args, today, args.client)
        write_chemical_list(workbook, f, listing, args.client)
        index_rows = write_binder_index(workbook, f, rows, args.group_by)
        write_summary(workbook, f, counts, len(rows), args.client, args, today)
        kitlib.write_readme_sheet(workbook, f, "How to check this inventory", READ_ME)
        workbook.close()
    except PermissionError:
        print(f"Error: could not write {out}. Close it in Excel and run again.", file=sys.stderr)
        return 1

    print()
    print(f"Inventory written: {out}  ({len(rows)} rows, {index_rows} binder index rows)")
    for status in ("OK", "CHECK FOR NEWER SDS", "REVIEW", "MISSING SDS", "REPLACE: OLD FORMAT", "NOT ON SITE LIST"):
        if counts.get(status):
            print(f"  {status:<22} {counts[status]}")
    if others:
        print(f"Skipped {len(others)} non-PDF file(s): " + ", ".join(p.name for p in others[:6]))
    print("Next: open the Inventory sheet, check every REVIEW row against its PDF, then build the binder.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
