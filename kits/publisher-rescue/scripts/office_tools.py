"""Shared helpers for the Publisher Rescue scripts.

- find LibreOffice and check its version
- run LibreOffice one file at a time, with a timeout, in a private profile
- read PDFs: page count, text, fonts, and first-page preview pictures

PDF reading uses PyMuPDF when it is installed and falls back to the Poppler
command-line tools (pdfinfo, pdftotext, pdffonts, pdftoppm).
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

try:  # PyMuPDF 1.24+ is "pymupdf"; older versions only had "fitz".
    import pymupdf as fitz  # type: ignore
except ImportError:  # pragma: no cover - depends on the machine
    try:
        import fitz  # type: ignore
    except ImportError:
        fitz = None


# LibreOffice's import filter for Microsoft Publisher files. It uses libmspub.
# Forcing it stops LibreOffice from "guessing" and opening a damaged .pub
# file as a page of garbage text.
PUBLISHER_FILTER = "Publisher Document"

# Publisher 98 and later save files as OLE compound documents, which always
# start with these eight bytes.
OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")

# Which LibreOffice program opens each file type. Used to pick the right PDF
# export filter and to check that LibreOffice opened the file the way we expect.
MODULE_BY_EXT = {
    # Draw: Publisher and other page-layout or drawing formats
    "pub": "draw", "odg": "draw", "fodg": "draw", "vsd": "draw", "vsdx": "draw",
    "vdx": "draw", "cdr": "draw", "cmx": "draw", "wpg": "draw", "pmd": "draw",
    "pm6": "draw", "p65": "draw", "fh": "draw", "zmf": "draw",
    # Writer: word-processing formats
    "doc": "writer", "docx": "writer", "dot": "writer", "dotx": "writer",
    "odt": "writer", "fodt": "writer", "rtf": "writer", "wpd": "writer",
    "wps": "writer", "lwp": "writer",
    # Impress: presentation formats
    "ppt": "impress", "pptx": "impress", "pps": "impress", "ppsx": "impress",
    "pot": "impress", "potx": "impress", "odp": "impress", "fodp": "impress",
    "key": "impress",
}

PDF_EXPORT_FILTER = {
    "draw": "draw_pdf_Export",
    "writer": "writer_pdf_Export",
    "impress": "impress_pdf_Export",
}

# What LibreOffice prints in "convert x as a Draw document -> ..."
MODULE_LABEL = {"draw": "Draw", "writer": "Writer", "impress": "Impress"}

# PDF/A-2b: the ISO archive flavour of PDF. Needs LibreOffice 7.4 or newer
# (the JSON filter-options syntax arrived in 7.4).
PDFA_OPTIONS = '{"SelectPdfVersion":{"type":"long","value":"2"}}'


class OfficeToolsError(RuntimeError):
    """A problem the user has to fix, such as LibreOffice not being installed."""


# ---------------------------------------------------------------------------
# Finding LibreOffice
# ---------------------------------------------------------------------------

def find_soffice(explicit: str | None = None) -> str:
    """Return the path of the LibreOffice program, or raise OfficeToolsError."""
    candidates = [
        explicit,
        os.environ.get("SOFFICE"),
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/opt/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise OfficeToolsError(
        "LibreOffice was not found. On Ubuntu or Debian run scripts/setup.sh, "
        "or install it with: sudo apt-get install libreoffice-draw "
        "libreoffice-writer libreoffice-impress"
    )


def soffice_version(soffice: str) -> tuple[int, int] | None:
    """Return LibreOffice's (major, minor) version, or None if unknown."""
    try:
        out = subprocess.run(
            [soffice, "--version"], capture_output=True, text=True, timeout=120
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"LibreOffice\s+(\d+)\.(\d+)", out)
    return (int(match.group(1)), int(match.group(2))) if match else None


def soffice_version_text(soffice: str) -> str:
    try:
        out = subprocess.run(
            [soffice, "--version"], capture_output=True, text=True, timeout=120
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return out.strip().splitlines()[0] if out.strip() else "unknown"


def can_open_publisher_files() -> bool:
    """Best-effort check that LibreOffice Draw (which holds the Publisher
    filter) is installed. The real proof is converting a .pub file."""
    roots = [Path("/usr/lib/libreoffice/program"), Path("/opt/libreoffice/program")]
    for root in roots:
        if (root / "libwpftdrawlo.so").exists():
            return True
    return False


# ---------------------------------------------------------------------------
# Running LibreOffice
# ---------------------------------------------------------------------------

@dataclass
class ConvertResult:
    ok: bool
    output: Path | None
    seconds: float
    timed_out: bool
    opened_as: str  # "Draw", "Writer", "Impress" or "" if LibreOffice did not say
    message: str  # plain-English reason when ok is False
    log: str  # what LibreOffice printed
    short: str = ""  # a few words for the contact sheet when ok is False


class Soffice:
    """Runs LibreOffice in headless mode, one document at a time.

    Each instance uses its own throw-away LibreOffice profile so it never
    clashes with a copy of LibreOffice you have open, and so a crash cannot
    damage your normal settings.
    """

    def __init__(self, soffice: str | None = None, timeout: int = 180):
        self.path = find_soffice(soffice)
        self.timeout = timeout
        self._profile = Path(tempfile.mkdtemp(prefix="publisher-rescue-lo-"))

    # Context-manager support: "with Soffice() as lo:"
    def __enter__(self) -> "Soffice":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        shutil.rmtree(self._profile, ignore_errors=True)

    def _reset_profile(self) -> None:
        """A killed LibreOffice can leave its profile locked; start afresh."""
        shutil.rmtree(self._profile, ignore_errors=True)
        self._profile.mkdir(parents=True, exist_ok=True)

    def _run(self, args: list[str], timeout: int) -> tuple[int, str, bool, float]:
        cmd = [
            self.path, "--headless", "--invisible", "--nologo", "--norestore",
            "--nodefault", "--nolockcheck",
            f"-env:UserInstallation={self._profile.as_uri()}",
            *args,
        ]
        kwargs: dict = {}
        if os.name == "posix":
            kwargs["start_new_session"] = True  # lets us stop every child process
        else:  # Windows
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        start = time.monotonic()
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", **kwargs,
        )
        timed_out = False
        try:
            out, _ = proc.communicate(timeout=timeout)
        except KeyboardInterrupt:  # Ctrl+C: stop LibreOffice too, then stop the script
            self._kill(proc)
            proc.wait()
            raise
        except subprocess.TimeoutExpired:
            timed_out = True
            self._kill(proc)
            try:
                out, _ = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                out = ""
            self._reset_profile()
        return proc.returncode, out or "", timed_out, time.monotonic() - start

    @staticmethod
    def _kill(proc: subprocess.Popen) -> None:
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    def convert(
        self,
        source: Path,
        destination: Path,
        target: str = "pdf",
        infilter: str | None = None,
        timeout: int | None = None,
    ) -> ConvertResult:
        """Convert one file. The original is never touched: LibreOffice works
        on a temporary copy with a plain name, and only a finished output file
        is moved to `destination`."""
        timeout = timeout or self.timeout
        out_ext = target.split(":", 1)[0]
        with tempfile.TemporaryDirectory(prefix="publisher-rescue-job-") as tmp:
            tmp_dir = Path(tmp)
            work_copy = tmp_dir / ("source" + source.suffix.lower())
            shutil.copyfile(source, work_copy)
            out_dir = tmp_dir / "out"
            out_dir.mkdir()
            args = []
            if infilter:
                args.append(f"--infilter={infilter}")
            args += ["--convert-to", target, "--outdir", str(out_dir), str(work_copy)]
            _code, log, timed_out, seconds = self._run(args, timeout)
            log = "\n".join(
                line for line in log.splitlines() if "javaldx" not in line
            ).strip()
            match = re.search(r" as an? (\w+) document", log)
            opened_as = match.group(1) if match else ""
            produced = out_dir / f"source.{out_ext}"
            if timed_out:
                return ConvertResult(False, None, seconds, True, opened_as,
                                     f"LibreOffice was still working after {timeout} "
                                     "seconds and was stopped. The file may be very "
                                     "large or damaged. Try again with a longer "
                                     "--timeout.", log, "Took too long, stopped")
            if not produced.exists() or produced.stat().st_size == 0:
                short = "LibreOffice could not open it"
                if "could not be loaded" in log:
                    message = ("LibreOffice could not open this file. It may be "
                               "damaged, from an unsupported version, or not the "
                               "file type its name suggests.")
                elif log:
                    short = "No PDF was made"
                    message = "LibreOffice did not create an output file: " + log.splitlines()[-1]
                else:
                    short = "No PDF was made"
                    message = "LibreOffice did not create an output file and gave no reason."
                return ConvertResult(False, None, seconds, False, opened_as, message, log, short)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(produced), str(destination))
            return ConvertResult(True, destination, seconds, False, opened_as, "", log)


def pdf_target(ext: str, pdfa: bool) -> str:
    """The --convert-to value for a file type, optionally as PDF/A-2b."""
    module = MODULE_BY_EXT.get(ext.lower().lstrip("."))
    if pdfa and module in PDF_EXPORT_FILTER:
        return f"pdf:{PDF_EXPORT_FILTER[module]}:{PDFA_OPTIONS}"
    return "pdf"


def has_ole_signature(path: Path) -> bool:
    with open(path, "rb") as handle:
        return handle.read(8) == OLE_SIGNATURE


# ---------------------------------------------------------------------------
# Reading PDFs
# ---------------------------------------------------------------------------

@dataclass
class PdfInfo:
    pages: int
    has_text: bool
    snippet: str  # the first words of text, for searching the index
    fonts: list[str]
    creator: str


_SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")


def _clean_font(name: str) -> str:
    name = _SUBSET_PREFIX.sub("", name or "").strip()
    return name


def _snippet(text: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + " ..."


def read_pdf(pdf: Path) -> PdfInfo:
    """Page count, whether there is selectable text, first words, fonts used."""
    if fitz is not None:
        with fitz.open(pdf) as doc:
            text_parts: list[str] = []
            has_text = False
            fonts: set[str] = set()
            for index, page in enumerate(doc):
                page_text = page.get_text("text")
                if page_text.strip():
                    has_text = True
                    if sum(len(t) for t in text_parts) < 600:
                        text_parts.append(page_text)
                for font in doc.get_page_fonts(index):
                    if font[3]:
                        fonts.add(_clean_font(font[3]))
            creator = (doc.metadata or {}).get("creator", "") or ""
            return PdfInfo(doc.page_count, has_text, _snippet(" ".join(text_parts)),
                           sorted(f for f in fonts if f), creator)
    # Fallback: Poppler command-line tools
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages_match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    creator_match = re.search(r"^Creator:\s+(.*)$", info, re.M)
    text = subprocess.run(["pdftotext", "-l", "3", str(pdf), "-"],
                          capture_output=True, text=True).stdout
    font_lines = subprocess.run(["pdffonts", str(pdf)], capture_output=True,
                                text=True).stdout.splitlines()[2:]
    fonts = sorted({_clean_font(line.split()[0]) for line in font_lines if line.strip()})
    return PdfInfo(int(pages_match.group(1)) if pages_match else 0, bool(text.strip()),
                   _snippet(text), fonts,
                   creator_match.group(1).strip() if creator_match else "")


def render_page(pdf: Path, png: Path, width_px: int = 600, page: int = 0) -> None:
    """Save one page of a PDF as a PNG picture `width_px` pixels wide."""
    png.parent.mkdir(parents=True, exist_ok=True)
    if fitz is not None:
        with fitz.open(pdf) as doc:
            pdf_page = doc[page]
            zoom = width_px / pdf_page.rect.width
            pixmap = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            pixmap.save(str(png))
        return
    base = png.with_suffix("")
    subprocess.run(
        ["pdftoppm", "-png", "-f", str(page + 1), "-l", str(page + 1), "-singlefile",
         "-scale-to-x", str(width_px), "-scale-to-y", "-1", str(pdf), str(base)],
        check=True, capture_output=True,
    )


def render_all_pages(pdf: Path, out_dir: Path, width_px: int = 1000) -> list[Path]:
    """Save every page of a PDF as page-01.png, page-02.png, ... in out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = read_pdf(pdf).pages
    written = []
    for index in range(pages):
        target = out_dir / f"page-{index + 1:02d}.png"
        render_page(pdf, target, width_px, index)
        written.append(target)
    return written
