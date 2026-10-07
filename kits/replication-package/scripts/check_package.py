#!/usr/bin/env python3
"""First-pass check of a research replication package.

Scans a package folder and writes a findings report in two formats:
check_report.md (to read or send) and check_report.xlsx (to track fixes).
Every finding has a severity and a suggested fix.

The checker only reads files. It never changes the package. It never reads
or prints data values: for CSV and TSV files it reads the header row only.

Usage:
    python check_package.py PATH/TO/PACKAGE
    python check_package.py PATH/TO/PACKAGE --out reports/smith-2026

Options:
    --out DIR        Folder for the report. Default: <package name>_check_report
                     in the current folder.
    --large-mb N     Flag files larger than N megabytes (default 100).
    --csv-max-mb N   Read headers of CSV/TSV files up to N megabytes (default 50).

Severity levels:
    High    Likely to stop the code running, or to fail the journal's code check
    Medium  The data editor will probably ask for a change
    Low     Good practice, quick to fix
    Info    For your information

The checks use text patterns. They can miss problems and can flag things
that are fine, so a person must review every finding.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

VERSION = "1.0"

SEVERITIES = ["High", "Medium", "Low", "Info"]
SEVERITY_MEANING = {
    "High": "Likely to stop the code running, or to fail the journal's code check",
    "Medium": "The data editor will probably ask for a change",
    "Low": "Good practice, quick to fix",
    "Info": "For your information",
}
CATEGORIES = ["README", "Master script", "Paths", "Dependencies", "Data files",
              "Outputs", "Personal data", "Large files", "Randomness", "Logs", "Housekeeping"]

LANG_BY_EXT = {
    ".py": "Python", ".ipynb": "Python",
    ".r": "R", ".rmd": "R", ".qmd": "R",
    ".do": "Stata", ".ado": "Stata",
    ".m": "MATLAB",
    ".sas": "SAS",
    ".sh": "Shell",
}
CHECKED_LANGS = ["R", "Stata", "Python", "MATLAB", "SAS", "Shell"]

# Folders that are skipped silently.
SKIP_DIRS = {".git", ".svn", ".hg", "node_modules", ".tox", ".mypy_cache",
             ".pytest_cache", ".idea", ".vscode"}
# Folders that should not be in a deposited package.
JUNK_DIRS = {"__pycache__", ".ipynb_checkpoints", "__MACOSX", ".Rproj.user", ".venv"}
JUNK_FILES = {".ds_store", "thumbs.db", "desktop.ini", ".rhistory", ".rapp.history"}
# Third-party code saved inside the package: listed, but not scanned.
VENDORED_DIRS = {"ado", "renv", "packrat", "site-packages"}

DATA_EXTS = {".csv", ".tsv", ".tab", ".dta", ".rds", ".rdata", ".rda", ".xlsx", ".xls",
             ".sav", ".por", ".sas7bdat", ".sas7bcat", ".xpt", ".parquet", ".feather",
             ".arrow", ".json", ".dat", ".zip", ".gz", ".bz2", ".7z", ".mat", ".shp",
             ".gpkg", ".geojson", ".pkl", ".pickle", ".h5", ".hdf5", ".nc", ".fst",
             ".qs", ".dbf", ".ods", ".sqlite", ".db", ".txt"}
OUTPUT_EXTS = {".png", ".pdf", ".eps", ".svg", ".jpg", ".jpeg", ".tif", ".tiff", ".gph",
               ".emf", ".wmf", ".tex", ".csv", ".xlsx", ".xls", ".rtf", ".docx",
               ".html", ".htm", ".txt", ".md"}
OUTPUT_DIR_RE = re.compile(r"^(outputs?|out|results?|tables?|figures?|figs?|graphs?|plots?"
                           r"|charts?|exhibits?|images?|img)$", re.I)
OUTPUT_NAME_RE = re.compile(r"^(table|tab|fig|figure|graph|chart|plot|appendix|app_?table"
                            r"|app_?fig|exhibit)[\s_.-]?[a-z]{0,2}\d", re.I)
NOT_OUTPUT_DIR_RE = re.compile(r"^(data|raw|input|inputs|source|sources|docs?|paper"
                               r"|manuscript|literature|logs?|ado|renv)$", re.I)
DOC_EXTS = {".pdf", ".docx", ".doc", ".odt", ".md", ".txt", ".rst", ".tex", ".html", ".htm"}

TABLE_SEP = " · "


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    severity: str
    category: str
    where: str
    finding: str
    fix: str
    id: str = ""


@dataclass
class FileInfo:
    rel: str            # path relative to the package, with forward slashes
    path: Path
    size: int
    ext: str
    lang: str | None
    vendored: bool


@dataclass
class Source:
    info: FileInfo
    lang: str
    rows: list          # (line label, code part, comment part)

    @property
    def code_text(self) -> str:
        return "\n".join(code for _, code, _ in self.rows)


# ---------------------------------------------------------------------------
# Reading files
# ---------------------------------------------------------------------------
def walk_package(root: Path):
    """Return (files, junk): every file in the package, and stray system files."""
    files, junk = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel_dir = here.relative_to(root)
        keep = []
        for d in sorted(dirnames):
            if d in SKIP_DIRS:
                continue
            is_venv = (here / d / "pyvenv.cfg").exists()
            if d in JUNK_DIRS or is_venv:
                junk.append((rel_dir / d).as_posix() + "/")
                continue
            keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            rel = (rel_dir / name).as_posix()
            low = name.lower()
            if (low in JUNK_FILES or name.startswith("~$") or name.startswith(".~lock.")
                    or low.endswith((".pyc", ".swp")) or name.endswith("~")):
                junk.append(rel)
                continue
            path = here / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            ext = path.suffix.lower()
            parts = {p.lower() for p in Path(rel).parts[:-1]}
            vendored = bool(parts & VENDORED_DIRS)
            files.append(FileInfo(rel, path, size, ext, LANG_BY_EXT.get(ext), vendored))
    return files, junk


def read_text(path: Path, limit_mb: float = 20) -> str | None:
    try:
        if path.stat().st_size > limit_mb * 1024 * 1024:
            return None
        return path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return None


def numbered_lines(info: FileInfo, text: str):
    """Return (label, line) pairs. Notebooks give 'cell N, line M' labels."""
    if info.ext == ".ipynb":
        try:
            nb = json.loads(text)
        except ValueError:
            return []
        out = []
        for i, cell in enumerate(nb.get("cells", []), 1):
            if cell.get("cell_type") != "code":
                continue
            src = cell.get("source", "")
            if isinstance(src, list):
                src = "".join(src)
            for j, line in enumerate(src.splitlines(), 1):
                out.append((f"cell {i}, line {j}", line))
        return out
    return [(str(n), line) for n, line in enumerate(text.splitlines(), 1)]


def split_comments(lines, lang: str):
    """Split each line into its code part and its comment part.

    A simple scanner, good enough for finding paths and commands. Text inside
    quotes stays in the code part, so quoted paths are kept. Python docstrings
    and other triple-quoted text count as comments, since they usually hold
    explanations and examples rather than paths the code uses.
    """
    out = []
    block = False          # inside /* */ (Stata, SAS) or %{ %} (MATLAB)
    sas_star = False       # inside a SAS "* ... ;" comment
    triple = None          # inside a Python triple-quoted string: its delimiter
    for label, line in lines:
        stripped = line.strip()
        if lang == "MATLAB":
            if block:
                if stripped == "%}":
                    block = False
                out.append((label, "", line))
                continue
            if stripped == "%{":
                block = True
                out.append((label, "", line))
                continue
        if lang == "SAS" and sas_star:
            if ";" in line:
                sas_star = False
            out.append((label, "", line))
            continue
        if not block and lang in ("Stata", "SAS") and stripped.startswith("*"):
            if lang == "SAS" and ";" not in line:
                sas_star = True
            out.append((label, "", line))
            continue
        code, comment = [], []
        quote = None
        i, n = 0, len(line)
        while i < n:
            ch = line[i]
            if triple:
                end = line.find(triple, i)
                if end == -1:
                    comment.append(line[i:])
                    break
                comment.append(line[i:end + 3])
                i = end + 3
                triple = None
                continue
            if lang == "Python" and not quote and line.startswith(('"""', "'''"), i):
                triple = line[i:i + 3]
                comment.append(triple)
                i += 3
                continue
            if block:
                end = line.find("*/", i)
                if end == -1:
                    comment.append(line[i:])
                    break
                comment.append(line[i:end + 2])
                i = end + 2
                block = False
                continue
            if quote:
                code.append(ch)
                if ch == "\\" and lang in ("Python", "R", "Shell") and i + 1 < n:
                    code.append(line[i + 1])
                    i += 2
                    continue
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in "\"'":
                if lang == "Stata" and ch == "'":       # closes a local macro
                    code.append(ch)
                    i += 1
                    continue
                if lang == "MATLAB" and ch == "'":
                    prev = "".join(code).rstrip()[-1:]
                    if prev and (prev.isalnum() or prev in ")]}._'"):   # transpose
                        code.append(ch)
                        i += 1
                        continue
                quote = ch
                code.append(ch)
                i += 1
                continue
            if lang in ("Python", "R", "Shell") and ch == "#":
                comment.append(line[i:])
                break
            if lang == "MATLAB" and (ch == "%" or line.startswith("...", i)):
                comment.append(line[i:])
                break
            if lang in ("Stata", "SAS") and line.startswith("/*", i):
                block = True
                comment.append("/*")
                i += 2
                continue
            if lang == "Stata" and line.startswith("//", i) and (i == 0 or line[i - 1] in " \t"):
                comment.append(line[i:])
                break
            code.append(ch)
            i += 1
        out.append((label, "".join(code), "".join(comment)))
    return out


def load_sources(files):
    sources = []
    for f in files:
        if not f.lang or f.vendored:
            continue
        text = read_text(f.path)
        if text is None:
            continue
        sources.append(Source(f, f.lang, split_comments(numbered_lines(f, text), f.lang)))
    return sources


def document_text(path: Path) -> str | None:
    """Plain text of a README in .md/.txt/.docx/.odt/.pdf form (None if unreadable)."""
    ext = path.suffix.lower()
    try:
        if ext in (".docx", ".odt"):
            member = "word/document.xml" if ext == ".docx" else "content.xml"
            with zipfile.ZipFile(path) as z:
                xml = z.read(member).decode("utf-8", errors="replace")
            xml = re.sub(r"</(w:p|text:p|text:h)>", "\n", xml)
            return re.sub(r"<[^>]+>", "", xml)
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                return None
            reader = PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages[:80])
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None
    except Exception:  # damaged PDF and similar
        return None
    return read_text(path)


def short(text: str, limit: int = 90) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def where(src: Source, label: str) -> str:
    return f"{src.info.rel} (line {label})" if label[0].isdigit() else f"{src.info.rel} ({label})"


# ---------------------------------------------------------------------------
# 1. README
# ---------------------------------------------------------------------------
README_SECTIONS = [
    ("Overview", "Low",
     [r"\boverview\b", r"^#+\s*summary\b", r"\bsummary of the package\b"],
     "Add a short overview: what the package reproduces, which script to run, and roughly how long it takes."),
    ("Data availability and provenance statements", "High",
     [r"data availability", r"availability of (the )?data", r"data (and code )?availability",
      r"provenance", r"\bdata sources?\b"],
     "Add a data availability statement: where each dataset comes from, whether it is included, "
     "and how a replicator can get any data that is not included (cost, wait time, application)."),
    ("Statement about rights (permission to use and share the data)", "Medium",
     [r"\brights?\b", r"\bpermission", r"\blicen[cs]e", r"terms of use", r"redistribut"],
     "State that the authors may use the data and may (or may not) share them, and under which licence or terms."),
    ("Dataset list (each data file, its source, and whether it is provided)", "Medium",
     [r"dataset list", r"list of (data|datasets|data files)", r"\bdata files?\b", r"\bdatasets?\b",
      r"\bdata sets?\b"],
     "Add a table of every data file: name, source, whether it is provided, and its format."),
    ("Computational requirements", "High",
     [r"computational requirements", r"software requirements", r"computing (environment|requirements)",
      r"\brequirements\b"],
     "Add the software and versions used (including packages), the operating system, and hardware."),
    ("Hardware and run time", "Medium",
     [r"run ?time", r"running time", r"\b\d+\s*(hours?|hrs?|minutes?|mins?|seconds?|days?)\b",
      r"\bmemory\b", r"\bram\b", r"\bcores?\b", r"\bstorage\b"],
     "Say how long a full run takes and on what computer (processor, memory, operating system)."),
    ("Description of programs", "Medium",
     [r"description of (the )?(programs|code)", r"\bprograms?\b", r"folder structure",
      r"directory structure", r"\bcode (structure|files)\b"],
     "Describe the programs: what each folder and script does, in the order they run."),
    ("Instructions to replicators", "High",
     [r"\binstructions\b", r"how to (run|replicate|reproduce)", r"to (replicate|reproduce) (the|all|our)",
      r"steps? to (run|replicate|reproduce)"],
     "Add step-by-step instructions: what to install, which single script to run, and where the results appear."),
    ("List of tables and figures with the programs that make them", "High",
     [r"list of (tables|figures|exhibits)", r"tables? and figures?", r"figures? and tables?",
      r"table/figure", r"\bexhibits?\b"],
     "Add a table mapping every table and figure in the paper to the program (and line) that creates it "
     "and the output file name."),
    ("References and data citations", "Medium",
     [r"\breferences\b", r"data citations?", r"\bbibliography\b", r"\bcitations?\b"],
     "Add a References section that cites every dataset (creator, year, title, publisher or repository, "
     "version, DOI or web address)."),
]

VERSION_EXAMPLES = {"Python": "Python 3.11.9", "R": "R 4.4.1", "Stata": "Stata/MP 18.0",
                    "MATLAB": "MATLAB R2024a", "SAS": "SAS 9.4M8"}
VERSION_PATTERNS = {
    "Python": re.compile(r"python\s*(version\s*)?v?\d+(\.\d+)+", re.I),
    "R": re.compile(r"\bR\s*(version\s*)?v?\d+\.\d+"),
    "Stata": re.compile(r"stata\s*(/?\s*(mp|se|be|ic|now)\b)?\s*(version\s*)?\d+", re.I),
    "MATLAB": re.compile(r"matlab\s*(version\s*)?(r?\d{4}[ab]|\d+(\.\d+)?)", re.I),
    "SAS": re.compile(r"\bsas\s*(version\s*|9\.|v?\d)", re.I),
}


def find_readmes(files):
    top = [f for f in files if "/" not in f.rel and f.path.name.lower().startswith("readme")]
    deeper = [f for f in files if "/" in f.rel and f.path.name.lower().startswith("readme")
              and f.rel.count("/") == 1 and not f.vendored]
    return top, deeper


def check_readme(files, langs, report):
    top, deeper = find_readmes(files)
    if not top:
        if deeper:
            report.add("Medium", "README", deeper[0].rel,
                       "The README is not in the top folder of the package.",
                       "Move it to the top folder and call it README (README.md or README.pdf), "
                       "where data editors look first.")
            top = deeper
        else:
            report.add("High", "README", "(package)",
                       "No README file found.",
                       "Write a README using templates/README-template.md. Data editors reject packages without one.")
            return None
    rank = {".md": 0, ".txt": 1, ".rst": 2, "": 3, ".docx": 4, ".odt": 5, ".pdf": 6, ".html": 7, ".tex": 8}
    top.sort(key=lambda f: rank.get(f.ext, 9))
    readme = top[0]
    report.readme = readme.rel
    text = document_text(readme.path)
    if not text or len(text.strip()) < 20:
        report.add("Info", "README", readme.rel,
                   "Could not read the README's text, so its sections were not checked.",
                   "Check the sections by hand against templates/README-template.md "
                   "(for PDF files, installing pypdf lets the checker read them).")
        return None
    lower = text.lower()
    missing = 0
    for title, sev, patterns, fix in README_SECTIONS:
        flags = re.I | re.M
        if not any(re.search(p, text, flags) for p in patterns):
            missing += 1
            report.add(sev, "README", readme.rel, f"Section missing: {title}.", fix)
    for lang in langs:
        pat = VERSION_PATTERNS.get(lang)
        if pat and not pat.search(text):
            report.add("Medium", "README", readme.rel,
                       f"The README does not say which version of {lang} was used.",
                       f"Add the exact version (for example {VERSION_EXAMPLES[lang]}) under Computational "
                       "requirements, and check it with the author.")
    if not re.search(r"doi\.org/|\bdoi:\s*10\.|https?://", lower):
        report.add("Medium", "README", readme.rel,
                   "No data citation found (no DOI or web address in the README).",
                   "Cite each dataset in the References section with a DOI or a stable web address, "
                   "and cite the same datasets in the paper.")
    report.readme_sections_missing = missing
    return text


# ---------------------------------------------------------------------------
# 2. Master script
# ---------------------------------------------------------------------------
MASTER_NAME_RE = re.compile(
    r"^(\d+_?)?(main|master|run_?all|runall|run|run_?everything|make_?all|replicate|replication"
    r"|reproduce|all)\.(py|r|do|m|sas|sh|bat|cmd|ipynb|jl)$", re.I)
MASTER_SPECIAL = {"makefile", "snakefile", "_targets.r", "dvc.yaml", "justfile"}


def check_master(files, sources, report):
    by_name = [f for f in files if not f.vendored and (MASTER_NAME_RE.match(f.path.name)
               or f.path.name.lower() in MASTER_SPECIAL)]
    code_names = {s.info.path.name.lower() for s in sources}
    by_content = []
    for s in sources:
        text = s.code_text.lower()
        called = {n for n in code_names if n != s.info.path.name.lower() and n in text}
        if len(called) >= 2:
            by_content.append(s.info)
    candidates = {f.rel: f for f in by_name + by_content}
    report.master = sorted(candidates)
    if not candidates:
        report.add("High", "Master script", "(package)",
                   "No master script found. Nothing runs the whole package from start to finish.",
                   "Add one master script in the top folder (main.py, main.R or main.do from templates/) "
                   "that runs every program in order and writes a log.")
        return
    top = [r for r in candidates if "/" not in r]
    if not top:
        report.add("Low", "Master script", ", ".join(sorted(candidates)),
                   "The master script is not in the top folder.",
                   "Move it to the top folder, or say clearly in the README which file to run.")
    elif len(top) > 1:
        report.add("Info", "Master script", ", ".join(sorted(top)),
                   "Several files could be the master script.",
                   "Say clearly in the README which single file the replicator should run.")


# ---------------------------------------------------------------------------
# 3. Absolute paths and changes of working folder
# ---------------------------------------------------------------------------
STRONG_ROOTS = ("Users|home|Volumes|mnt|media|gpfs|nfs|lustre|scratch|afs|net|root|private"
                "|content/drive|cygdrive")
WEAK_ROOTS = ("data|project|projects|work|storage|shared|groups|global|research|space|opt|srv|tmp"
              "|workspace|Library|share|users")
STOP = r"[^\s\"'`;,()\[\]{}<>|]*"
WIN_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]:[\\/]{1,2}" + STOP + ")")
UNC_RE = re.compile(r"(?<![A-Za-z0-9_:])(\\{2,}[A-Za-z0-9._$-]+\\{1,2}[A-Za-z0-9._$ -]+" + STOP + ")")
STRONG_RE = re.compile(r"(?<![A-Za-z0-9_.~$/\\})\]:-])(/(?:" + STRONG_ROOTS + r")/" + STOP + ")")
WEAK_RE = re.compile(r"([\"'])(/(?:" + WEAK_ROOTS + r")/" + STOP + ")")
TILDE_RE = re.compile(r"(?<![A-Za-z0-9_.$/\\-])(~[/\\]" + STOP + ")")
SYNCED_RE = re.compile(r"dropbox|onedrive|google ?drive|icloud|box sync|mydrive", re.I)

CHDIR_RE = {
    "R": re.compile(r"\bsetwd\s*\("),
    "Python": re.compile(r"\b(os\.)?chdir\s*\("),
    "Stata": re.compile(r"^\s*((cap|capture|qui|quietly|noi|noisily)\s+)*cd(\s|$)"),
    "MATLAB": re.compile(r"^\s*cd(\s|\(|$)|\bcd\s*\("),
    "SAS": re.compile(r"\bx\s+[\"']cd\s|\bdlgcdir\s*\(|%sysexec\s+cd\b", re.I),
}
ROOT_DEFINITION_RE = {
    "Stata": re.compile(r"^\s*(global|local)\s+\w+"),
    "R": re.compile(r"^\s*[\w.]+\s*(<-|=)"),
    "Python": re.compile(r"^\s*\w+\s*="),
    "MATLAB": re.compile(r"^\s*\w+\s*="),
    "SAS": re.compile(r"^\s*%let\s", re.I),
}
PATH_FIX = {
    "Python": "Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], "
              "then ROOT / \"data\" / \"raw\" / \"file.csv\".",
    "R": "Use paths relative to the package's top folder and run everything from there through the master "
         "script (or use here::here(\"data\", \"raw\", \"file.csv\")).",
    "Stata": "Set the root once in the master do-file (global root \"`c(pwd)'\") and write paths as "
             "\"$root/data/raw/file.dta\".",
    "MATLAB": "Find the package folder with root = fileparts(mfilename('fullpath')) and build paths with "
              "fullfile(root, 'data', 'file.csv').",
    "SAS": "Define the root once in the master program (%let root = ...;), use &root./data/... everywhere, "
           "and tell replicators in the README that this is the only line to change.",
    "Shell": "Start the script with cd \"$(dirname \"$0\")\" and use relative paths.",
}
CHDIR_FIX = {
    "R": "Remove setwd(). Run the package from its top folder (through the master script) and use relative paths.",
    "Python": "Remove os.chdir(). Build every path from Path(__file__) instead.",
    "Stata": "Keep at most one cd, in the master do-file, pointing at the package root ($root). "
             "Remove cd from the other do-files.",
    "MATLAB": "Remove cd. Build paths with fullfile(root, ...) instead.",
    "SAS": "Remove the change of folder. Use one %let root = ...; in the master program.",
}


def is_concatenated(code: str, quote_pos: int) -> bool:
    prefix = code[:quote_pos].rstrip()
    return bool(prefix) and (prefix[-1].isalnum() or prefix[-1] in "+,&)]_." or prefix.endswith(".."))


def path_hits(code: str, lang: str):
    """Absolute or home-folder paths in a piece of code, as (kind, path) pairs."""
    found = []   # (start, end, kind, path)
    for m in WIN_RE.finditer(code):
        found.append((m.start(1), m.end(1), "abs", m.group(1)))
    for m in UNC_RE.finditer(code):
        found.append((m.start(1), m.end(1), "abs", m.group(1)))
    for m in STRONG_RE.finditer(code):
        if lang == "Stata" and m.start(1) > 0 and code[m.start(1) - 1] == "'":
            continue  # `root'/Users... starts with a macro, so it is not absolute
        found.append((m.start(1), m.end(1), "abs", m.group(1)))
    for m in WEAK_RE.finditer(code):
        if not is_concatenated(code, m.start(1)):
            found.append((m.start(2), m.end(2), "abs", m.group(2)))
    for m in TILDE_RE.finditer(code):
        found.append((m.start(1), m.end(1), "home", m.group(1)))
    hits, taken = [], []
    for start, end, kind, path in sorted(found):
        if any(start < e and end > b for b, e in taken):
            continue
        taken.append((start, end))
        hits.append((kind, path))
    return hits


QUOTED_STR_RE = re.compile(r'"([^"\n]*)"|\'([^\'\n]*)\'')
BACKSLASH_PATH_RE = re.compile(r"[\w.$`'{}-]+(?:\\{1,2}[\w.$`'{}-]+)+")
PATHLIKE_EXTS = DATA_EXTS | OUTPUT_EXTS | set(LANG_BY_EXT)


def backslash_paths(code: str, lang: str):
    """Relative paths written with backslashes, which work only on Windows."""
    out = []
    for m in QUOTED_STR_RE.finditer(code):
        text = m.group(1) if m.group(1) is not None else m.group(2)
        if m.group(2) is not None and lang == "Stata":
            continue
        if text and BACKSLASH_PATH_RE.fullmatch(text):
            seps = len(re.findall(r"\\{1,2}", text))
            ext = "." + text.rsplit(".", 1)[-1].lower() if "." in text else ""
            if seps >= 2 or ext in PATHLIKE_EXTS:
                out.append(text)
    return out


def check_paths(sources, report):
    for s in sources:
        is_master = s.info.rel in report.master
        chdir_re = CHDIR_RE.get(s.lang)
        for label, code, comment in s.rows:
            hits = path_hits(code, s.lang)
            moves = bool(chdir_re and chdir_re.search(code))
            if hits:
                kind, path = hits[0]
                synced = " It points into a synced folder (Dropbox, OneDrive or similar)." if SYNCED_RE.search(path) else ""
                if moves:
                    sev, msg = "High", f"Changes the working folder to a hard-coded path: `{short(path, 70)}`.{synced}"
                elif kind == "home":
                    sev, msg = "Medium", f"Path inside one person's home folder: `{short(path, 70)}`. It works only on that computer.{synced}"
                elif is_master and ROOT_DEFINITION_RE.get(s.lang, re.compile("$^")).search(code):
                    sev, msg = "Medium", f"The master script sets the root folder to a fixed path: `{short(path, 70)}`."
                else:
                    sev, msg = "High", f"Hard-coded absolute path: `{short(path, 70)}`.{synced}"
                fix = PATH_FIX.get(s.lang, PATH_FIX["Python"])
                if sev == "Medium" and is_master and kind == "abs" and not moves:
                    fix = ("Detect the root automatically (for example from the script's own location), or make this "
                           "the only line a replicator edits and say so in the README.")
                if len(hits) > 1:
                    msg += f" ({len(hits)} paths on this line.)"
                report.add(sev, "Paths", where(s, label), msg, fix)
            elif backslash_paths(code, s.lang):
                bad = backslash_paths(code, s.lang)[0]
                report.add("Medium", "Paths", where(s, label),
                           f"Path written with backslashes: `{short(bad, 70)}`. This works only on Windows.",
                           "Use forward slashes (data/raw/file.csv). They work on Windows, Mac and Linux.")
            if not hits and moves:
                sev = "Low" if is_master else "Medium"
                report.add(sev, "Paths", where(s, label),
                           f"Changes the working folder: `{short(code, 70)}`.",
                           CHDIR_FIX.get(s.lang, CHDIR_FIX["R"]) if not is_master else
                           "Fine if it points at the package root, found automatically. Make sure it never "
                           "needs editing.")
            if comment:
                for kind, path in path_hits(comment, s.lang):
                    report.add("Low", "Paths", where(s, label),
                               f"Absolute path in a comment: `{short(path, 70)}`.",
                               "Harmless when running, but it reveals where files lived on the author's "
                               "computer. Delete or update the comment.")
                    break


# ---------------------------------------------------------------------------
# 4. Dependencies
# ---------------------------------------------------------------------------
IMPORT_TO_DIST = {
    "sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow", "yaml": "pyyaml",
    "bs4": "beautifulsoup4", "dateutil": "python-dateutil", "Bio": "biopython",
    "skimage": "scikit-image", "docx": "python-docx", "pptx": "python-pptx",
    "dotenv": "python-dotenv", "attr": "attrs", "mpl_toolkits": "matplotlib",
    "pkg_resources": "setuptools", "IPython": "ipython", "osgeo": "gdal", "fitz": "pymupdf",
    "jwt": "pyjwt", "Crypto": "pycryptodome", "zmq": "pyzmq", "serial": "pyserial",
}
R_BASE = {"base", "stats", "utils", "graphics", "grDevices", "methods", "datasets", "tools",
          "parallel", "grid", "splines", "stats4", "tcltk", "compiler"}
STATA_COMMUNITY = [
    "reghdfe", "ftools", "ivreghdfe", "ivreg2", "ranktest", "esttab", "estout", "eststo", "estadd",
    "outreg2", "coefplot", "winsor2", "gtools", "gcollapse", "gegen", "boottest", "rdrobust",
    "rdplot", "csdid", "did_multiplegt", "did_imputation", "eventstudyinteract", "jwdid",
    "binscatter", "binsreg", "unique", "distinct", "tabout", "mdesc", "carryforward", "labutil",
    "asdoc", "texsave", "synth", "psmatch2", "xtabond2", "ppmlhdfe", "weakivtest", "rangestat",
    "rangejoin", "egenmore", "fre", "sumup", "outtable", "frmttable", "spmap", "shp2dta", "geodist",
    "reclink", "matchit", "strgroup", "ietoolkit", "iefieldkit", "ritest", "wyoung", "sdid",
    "avar", "lassopack", "pdslasso", "event_plot", "grc1leg",
]
STATA_CMD_RE = re.compile(
    r"(?:^|:)\s*(?:(?:cap|capture|qui|quietly|noi|noisily|xi|eststo(?:\s+\w+)?)\s*:?\s+)*("
    + "|".join(STATA_COMMUNITY) + r")\b", re.M)
PY_IMPORT_RE = re.compile(r"^\s*(?:import\s+([A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.]*)*)"
                          r"|from\s+([A-Za-z_][\w.]*)\s+import\b)")
R_LIB_RE = re.compile(r"\b(?:library|require|requireNamespace)\s*\(\s*[\"']?([A-Za-z][\w.]*)")
R_NS_RE = re.compile(r"\b([A-Za-z][\w.]*):::?[A-Za-z._]")
R_PLOAD_RE = re.compile(r"\bp_load\s*\(([^)]*)\)")


def python_requirements(files):
    """Return (dependency files, {name: pinned?}, has_lock)."""
    dep_files, pins, has_lock = [], {}, False
    for f in files:
        name = f.path.name.lower()
        if f.vendored:
            continue
        if name in ("pipfile.lock", "poetry.lock", "uv.lock", "pdm.lock", "conda-lock.yml"):
            dep_files.append(f.rel)
            has_lock = True
            text = (read_text(f.path) or "").lower()
            for m in re.finditer(r'name\s*=\s*"([^"]+)"|"([a-z0-9_.-]+)"\s*:\s*\{', text):
                pins[(m.group(1) or m.group(2)).replace("_", "-")] = True
        elif re.match(r"requirements.*\.(txt|in)$", name):
            dep_files.append(f.rel)
            for line in (read_text(f.path) or "").splitlines():
                line = line.split("#", 1)[0].strip()
                if not line or line.startswith("-"):
                    continue
                m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)", line)
                if m:
                    spec = m.group(3)
                    exact = bool(re.match(r"===?\s*[\w.]+\s*(;|$)", spec)) and "*" not in spec
                    direct_url = spec.startswith("@") or " @ " in line
                    pinned = exact or direct_url
                    pins[m.group(1).lower().replace("_", "-")] = pinned
        elif re.match(r"environment.*\.ya?ml$", name):
            dep_files.append(f.rel)
            in_deps = False
            for line in (read_text(f.path) or "").splitlines():
                if re.match(r"^\s*dependencies\s*:", line):
                    in_deps = True
                    continue
                if in_deps and re.match(r"^\S", line):
                    in_deps = False
                m = re.match(r"^\s*-\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(.*)$", line)
                if in_deps and m and m.group(1) != "pip":
                    spec = m.group(2).strip()
                    pins[m.group(1).lower().replace("_", "-")] = bool(re.match(r"==?\s*\d", spec))
        elif name == "pyproject.toml":
            dep_files.append(f.rel)
            try:
                import tomllib
                data = tomllib.loads(read_text(f.path) or "")
            except Exception:
                data = {}
            for dep in data.get("project", {}).get("dependencies", []):
                m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(.*)", dep)
                if m:
                    pins.setdefault(m.group(1).lower().replace("_", "-"), "==" in m.group(2))
            poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for dep, spec in poetry.items():
                if dep.lower() != "python":
                    pins.setdefault(dep.lower().replace("_", "-"), isinstance(spec, str) and re.match(r"^=?=?\d", spec) is not None)
    if has_lock:
        pins = {k: True for k in pins}
    return dep_files, pins, has_lock


def check_dependencies(files, sources, langs, report):
    local_names = {Path(f.rel).stem for f in files if f.ext == ".py"}
    local_names |= {part for f in files for part in Path(f.rel).parts[:-1]}
    stdlib = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}

    # Python ----------------------------------------------------------------
    if "Python" in langs:
        dep_files, pins, has_lock = python_requirements(files)
        report.dependency_files += dep_files
        imports = {}
        for s in sources:
            if s.lang != "Python":
                continue
            for label, code, _ in s.rows:
                m = PY_IMPORT_RE.match(code)
                if not m:
                    continue
                names = m.group(1).split(",") if m.group(1) else [m.group(2)]
                for name in names:
                    top = name.strip().split(".")[0]
                    if top and top not in stdlib and top not in local_names:
                        imports.setdefault(top, s.info.rel)
        if not dep_files and imports:
            report.add("Medium", "Dependencies", "(package)",
                       "Python code but no list of packages with versions (no requirements.txt or "
                       "environment.yml). Imports: " + ", ".join(sorted(imports)) + ".",
                       "Ask the author for the versions they used (pip freeze on their computer) and write "
                       "requirements.txt with name==version lines.")
        unpinned = sorted(k for k, v in pins.items() if not v and k != "python")
        if unpinned:
            report.add("Medium", "Dependencies", ", ".join(dep_files),
                       "Packages listed without exact versions: " + ", ".join(unpinned) + ".",
                       "Pin each one with ==, using the versions the author actually used (pip freeze on "
                       "their computer), not today's latest versions.")
        if dep_files:
            listed = set(pins)
            missing = []
            for top, rel in sorted(imports.items()):
                dist = IMPORT_TO_DIST.get(top, top).lower().replace("_", "-")
                if dist not in listed and top.lower() not in listed:
                    missing.append(f"{IMPORT_TO_DIST.get(top, top)} (imported in {rel})")
            if missing:
                report.add("Medium", "Dependencies", ", ".join(dep_files),
                           "Imported in the code but not in the package list: " + "; ".join(missing) + ".",
                           "Add each one with its exact version (name==version).")

    # R ---------------------------------------------------------------------
    if "R" in langs:
        used = {}
        for s in sources:
            if s.lang != "R":
                continue
            for _, code, _ in s.rows:
                names = R_LIB_RE.findall(code) + R_NS_RE.findall(code)
                for group in R_PLOAD_RE.findall(code):
                    names += [n.strip().strip("\"'") for n in group.split(",") if "=" not in n]
                for n in names:
                    if n and n not in R_BASE and n not in ("pacman",):
                        used.setdefault(n, s.info.rel)
        lock = [f for f in files if f.path.name.lower() in ("renv.lock", "packrat.lock")]
        r_text = "\n".join(s.code_text for s in sources if s.lang == "R")
        other_pin = re.search(r"groundhog\.library|install_version\s*\(|checkpoint\s*\(", r_text)
        if lock:
            report.dependency_files += [f.rel for f in lock]
            locked = set()
            for f in lock:
                text = read_text(f.path) or ""
                try:
                    locked |= set(json.loads(text).get("Packages", {}))
                except ValueError:
                    locked |= set(re.findall(r"^Package:\s*(\S+)", text, re.M))
            missing = sorted(n for n in used if n not in locked)
            if missing:
                report.add("Medium", "Dependencies", lock[0].rel,
                           "R packages used in the code but not in the lock file: " + ", ".join(missing) + ".",
                           "Run renv::snapshot() in the author's project after loading all packages, "
                           "and include the updated renv.lock.")
        elif used and not other_pin:
            report.add("Medium", "Dependencies", "(package)",
                       "R packages are not pinned (no renv.lock). Packages used: "
                       + ", ".join(sorted(used)) + ".",
                       "In the author's R setup run renv::init() and renv::snapshot(), then include renv.lock. "
                       "At least list every package and version in the README (from sessionInfo()).")

    # Stata -----------------------------------------------------------------
    if "Stata" in langs:
        stata = [s for s in sources if s.lang == "Stata"]
        used = {}
        for s in stata:
            for cmd in STATA_CMD_RE.findall(s.code_text):
                used.setdefault(cmd, s.info.rel)
        text = "\n".join(s.code_text for s in stata)
        has_ado_dir = any(f.ext == ".ado" and f.vendored for f in files)
        installs = re.search(r"\b(ssc|net)\s+install\b", text)
        ado_list = [f for f in files if re.search(r"ado|stata.?(packages|requirements)", f.path.stem, re.I)
                    and f.ext in (".txt", ".md", ".csv")]
        if used and not (has_ado_dir or installs or ado_list):
            report.add("Medium", "Dependencies", ", ".join(sorted(set(used.values()))),
                       "Uses Stata community commands with no list or copy of them: "
                       + ", ".join(sorted(used)) + ".",
                       "Save the exact ado files inside the package (an ado/ folder set up in the master "
                       "do-file, see templates/main.do) and list them with versions in the README.")
        elif installs and not has_ado_dir:
            report.add("Low", "Dependencies", "(Stata code)",
                       "Community packages are installed with ssc/net install, which always fetches the "
                       "latest version.",
                       "Copy the exact ado files into an ado/ folder in the package so results cannot change "
                       "when a package is updated.")
        if stata and not re.search(r"^\s*version\s+\d", text, re.M):
            report.add("Low", "Dependencies", "(Stata code)",
                       "No version statement in the do-files.",
                       "Add version NN (the Stata version the author used) near the top of the master do-file.")


# ---------------------------------------------------------------------------
# 5. Data files the code reads
# ---------------------------------------------------------------------------
QUOTED_FILE_RE = re.compile(r"([\"'])([^\"'\n]{1,300}?\.(?:" + "|".join(e[1:] for e in sorted(DATA_EXTS))
                            + r"))\1", re.I)
STATA_FILE_RE = re.compile(r"\b(use|using|save|saveold)\s+(\"[^\"]+\"|[^\s,\"]+)", re.I)
STATA_READ_CMDS = {"use", "merge", "append", "joinby", "cross", "insheet", "import", "infile", "infix"}
STATA_WRITE_CMDS = {"save", "saveold", "export", "outsheet", "esttab", "estout", "outreg2", "log",
                    "putexcel", "texsave", "graph", "outfile", "file"}
READ_VERBS = re.compile(
    r"(read_csv|read_table|read_excel|read_stata|read_spss|read_sas|read_parquet|read_feather|read_json"
    r"|read_pickle|read_fwf|read_hdf|read_dta|read_sav|read_xlsx|read_xls|read_delim|read_tsv"
    r"|read\.csv2?|read\.table|read\.delim|read\.dta|read\.xlsx|readRDS|read_rds|fread|vroom"
    r"|\bload\s*\(|loadtxt|genfromtxt|np\.load|open\s*\(|readtable|readmatrix|readcell|csvread|xlsread"
    r"|importdata|\bload\b|st_read|read_sf|read_file|import\s+delimited|import\s+excel|insheet"
    r"|\buse\b|infile|datafile\s*=|\bset\b|read_xpt)", re.I)
WRITE_VERBS = re.compile(
    r"(to_csv|to_excel|to_stata|to_parquet|to_pickle|to_json|to_latex|to_feather|to_html|to_markdown"
    r"|write\.csv2?|write\.table|write_csv|write_tsv|write_dta|write_rds|write_xlsx|write\.xlsx"
    r"|write_parquet|saveRDS|\bsave\s*\(|save_kable|fwrite|ggsave|savefig|\bpng\s*\(|\bpdf\s*\("
    r"|jpeg\s*\(|svg\s*\(|\bsave\b|saveold|export\s+delimited|export\s+excel|graph\s+export|esttab"
    r"|estout|outreg2|outsheet|putexcel|writetable|writematrix|writecell|csvwrite|xlswrite|saveas"
    r"|exportgraphics|outfile\s*=|\bods\b|\bsink\s*\(|log\s+using|texsave|stargazer|modelsummary"
    r"|etable|writeLines|np\.save|savetxt|json\.dump|pickle\.dump)", re.I)


def classify(code: str, pos: int, end: int) -> str:
    """Is the file at code[pos:end] read, written, or just mentioned?"""
    before = code[:pos]
    last_read = max(READ_VERBS.finditer(before), key=lambda m: m.end(), default=None)
    last_write = max(WRITE_VERBS.finditer(before), key=lambda m: m.end(), default=None)
    if last_read is None and last_write is None:
        return "unknown"
    if last_read is None or (last_write is not None and last_write.end() > last_read.end()):
        return "write"
    if last_read.group(0).lower().startswith("open"):
        if re.match(r"\s*,\s*(mode\s*=\s*)?[\"'][wax]", code[end:]):
            return "write"
    return "read"


def stata_mode(code: str, keyword: str) -> str:
    first = re.sub(r"^\s*((cap|capture|qui|quietly|noi|noisily)\s+)*", "", code).split()
    cmd = first[0].lower() if first else ""
    if keyword.lower() in ("save", "saveold"):
        return "write"
    if keyword.lower() == "use" and cmd == "use":
        return "read"
    if cmd in STATA_WRITE_CMDS:
        return "write"
    if cmd in STATA_READ_CMDS:
        return "read"
    return "unknown"


def file_references(sources):
    """Every file name the code mentions: (source, label, reference, mode)."""
    refs = []
    for s in sources:
        for label, code, _ in s.rows:
            seen = set()
            for m in QUOTED_FILE_RE.finditer(code):
                ref = m.group(2)
                seen.add(ref)
                mode = classify(code, m.start(), m.end())
                if s.lang == "Stata" and mode == "unknown":
                    mode = stata_mode(code, "using")   # merge/append/joinby ... using "file"
                refs.append((s, label, ref, mode))
            if s.lang == "Stata":
                for m in STATA_FILE_RE.finditer(code):
                    ref = m.group(2).strip('"')
                    if ref in seen or ref.lower() in ("using", "replace", "clear"):
                        continue
                    if not Path(ref.replace("\\", "/")).suffix and m.group(1).lower() in ("use", "using", "save", "saveold"):
                        mode = stata_mode(code, m.group(1))
                        if mode == "unknown":
                            continue
                        ref += ".dta"
                    elif not Path(ref.replace("\\", "/")).suffix:
                        continue
                    refs.append((s, label, ref, stata_mode(code, m.group(1))))
    return refs


def check_data_references(root, files, sources, report):
    by_lower = {}
    for f in files:
        by_lower.setdefault(f.path.name.lower(), []).append(f.path.name)
    refs = file_references(sources)
    written = {Path(r.replace("\\", "/")).name.lower() for _, _, r, mode in refs if mode == "write"}
    reported = set()
    for s, label, ref, mode in refs:
        if mode == "write":
            continue
        clean = ref.replace("\\", "/")
        if re.match(r"^(https?|ftp)://", clean, re.I):
            key = (clean.lower(), s.info.rel)
            if key not in reported:
                reported.add(key)
                report.add("Medium", "Data files", where(s, label),
                           f"Downloads data from the internet when it runs: `{short(clean, 70)}`.",
                           "Web data can change or disappear. If the licence allows, save a copy in the package "
                           "and read that instead; record the download date and cite the source in the README.")
            continue
        base = clean.rsplit("/", 1)[-1]
        if not base or re.search(r"[$`'{}%*<>]", base) or base.lower() in written:
            continue
        if Path(clean).suffix.lower() not in DATA_EXTS:
            continue
        if not re.match(r"^[A-Za-z]:|^/|^~|^\\\\", clean):
            if (root / clean).exists() or (s.info.path.parent / clean).exists():
                continue
        names = by_lower.get(base.lower())
        key = (base.lower(), s.info.rel)
        if key in reported:
            continue
        if names and base in names:
            continue
        reported.add(key)
        if names:
            report.add("Low", "Data files", where(s, label),
                       f"The code asks for `{base}` but the file is called `{names[0]}`. "
                       "Upper and lower case matter on Linux and Mac.",
                       "Make the name in the code match the file name exactly.")
        elif mode == "read":
            report.add("High", "Data files", where(s, label),
                       f"Reads `{short(base, 60)}`, which is not in the package.",
                       "Add the file. If the data are restricted or confidential, keep the code, and explain in "
                       "the README's data availability section how a replicator can get access.")
        else:
            report.add("Low", "Data files", where(s, label),
                       f"Mentions `{short(base, 60)}`, which is not in the package (it may be created by the code).",
                       "Check whether a program creates it. If not, add it or document how to get it.")


# ---------------------------------------------------------------------------
# 6. Outputs without a producing program
# ---------------------------------------------------------------------------
def output_candidates(files):
    out = []
    for f in files:
        if f.vendored or f.ext not in OUTPUT_EXTS:
            continue
        name = f.path.name.lower()
        if name.startswith(("readme", "license", "licence", "requirements", "changelog")):
            continue
        dirs = Path(f.rel).parts[:-1]
        if any(NOT_OUTPUT_DIR_RE.match(d) for d in dirs):
            continue
        if any(OUTPUT_DIR_RE.match(d) for d in dirs) or OUTPUT_NAME_RE.match(f.path.name):
            out.append(f)
    return out


def check_outputs(files, sources, report):
    code = "\n".join(s.code_text for s in sources).lower()
    outputs = output_candidates(files)
    report.outputs = [f.rel for f in outputs]
    for f in outputs:
        name, stem = f.path.name.lower(), f.path.stem.lower()
        if name in code or (len(stem) >= 4 and stem in code):
            continue
        report.add("Medium", "Outputs", f.rel,
                   "No program in the package appears to create this file.",
                   "Ask the author for the program that makes it and add it to the master script and the "
                   "table/figure list. If the file is not in the paper, remove it. Never recreate an output by hand.")


# ---------------------------------------------------------------------------
# 7. Large files, 8. personal data in CSV headers
# ---------------------------------------------------------------------------
PII_RULES = [
    ("name", re.compile(r"^(name|fullname|firstname|lastname|surname|givenname|familyname|fname|lname"
                        r"|.*(student|respondent|person|patient|participant|parent|child|mother|father"
                        r"|spouse|teacher|owner|contact|client|customer|employee|worker|member)name)$")),
    ("email", re.compile(r"(e?mail|emailaddress)")),
    ("phone", re.compile(r"(phone|^tel$|^mobile$|mobileno|mobilenumber|^cell$|^fax$|whatsapp)")),
    ("address", re.compile(r"(address|^addr|street|^zip$|zipcode|postcode|postalcode)")),
    ("birth date", re.compile(r"(^dob$|dateofbirth|birthdate|birthday|^bdate$|^bday$|^birth$|birthdt)")),
    ("ID number", re.compile(r"(^ssn$|socialsecurity|passport|nationalid|^nid$|taxid|driverslicen)")),
    ("location", re.compile(r"(^gps|latitude|longitude|^lat$|^lon$|^lng$|coordinates|geoloc)")),
    ("online ID", re.compile(r"(ipaddress|^ip$|username|userid_email)")),
]
NAME_EXCEPTIONS = re.compile(r"(file|var|variable|col|column|dataset|school|country|state|county|city"
                             r"|district|region|firm|company|industry|product|program|item|bank|brand"
                             r"|team|occupation|sheet|table|label|unit|province|municipality|village)name$")


def pii_type(column: str):
    tokens = re.sub(r"([a-z])([A-Z])", r"\1_\2", column.strip())
    norm = re.sub(r"[^a-z0-9]", "", tokens.lower())
    if not norm:
        return None
    for kind, rule in PII_RULES:
        if rule.search(norm):
            if kind == "name" and NAME_EXCEPTIONS.search(norm):
                return None
            return kind
    return None


def csv_header(path: Path):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        first = fh.readline()
    if not first:
        return []
    delim = "\t" if path.suffix.lower() == ".tsv" else max([",", ";", "\t", "|"], key=first.count)
    return next(csv.reader([first], delimiter=delim), [])


def check_files(files, junk, large_mb, csv_max_mb, report):
    for f in files:
        mb = f.size / 1024 / 1024
        if mb > large_mb:
            report.add("Medium", "Large files", f.rel, f"Very large file: {mb:,.0f} MB.",
                       "Check the repository's size limits. Compress it, split it, or leave it out and explain "
                       "in the README how to get it.")
        if f.ext in (".csv", ".tsv") and mb <= csv_max_mb:
            flagged = {}
            for col in csv_header(f.path):
                kind = pii_type(col)
                if kind:
                    flagged.setdefault(kind, []).append(col)
            if flagged:
                parts = [f"{kind}: {', '.join(cols)}" for kind, cols in flagged.items()]
                direct = any(k in flagged for k in ("name", "email", "phone", "address", "birth date", "ID number"))
                report.add("High" if direct else "Medium", "Personal data", f.rel,
                           "Column names suggest personal data (" + "; ".join(parts) + "). "
                           "Only the header row was read; no values were opened.",
                           "Ask the author. If these are real identifiers, remove the columns before publishing "
                           "(if the analysis does not use them) or move the file to restricted access and explain "
                           "access in the README. Do not open or share the values.")
    if junk:
        report.add("Low", "Housekeeping", ", ".join(junk[:8]) + (" ..." if len(junk) > 8 else ""),
                   f"{len(junk)} stray system or temporary file(s) or folder(s).",
                   "Delete them from the deposit (they are created by Mac, Windows, Python, R or Office).")
    if not any(f.path.name.lower().startswith(("license", "licence", "copying")) for f in files):
        report.add("Low", "Housekeeping", "(package)", "No LICENSE file.",
                   "Ask the author which licence to use for code and data (for example MIT for code, CC BY 4.0 "
                   "for data they own) and add a LICENSE file.")


# ---------------------------------------------------------------------------
# 9. Random numbers without a seed, 10. logs
# ---------------------------------------------------------------------------
RANDOM_USE = {
    "Python": re.compile(r"np\.random\.(?!seed)\w+\s*\(|numpy\.random\.(?!seed)\w+\s*\(|\brandom\.(random|randint"
                         r"|choice|choices|shuffle|sample|uniform|gauss)\s*\(|default_rng\s*\(\s*\)"
                         r"|\.sample\s*\((?![^)]*random_state)"),
    "R": re.compile(r"\b(sample|rnorm|runif|rbinom|rpois|rexp|rgamma|rbeta|rmultinom|rchisq|boot"
                    r"|sample_n|sample_frac|slice_sample|kmeans)\s*\("),
    "Stata": re.compile(r"\b(runiform|rnormal|rbinomial|rpoisson|uniform)\s*\(|\b(bsample|bootstrap|permute"
                        r"|simulate|splitsample)\b|^\s*sample\s+\d|vce\s*\(\s*boot", re.M),
    "MATLAB": re.compile(r"\b(rand|randn|randi|randperm|bootstrp|datasample|randsample|normrnd|unifrnd)\s*\("),
    "SAS": re.compile(r"\b(ranuni|rannor|ranbin|ranpoi|rand)\s*\(|proc\s+surveyselect", re.I),
}
RANDOM_SEED = {
    "Python": re.compile(r"random\.seed\s*\(|default_rng\s*\(\s*\w|RandomState\s*\(\s*\w"),
    "R": re.compile(r"set\.seed\s*\("),
    "Stata": re.compile(r"set\s+seed\b|\bseed\s*\(\s*\d"),
    "MATLAB": re.compile(r"\brng\s*[\(\s]|RandStream"),
    "SAS": re.compile(r"streaminit|seed\s*=\s*[1-9]|ranuni\s*\(\s*[1-9]", re.I),
}
SEED_EXAMPLE = {"Python": "rng = np.random.default_rng(20240101)", "R": "set.seed(20240101)",
                "Stata": "set seed 20240101", "MATLAB": "rng(20240101)", "SAS": "call streaminit(20240101);"}


def check_randomness(sources, readme_text, report):
    for lang, use_re in RANDOM_USE.items():
        files = [s for s in sources if s.lang == lang]
        if not files:
            continue
        seeded = any(RANDOM_SEED[lang].search(s.code_text) for s in files)
        for s in files:
            for label, code, _ in s.rows:
                if use_re.search(code) and not RANDOM_SEED[lang].search(code):
                    if not seeded:
                        report.add("Medium", "Randomness", where(s, label),
                                   f"Uses random numbers but no seed is set: `{short(code, 60)}`.",
                                   f"Set a seed once, e.g. {SEED_EXAMPLE[lang]}, and describe it in the README. "
                                   "A new seed can change results slightly: agree with the author first and report "
                                   "any change.")
                    elif readme_text is not None and "seed" not in readme_text.lower():
                        report.add("Low", "Randomness", where(s, label),
                                   "Uses random numbers; the code sets a seed but the README does not mention it.",
                                   "Add a 'Controlled randomness' note to the README saying where the seed is set.")
                    break


LOG_CODE_RE = re.compile(r"log\s+using|\bsink\s*\(|R CMD BATCH|logging\.(basicConfig|getLogger|FileHandler)"
                         r"|\bdiary\b|proc\s+printto|\btee\b|\.log[\"']", re.I)


def check_logs(files, sources, report):
    log_files = [f for f in files if f.ext in (".log", ".smcl", ".rout")
                 or any(p.lower() in ("log", "logs") for p in Path(f.rel).parts[:-1])]
    if log_files or any(LOG_CODE_RE.search(s.code_text) for s in sources):
        return
    report.add("Medium", "Logs", "(package)",
               "No log files, and no code that writes a log.",
               "Have the master script save a log of the full run (templates/main.* do this), run it once, "
               "and include the logs in the package.")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
class Report:
    def __init__(self, root: Path):
        self.root = root
        self.findings: list[Finding] = []
        self.readme = None
        self.readme_sections_missing = 0
        self.master: list[str] = []
        self.dependency_files: list[str] = []
        self.outputs: list[str] = []

    def add(self, severity, category, where_, finding, fix):
        self.findings.append(Finding(severity, category, where_, finding, fix))

    def finalize(self):
        self.findings.sort(key=lambda f: (SEVERITIES.index(f.severity), CATEGORIES.index(f.category),
                                          natural_key(f.where)))
        width = max(2, len(str(len(self.findings))))
        for i, f in enumerate(self.findings, 1):
            f.id = f"F{i:0{width}d}"

    def counts(self):
        return {s: sum(1 for f in self.findings if f.severity == s) for s in SEVERITIES}


def natural_key(text: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def write_markdown(report: Report, files, out: Path, today: str):
    counts = report.counts()
    total_mb = sum(f.size for f in files) / 1024 / 1024
    lang_counts = {lang: sum(1 for f in files if f.lang == lang and not f.vendored) for lang in CHECKED_LANGS}
    lines = [
        f"# Replication package check: {report.root.name}",
        "",
        f"Checked {today} with check_package.py {VERSION}. This is an automated first pass: "
        "every finding needs a human look before you act on it.",
        "",
        "## Summary",
        "",
        "| Severity | Findings | What it means |",
        "|---|---:|---|",
    ]
    for s in SEVERITIES:
        lines.append(f"| {s} | {counts[s]} | {SEVERITY_MEANING[s]} |")
    lines.append(f"| **Total** | **{len(report.findings)}** | |")
    lines += ["", "## Package at a glance", ""]
    lines.append(f"- **Files:** {len(files)} ({total_mb:,.1f} MB)")
    code_bits = [f"{lang} {n}" for lang, n in lang_counts.items() if n]
    lines.append("- **Code files:** " + (", ".join(code_bits) if code_bits else "none found"))
    lines.append(f"- **README:** {report.readme or 'none found'}")
    lines.append("- **Master script:** " + (", ".join(report.master) if report.master else "none found"))
    lines.append("- **Dependency files:** " + (", ".join(sorted(set(report.dependency_files))) or "none found"))
    lines.append(f"- **Tables and figures found:** {len(report.outputs)}")
    lines += ["", "## Findings", ""]
    if not report.findings:
        lines.append("No findings. Still read the README and run the package before you sign off.")
    for sev in SEVERITIES:
        group = [f for f in report.findings if f.severity == sev]
        if not group:
            continue
        lines += [f"### {sev} ({len(group)})", "", "| ID | Check | Where | Finding | Suggested fix |",
                  "|---|---|---|---|---|"]
        for f in group:
            lines.append(f"| {f.id} | {f.category} | {md_cell(f.where)} | {md_cell(f.finding)} | {md_cell(f.fix)} |")
        lines.append("")
    lines += [
        "## What this check does not do",
        "",
        "- It does not run the code. Use run_and_compare.py for that.",
        "- It reads text patterns, so it can miss problems and can flag things that are fine.",
        "- For CSV and TSV files it reads only the header row. It never opens or prints data values.",
        "- It cannot judge whether the README is accurate, only whether the expected sections exist.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def write_excel(report: Report, files, out: Path, today: str):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        print("openpyxl is not installed, so the .xlsx report was skipped (pip install openpyxl).")
        return False

    base = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    head_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1F3A5F")
    edit_fill = PatternFill("solid", fgColor="FFF2CC")
    sev_fill = {"High": "F8D7DA", "Medium": "FFE8C2", "Low": "DCEBFA", "Info": "EDEDED"}
    thin = Side(style="thin", color="D0D0D0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = f"Replication package check: {report.root.name}"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = f"Checked {today} with check_package.py {VERSION}. Automated first pass: review every finding."
    ws["A2"].font = base
    headers = ["Severity", "Findings", "Still open", "What it means"]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=col, value=h)
        c.font, c.fill, c.border = head_font, head_fill, border
    for r, sev in enumerate(SEVERITIES, 5):
        ws.cell(row=r, column=1, value=sev)
        ws.cell(row=r, column=2, value=f'=COUNTIF(Findings!$B:$B,"{sev}")')
        ws.cell(row=r, column=3, value=f'=COUNTIFS(Findings!$B:$B,"{sev}",Findings!$G:$G,"Open")')
        ws.cell(row=r, column=4, value=SEVERITY_MEANING[sev])
        for col in range(1, 5):
            c = ws.cell(row=r, column=col)
            c.font, c.border = base, border
        ws.cell(row=r, column=1).fill = PatternFill("solid", fgColor=sev_fill[sev])
    total_row = 5 + len(SEVERITIES)
    ws.cell(row=total_row, column=1, value="Total").font = bold
    ws.cell(row=total_row, column=2, value=f"=SUM(B5:B{total_row - 1})").font = bold
    ws.cell(row=total_row, column=3, value=f"=SUM(C5:C{total_row - 1})").font = bold
    for col in range(1, 5):
        ws.cell(row=total_row, column=col).border = border
    notes = [
        "How to use this workbook",
        "On the Findings sheet, edit only the yellow columns: Status (pick from the list) and Notes.",
        "The counts above update by themselves. 'Still open' counts findings whose Status is Open.",
        "Status values: Open, Fixed, Author to decide, Not an issue.",
        "For CSV files only the header row was read. No data values were opened or copied here.",
    ]
    for i, text in enumerate(notes):
        c = ws.cell(row=total_row + 2 + i, column=1, value=text)
        c.font = bold if i == 0 else base
    for col, width in zip("ABCD", (14, 11, 11, 70)):
        ws.column_dimensions[col].width = width

    fs = wb.create_sheet("Findings")
    cols = ["ID", "Severity", "Check", "Where", "Finding", "Suggested fix", "Status", "Notes"]
    widths = [7, 10, 14, 36, 60, 60, 16, 36]
    for col, (h, w) in enumerate(zip(cols, widths), 1):
        c = fs.cell(row=1, column=col, value=h)
        c.font, c.fill, c.border, c.alignment = head_font, head_fill, border, wrap
        fs.column_dimensions[get_column_letter(col)].width = w
    dv = DataValidation(type="list", formula1='"Open,Fixed,Author to decide,Not an issue"', allow_blank=False)
    fs.add_data_validation(dv)
    for r, f in enumerate(report.findings, 2):
        values = [f.id, f.severity, f.category, f.where, f.finding, f.fix, "Open", ""]
        for col, v in enumerate(values, 1):
            c = fs.cell(row=r, column=col, value=v)
            c.font, c.border, c.alignment = base, border, wrap
        fs.cell(row=r, column=2).fill = PatternFill("solid", fgColor=sev_fill[f.severity])
        fs.cell(row=r, column=7).fill = edit_fill
        fs.cell(row=r, column=8).fill = edit_fill
        dv.add(fs.cell(row=r, column=7))
    fs.freeze_panes = "A2"
    if report.findings:
        fs.auto_filter.ref = f"A1:H{len(report.findings) + 1}"

    inv = wb.create_sheet("Files")
    inv_cols = ["Path", "Size (MB)", "Type", "Role"]
    for col, (h, w) in enumerate(zip(inv_cols, (60, 11, 10, 16)), 1):
        c = inv.cell(row=1, column=col, value=h)
        c.font, c.fill, c.border = head_font, head_fill, border
        inv.column_dimensions[get_column_letter(col)].width = w
    outputs = set(report.outputs)
    for r, f in enumerate(sorted(files, key=lambda x: natural_key(x.rel)), 2):
        if f.vendored:
            role = "Bundled package"
        elif f.lang:
            role = f"Code ({f.lang})"
        elif f.rel in outputs:
            role = "Output"
        elif f.ext in DATA_EXTS:
            role = "Data"
        elif f.ext in DOC_EXTS:
            role = "Document"
        else:
            role = "Other"
        for col, v in enumerate([f.rel, round(f.size / 1024 / 1024, 3), f.ext or "(none)", role], 1):
            c = inv.cell(row=r, column=col, value=v)
            c.font, c.border = base, border
        inv.cell(row=r, column=2).number_format = "0.000"
    inv.freeze_panes = "A2"
    for sheet in (ws, fs, inv):
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
    fs.print_title_rows = "1:1"
    inv.print_title_rows = "1:1"
    wb.calculation.fullCalcOnLoad = True
    wb.save(out)
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_checks(root: Path, large_mb: float, csv_max_mb: float):
    files, junk = walk_package(root)
    sources = load_sources(files)
    langs = [lang for lang in CHECKED_LANGS if any(s.lang == lang for s in sources)]
    report = Report(root)
    readme = check_readme(files, [l for l in langs if l != "Shell"], report)
    check_master(files, sources, report)
    check_paths(sources, report)
    check_dependencies(files, sources, langs, report)
    check_data_references(root, files, sources, report)
    check_outputs(files, sources, report)
    check_files(files, junk, large_mb, csv_max_mb, report)
    check_randomness(sources, readme, report)
    check_logs(files, sources, report)
    report.finalize()
    return report, files, langs


def main(argv=None):
    parser = argparse.ArgumentParser(description="First-pass check of a research replication package.")
    parser.add_argument("package", help="Folder that holds the replication package")
    parser.add_argument("--out", help="Folder for the report (default: <package name>_check_report)")
    parser.add_argument("--large-mb", type=float, default=100, help="Flag files above this size in MB (default 100)")
    parser.add_argument("--csv-max-mb", type=float, default=50,
                        help="Read headers of CSV/TSV files up to this size in MB (default 50)")
    args = parser.parse_args(argv)

    root = Path(args.package).resolve()
    if not root.is_dir():
        parser.error(f"not a folder: {args.package}")
    out_dir = Path(args.out) if args.out else Path.cwd() / f"{root.name}_check_report"
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_dir.resolve() == root or root in out_dir.resolve().parents:
        parser.error("put the report outside the package folder, so the package stays unchanged")

    report, files, langs = run_checks(root, args.large_mb, args.csv_max_mb)
    today = dt.date.today().isoformat()
    md_path = out_dir / "check_report.md"
    xlsx_path = out_dir / "check_report.xlsx"
    write_markdown(report, files, md_path, today)
    wrote_xlsx = write_excel(report, files, xlsx_path, today)

    counts = report.counts()
    print(f"Checked {root.name}: {len(files)} files, {len(report.findings)} findings "
          + "(" + ", ".join(f"{counts[s]} {s}" for s in SEVERITIES) + ")")
    print(f"Report: {md_path}")
    if wrote_xlsx:
        print(f"Report: {xlsx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
