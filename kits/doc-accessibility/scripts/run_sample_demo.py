#!/usr/bin/env python3
"""Run the whole service on the fictional Town of Fernwick sample site.

1. Serves samples/town-site on a local web server (http://127.0.0.1:8765/).
2. Crawls it and downloads the documents      -> samples/crawl, samples/downloads
3. Triages the documents                       -> samples/inventory
4. Fills the snapshot report (Word and PDF)    -> samples/report
5. Applies safe fixes, with OCR if available   -> samples/fixes/basic-fixes
6. Rebuilds the council agenda from Word as a
   tagged PDF and compares before and after    -> samples/fixes/before-after
7. Fills a remediation log for the fixed files -> samples/fixes/remediation-log-sample.xlsx

Run build_samples.py first if samples/town-site does not exist (or pass --rebuild).

  python run_sample_demo.py              run everything
  python run_sample_demo.py --serve-only just serve the sample site, to try the crawler by hand
"""
from __future__ import annotations

import argparse
import functools
import json
import shutil
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

SCRIPTS = Path(__file__).resolve().parent
KIT = SCRIPTS.parent
SAMPLES = KIT / "samples"
SITE = SAMPLES / "town-site"
PYTHON = sys.executable
CLIENT = "Town of Fernwick (fictional)"


class SampleSiteHandler(SimpleHTTPRequestHandler):
    """Static files, plus two things a plain file server cannot do: fill in the
    real address in robots.txt and sitemap.xml, and serve a document from a link
    with no file extension (like /DocumentCenter/View/2041/...)."""

    base_url = ""
    routes: dict = {}

    def log_message(self, *args):  # keep the console quiet
        pass

    def do_GET(self):
        self.serve(head=False)

    def do_HEAD(self):
        self.serve(head=True)

    def serve(self, head: bool) -> None:
        path = urlsplit(self.path).path
        if path in self.routes:
            route = self.routes[path]
            data = (SITE / route["file"]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", route["type"])
            self.send_header("Content-Disposition", f'inline; filename="{route["filename"]}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if not head:
                self.wfile.write(data)
            return
        if path in ("/robots.txt", "/sitemap.xml"):
            data = (SITE / path.lstrip("/")).read_text(encoding="utf-8").replace("{{BASE_URL}}", self.base_url).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8" if path.endswith(".txt") else "application/xml")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if not head:
                self.wfile.write(data)
            return
        if path == "/routes.json":
            self.send_error(404)
            return
        if head:
            super().do_HEAD()
        else:
            super().do_GET()


def start_server(port: int) -> tuple[ThreadingHTTPServer, str]:
    handler = functools.partial(SampleSiteHandler, directory=str(SITE))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    SampleSiteHandler.base_url = base
    SampleSiteHandler.routes = json.loads((SITE / "routes.json").read_text(encoding="utf-8"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, base


def run(step: str, args: list[str]) -> None:
    print(f"\n=== {step} ===\n$ python {' '.join(args)}", flush=True)
    result = subprocess.run([PYTHON, *args], cwd=KIT)
    if result.returncode != 0:
        sys.exit(f"Step failed: {step}")


def fresh(folder: Path) -> Path:
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full process on the fictional sample site.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--serve-only", action="store_true", help="only serve the sample site until Ctrl+C")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the sample site first (build_samples.py)")
    args = parser.parse_args()

    if args.rebuild or not SITE.exists():
        run("Build the sample site", ["scripts/build_samples.py"])
    server, base = start_server(args.port)
    print(f"Sample site running at {base}")
    if args.serve_only:
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            server.shutdown()
            return 0

    for folder in ("crawl", "downloads", "inventory", "report", "fixes"):
        fresh(SAMPLES / folder)
    run("1. Crawl the site and download the documents",
        ["scripts/crawl_documents.py", base, "--out", "samples/crawl", "--download", "samples/downloads",
         "--depth", "3", "--delay", "0.2", "--sitemap",
         "--user-agent", "DocInventory/1.0 (+mailto:you@example.com)"])
    run("2. Triage the documents",
        ["scripts/triage_pdfs.py", "samples/downloads", "--crawl", "samples/crawl/documents.csv",
         "--out", "samples/inventory", "--client", CLIENT])
    run("3. Fill the snapshot report",
        ["scripts/make_report.py", "--inventory", "samples/inventory/inventory.xlsx",
         "--crawl-summary", "samples/crawl/crawl_summary.json", "--client", CLIENT,
         "--prepared-by", "Your Name, Document Accessibility Services", "--sector", "us-public",
         "--out", "samples/report/fernwick-document-snapshot.docx", "--pdf"])
    run("4. Safe automatic fixes (title, language, OCR)",
        ["scripts/fix_basics.py", "samples/downloads", "--out", "samples/fixes/basic-fixes",
         "--crawl", "samples/crawl/documents.csv", "--inventory", "samples/inventory/inventory.xlsx",
         "--lang", "en-US", "--ocr"])
    before_after = fresh(SAMPLES / "fixes" / "before-after")
    shutil.copy(SAMPLES / "downloads" / "council-agenda-2026-03-10.pdf", fresh(before_after / "before"))
    shutil.copy(SAMPLES / "source-files" / "council-agenda-2026-03-10.docx", fresh(before_after / "rebuilt-word-file"))
    run("5. Rebuild the agenda from a structured Word file and compare",
        ["scripts/docx_to_tagged_pdf.py", "samples/fixes/before-after/rebuilt-word-file/council-agenda-2026-03-10.docx",
         "--out", "samples/fixes/before-after/after",
         "--compare", "samples/fixes/before-after/before/council-agenda-2026-03-10.pdf", "--validate"])
    shutil.move(str(before_after / "after" / "comparison.md"), str(before_after / "comparison.md"))
    from validate_pdfs import find_verapdf
    if find_verapdf():
        run("6. veraPDF checks on the before and after files",
            ["scripts/validate_pdfs.py", "samples/fixes/before-after/before", "samples/fixes/before-after/after",
             "--out", "samples/fixes/before-after"])
    else:
        print("\nveraPDF is not installed, so the validation step was skipped (bash scripts/setup.sh --verapdf).")
    run("7. Fill a sample remediation log (automated columns only)",
        ["scripts/make_remediation_log.py", "--before", "samples/fixes/before-after/before",
         "--after", "samples/fixes/before-after/after", "--crawl", "samples/crawl/documents.csv",
         "--work", "Rebuilt in Word with real headings and lists, title and language set; exported a tagged PDF "
                   "with LibreOffice (PDF/UA option on)",
         "--tools", "Word file, LibreOffice, veraPDF", "--validate",
         "--out", "samples/fixes/remediation-log-sample.xlsx"])
    run("7b. Add the files that only got basic fixes",
        ["scripts/make_remediation_log.py", "--before", "samples/downloads", "--after", "samples/fixes/basic-fixes",
         "--fix-log", "samples/fixes/basic-fixes/fix-log.csv", "--crawl", "samples/crawl/documents.csv",
         "--validate", "--append", "--out", "samples/fixes/remediation-log-sample.xlsx"])
    server.shutdown()
    print("\nDone. Open samples/report/fernwick-document-snapshot.pdf and samples/inventory/inventory.xlsx.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(SCRIPTS))
    sys.exit(main())
