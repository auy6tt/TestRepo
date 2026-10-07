#!/usr/bin/env python3
"""Crawl one website and list every PDF, Word, PowerPoint and Excel file it links to.

Polite by default:
  - reads robots.txt and never fetches what it disallows (supports * and $
    patterns, and honours Crawl-delay)
  - one request at a time, at least --delay seconds apart (default 1 second)
  - stays on the starting site and stops after --max-pages pages
  - identifies itself with a user agent you can set (put your contact in it)

It finds documents three ways: links ending in .pdf, .docx, .xlsx and so on;
links like /DocumentCenter/View/123 that many town website platforms use
(checked by asking the server what type of file it is); and pages that turn
out to be documents when fetched. It also reads <iframe>, <embed> and
<object> tags, and with --sitemap it adds pages listed in the sitemap.

Outputs (in --out):
  documents.csv       one row per document (first page it was found on, how
                      many links point to it, download result)
  document_links.csv  every link to a document, with its link text and a note
                      when the text is unclear ("click here")
  pages.csv           every page fetched or skipped, and why
  crawl_summary.md    the numbers, in plain English
  crawl_summary.json  the same numbers for make_report.py

With --download DIR it saves the documents (on the same site, plus any hosts
named in --also-download-from) so triage_pdfs.py can check them.

Only crawl a client's site after they agree. Before that, keep any check of a
prospect's site light (a few pages, slow rate).

Examples:
  python crawl_documents.py https://www.example-town.gov/ --out crawl --download downloads
  python crawl_documents.py https://www.example-town.gov/ --depth 2 --max-pages 200 --sitemap \\
      --user-agent "DocInventory/1.0 (+mailto:you@example.com)" --out crawl
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import re
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Missing Python package ({exc.name}). Run: pip install -r requirements.txt")

DOC_EXTENSIONS = {
    ".pdf": "PDF",
    ".doc": "Word", ".docx": "Word", ".docm": "Word", ".dot": "Word", ".dotx": "Word", ".rtf": "Word",
    ".odt": "Word", ".wpd": "Word",
    ".ppt": "PowerPoint", ".pptx": "PowerPoint", ".pptm": "PowerPoint", ".pps": "PowerPoint",
    ".ppsx": "PowerPoint", ".odp": "PowerPoint",
    ".xls": "Excel", ".xlsx": "Excel", ".xlsm": "Excel", ".xlsb": "Excel", ".ods": "Excel",
}
CONTENT_TYPES = {
    "application/pdf": ".pdf", "application/x-pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-word.document.macroenabled.12": ".docm",
    "application/rtf": ".rtf", "text/rtf": ".rtf",
    "application/vnd.oasis.opendocument.text": ".odt",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.presentationml.slideshow": ".ppsx",
    "application/vnd.oasis.opendocument.presentation": ".odp",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel.sheet.macroenabled.12": ".xlsm",
    "application/vnd.oasis.opendocument.spreadsheet": ".ods",
}
# Links that often serve a document without a file extension (common on
# local-government website platforms). These are checked with a request.
DOC_URL_HINTS = re.compile(
    r"(documentcenter/view|agendacenter/viewfile|archive\.aspx\?adid=|showpublisheddocument|showdocument|"
    r"/download(/|$|\?)|[?&]download=|viewfile|getfile|filestream|/blobdl|/docs?/\d+)", re.I)
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tif", ".tiff", ".css", ".js",
    ".mp3", ".mp4", ".m4a", ".mov", ".avi", ".wmv", ".webm", ".zip", ".gz", ".tar", ".7z", ".rar", ".exe",
    ".dmg", ".iso", ".woff", ".woff2", ".ttf", ".eot", ".ics", ".vcf", ".xml", ".json", ".txt", ".csv",
}
HTML_TYPES = {"text/html", "application/xhtml+xml"}
VAGUE_LINK_TEXT = {
    "click here", "here", "click", "download", "pdf", "link", "read more", "more", "view", "open", "this",
    "file", "document", "this link", "learn more", "more info", "more information", "details", "view pdf",
    "download pdf", "download here", "go", "see more", "info", "doc", "word", "excel", "attachment",
}
MAX_HTML_BYTES = 5_000_000
DEFAULT_AGENT = "DocumentInventoryBot/1.0 (document accessibility check; set your contact with --user-agent)"


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

def normalize(url: str) -> str:
    url, _ = urldefrag(url.strip())
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    return urlunsplit((scheme, netloc, remove_dot_segments(parts.path or "/"), parts.query, ""))


def remove_dot_segments(path: str) -> str:
    if "/." not in path:
        return path
    out = []
    for segment in path.split("/"):
        if segment == "..":
            if len(out) > 1:
                out.pop()
        elif segment != ".":
            out.append(segment)
    result = "/".join(out)
    if path.endswith(("/.", "/..")):
        result += "/"
    return result if result.startswith("/") else "/" + result


def site_key(netloc: str) -> str:
    return netloc[4:] if netloc.startswith("www.") else netloc


INDEX_FILE = re.compile(r"/(index|default)\.(html?|php|aspx?)$", re.I)


def page_key(url: str) -> str:
    """Treat /folder/ and /folder/index.html as the same page."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, INDEX_FILE.sub("/", parts.path), parts.query, ""))


def extension(url: str) -> str:
    path = unquote(urlsplit(url).path).lower()
    name = path.rsplit("/", 1)[-1]
    return "." + name.rsplit(".", 1)[-1] if "." in name else ""


def doc_type_for(ext: str) -> str:
    return DOC_EXTENSIONS.get(ext, "")


def link_text_note(text: str, url: str) -> str:
    clean = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()
    clean = re.sub(r"\s+", " ", clean)
    if not text.strip():
        return "No link text"
    if clean in VAGUE_LINK_TEXT:
        return f"Unclear link text ('{text.strip()}')"
    if re.match(r"^(https?://|www\.)", text.strip(), re.I):
        return "Link text is a web address"
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?)$", text.strip(), re.I):
        return "Link text is a file name"
    return ""


# ---------------------------------------------------------------------------
# robots.txt (RFC 9309: longest match wins, Allow wins a tie, * and $ patterns)
# ---------------------------------------------------------------------------

class RobotsRules:
    def __init__(self, text: str, product: str):
        self.rules: list[tuple[bool, str]] = []
        self.crawl_delay: float | None = None
        self.sitemaps: list[str] = []
        groups, agents, current, in_rules = [], [], None, False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = (part.strip() for part in line.split(":", 1))
            field = field.lower()
            if field == "sitemap":
                self.sitemaps.append(value)
            elif field == "user-agent":
                if in_rules or current is None:
                    agents, current, in_rules = [], {"rules": [], "delay": None}, False
                    groups.append((agents, current))
                agents.append(value.lower())
            elif field in ("allow", "disallow") and current is not None:
                in_rules = True
                current["rules"].append((field == "allow", value))
            elif field == "crawl-delay" and current is not None:
                in_rules = True
                try:
                    current["delay"] = float(value)
                except ValueError:
                    pass
        product = product.lower()
        chosen = [g for a, g in groups if any(agent != "*" and agent in product for agent in a)]
        if not chosen:
            chosen = [g for a, g in groups if "*" in a]
        for group in chosen:
            self.rules += group["rules"]
            if group["delay"] is not None:
                self.crawl_delay = max(self.crawl_delay or 0, group["delay"])

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        anchored = pattern.endswith("$")
        body = pattern[:-1] if anchored else pattern
        regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in body)
        return re.match(regex + ("$" if anchored else ""), path) is not None

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        best = None
        for allow, pattern in self.rules:
            if not pattern:
                continue  # "Disallow:" with nothing means allow everything
            for candidate in (path, unquote(path)):
                if self._matches(pattern, candidate):
                    length = len(pattern)
                    if best is None or length > best[0] or (length == best[0] and allow):
                        best = (length, allow)
                    break
        return True if best is None else best[1]


class AllowAll:
    rules, crawl_delay, sitemaps = [], None, []

    def allowed(self, url: str) -> bool:
        return True


class DenyAll(AllowAll):
    def allowed(self, url: str) -> bool:
        return False


# ---------------------------------------------------------------------------
# The crawler
# ---------------------------------------------------------------------------

class Crawler:
    def __init__(self, args):
        self.args = args
        self.start = normalize(args.start_url)
        self.site = site_key(urlsplit(self.start).netloc)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = args.user_agent
        self.product = args.user_agent.split("/")[0].split()[0]
        self.robots: dict[str, object] = {}
        self.last_request: dict[str, float] = {}
        self.pages: list[dict] = []
        self.links: list[dict] = []
        self.documents: dict[str, dict] = {}
        self.seen: set[str] = set()
        self.queue: deque = deque()
        self.probed: dict[str, str] = {}
        self.exclude = re.compile(args.exclude, re.I) if args.exclude else None
        self.notes: list[str] = []
        self.beyond_depth: set[str] = set()
        self.counts = {"skipped_robots": 0, "skipped_excluded": 0, "requests": 0, "stopped_at_limit": False}

    # -- helpers -----------------------------------------------------------
    def on_site(self, url: str) -> bool:
        netloc = urlsplit(url).netloc
        key = site_key(netloc)
        if key == self.site:
            return True
        return bool(self.args.include_subdomains and key.endswith("." + self.site))

    def robots_for(self, url: str):
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self.robots:
            rules = AllowAll()
            try:
                self.wait_turn(base)
                response = self.session.get(base + "/robots.txt", timeout=(10, 30))
                self.counts["requests"] += 1
                if response.status_code == 200:
                    rules = RobotsRules(response.text[:600_000], self.product)
                elif response.status_code in (401, 403) or response.status_code >= 500:
                    rules = DenyAll()
                    self.notes.append(f"{base}/robots.txt answered {response.status_code}, so nothing on {base} "
                                      "was fetched. Ask the site owner to allow your crawler, or for a file list.")
            except requests.RequestException as exc:
                self.notes.append(f"Could not read {base}/robots.txt ({exc.__class__.__name__}).")
            self.robots[base] = rules
            if getattr(rules, "crawl_delay", None) and rules.crawl_delay > self.args.delay:
                unit = "second" if rules.crawl_delay == 1 else "seconds"
                self.notes.append(f"{base} asks for {rules.crawl_delay:g} {unit} between requests; the crawler waits that long.")
        return self.robots[base]

    def wait_turn(self, base: str) -> None:
        rules = self.robots.get(base)
        delay = max(self.args.delay, getattr(rules, "crawl_delay", None) or 0)
        last = self.last_request.get(base)
        if last is not None:
            pause = delay - (time.monotonic() - last)
            if pause > 0:
                time.sleep(pause)
        self.last_request[base] = time.monotonic()

    def request(self, url: str, method: str = "GET", stream: bool = True):
        parts = urlsplit(url)
        self.wait_turn(f"{parts.scheme}://{parts.netloc}")
        self.counts["requests"] += 1
        return self.session.request(method, url, timeout=(10, 30), stream=stream, allow_redirects=True)

    @staticmethod
    def content_type(response) -> str:
        return (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()

    @staticmethod
    def filename_from(response) -> str:
        disposition = response.headers.get("Content-Disposition") or ""
        match = re.search(r"filename\*=(?:UTF-8'')?([^;]+)|filename=\"?([^\";]+)\"?", disposition, re.I)
        if match:
            return unquote((match.group(1) or match.group(2) or "").strip().strip('"'))
        return ""

    def doc_ext_from_response(self, response) -> str:
        ext = CONTENT_TYPES.get(self.content_type(response), "")
        if not ext:
            name_ext = extension("/" + self.filename_from(response))
            if name_ext in DOC_EXTENSIONS:
                ext = name_ext
        return ext

    # -- recording ---------------------------------------------------------
    def record_document(self, url: str, ext: str, found_on: str, depth: int, text: str, element: str,
                        filename: str = "") -> None:
        doc_type = doc_type_for(ext) or "Unknown"
        note = link_text_note(text, url) if element == "a" else ""
        self.links.append({"document_url": url, "file_type": ext.lstrip(".").upper() or "?", "type_group": doc_type,
                           "found_on": found_on, "found_on_depth": depth, "link_text": text, "element": element,
                           "link_text_note": note})
        doc = self.documents.get(url)
        if doc is None:
            doc = {"doc_id": len(self.documents) + 1, "url": url, "file_type": ext.lstrip(".").upper() or "?",
                   "type_group": doc_type, "on_site": "Yes" if self.on_site(url) else "No",
                   "first_found_on": found_on, "found_on_depth": depth, "first_link_text": text,
                   "times_linked": 0, "pages": set(), "http_status": "", "content_type": "", "size_bytes": "",
                   "last_modified": "", "saved_as": "", "server_filename": filename, "note": ""}
            self.documents[url] = doc
        doc["times_linked"] += 1
        doc["pages"].add(found_on)
        if depth < doc["found_on_depth"]:
            doc["found_on_depth"] = depth
        if not doc["first_link_text"] and text:
            doc["first_link_text"] = text

    def add_page(self, url: str, depth: int, status="", ctype="", title="", docs=0, note="") -> None:
        self.pages.append({"url": url, "depth": depth, "status": status, "content_type": ctype, "title": title,
                           "documents_linked": docs, "note": note})

    # -- crawling ----------------------------------------------------------
    def probe(self, url: str) -> tuple[str, str]:
        """Ask the server what an extension-less link is. Returns (doc ext or '', content type)."""
        if url in self.probed:
            return self.probed[url], ""
        ext, ctype = "", ""
        try:
            response = self.request(url, "HEAD", stream=False)
            if response.status_code in (405, 501) or not self.content_type(response):
                response = self.request(url, "GET", stream=True)
                response.close()
            ctype = self.content_type(response)
            ext = self.doc_ext_from_response(response)
        except requests.RequestException:
            pass
        self.probed[url] = ext
        return ext, ctype

    def handle_link(self, url: str, text: str, element: str, page_url: str, depth: int) -> int:
        """Returns 1 if the link is a document."""
        if not url.startswith(("http://", "https://")):
            return 0
        ext = extension(url)
        if ext in DOC_EXTENSIONS:
            self.record_document(url, ext, page_url, depth, text, element)
            return 1
        if ext in SKIP_EXTENSIONS or not self.on_site(url):
            return 0
        if self.exclude and self.exclude.search(url):
            self.counts["skipped_excluded"] += 1
            return 0
        key = page_key(url)
        if DOC_URL_HINTS.search(url) and key not in self.seen:
            if not self.robots_for(url).allowed(url):
                self.record_document(url, "", page_url, depth, text, element)
                self.documents[url]["note"] = "Blocked by robots.txt (type not checked)"
                return 1
            doc_ext, _ = self.probe(url)
            if doc_ext:
                self.record_document(url, doc_ext, page_url, depth, text, element)
                return 1
        if key in self.seen:
            return 0
        if depth + 1 > self.args.depth:
            self.beyond_depth.add(key)
            return 0
        self.seen.add(key)
        self.queue.append((url, depth + 1, page_url, text))
        return 0

    def parse_page(self, url: str, body: bytes, charset: str | None, depth: int) -> tuple[str, int]:
        soup = BeautifulSoup(body, "html.parser", from_encoding=charset)
        base = url
        base_tag = soup.find("base", href=True)
        if base_tag:
            base = urljoin(url, base_tag["href"])
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        docs = 0
        for tag in soup.find_all(["a", "area", "iframe", "embed", "object"]):
            attr = {"a": "href", "area": "href", "iframe": "src", "embed": "src", "object": "data"}[tag.name]
            raw = tag.get(attr)
            if not raw or raw.strip().lower().startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
                continue
            target = normalize(urljoin(base, raw))
            if tag.name in ("a", "area"):
                text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
                if not text:
                    image = tag.find("img", alt=True)
                    text = tag.get("aria-label") or tag.get("title") or (image["alt"] if image else "") or ""
                docs += self.handle_link(target, text.strip(), "a", url, depth)
            else:
                docs += self.handle_link(target, f"(embedded {tag.name}) {tag.get('title', '')}".strip(), tag.name, url, depth)
        return title, docs

    def fetch_page(self, url: str, depth: int, referrer: str, link_text: str) -> None:
        if not self.robots_for(url).allowed(url):
            self.counts["skipped_robots"] += 1
            self.add_page(url, depth, note="Blocked by robots.txt (not fetched)")
            return
        try:
            response = self.request(url)
        except requests.RequestException as exc:
            self.add_page(url, depth, note=f"Error: {exc.__class__.__name__}")
            if depth == 0:
                self.notes.append(
                    f"Could not reach the start page ({exc.__class__.__name__}). In a Claude Code cloud session this "
                    "usually means the environment's network policy blocks the site: allow the client's domains under "
                    "Network access in the environment settings (see the kit README), then run the crawl again.")
            return
        final = normalize(response.url)
        ctype = self.content_type(response)
        doc_ext = self.doc_ext_from_response(response)
        if doc_ext:
            response.close()
            self.record_document(url, doc_ext, referrer, max(depth - 1, 0), link_text, "a", self.filename_from(response))
            doc = self.documents[url]
            doc["http_status"], doc["content_type"] = response.status_code, ctype
            self.add_page(url, depth, response.status_code, ctype, note="This link is a document")
            return
        if response.status_code >= 400:
            response.close()
            self.add_page(url, depth, response.status_code, ctype, note="Broken page link")
            return
        if ctype not in HTML_TYPES:
            response.close()
            self.add_page(url, depth, response.status_code, ctype, note="Not a web page or document")
            return
        if final != url and not self.on_site(final):
            if depth == 0:
                self.site = site_key(urlsplit(final).netloc)
                self.notes.append(f"The start page redirects to {final}; that site was crawled instead.")
            else:
                response.close()
                self.add_page(url, depth, response.status_code, ctype, note=f"Redirects off the site to {final}")
                return
        body = response.raw.read(MAX_HTML_BYTES, decode_content=True)
        response.close()
        match = re.search(r"charset=[\"']?([\w.-]+)", response.headers.get("Content-Type") or "", re.I)
        self.seen.add(page_key(final))
        title, docs = self.parse_page(final, body, match.group(1) if match else None, depth)
        self.add_page(final, depth, response.status_code, ctype, title, docs,
                      note="" if final == url else f"Redirected from {url}")
        pages_done = sum(1 for p in self.pages if p["content_type"] in HTML_TYPES)
        print(f"[{pages_done}/{self.args.max_pages}] depth {depth}  {response.status_code}  {final}  ({docs} document links)",
              file=sys.stderr)

    def sitemap_urls(self) -> list[str]:
        rules = self.robots_for(self.start)
        parts = urlsplit(self.start)
        to_read = list(getattr(rules, "sitemaps", [])) or [f"{parts.scheme}://{parts.netloc}/sitemap.xml"]
        found, read = [], 0
        while to_read and read < 20:
            sitemap = to_read.pop(0)
            read += 1
            if not self.robots_for(sitemap).allowed(sitemap):
                continue
            try:
                response = self.request(sitemap, stream=False)
                if response.status_code != 200:
                    continue
                data = response.content[:50_000_000]
                if sitemap.endswith(".gz") or data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)
                root = ET.fromstring(data)
            except Exception as exc:
                self.notes.append(f"Could not read sitemap {sitemap} ({exc.__class__.__name__}).")
                continue
            for loc in root.iter():
                if loc.tag.endswith("loc") and loc.text:
                    url = loc.text.strip()
                    if not url.startswith(("http://", "https://")):
                        continue
                    if root.tag.endswith("sitemapindex"):
                        to_read.append(url)
                    else:
                        found.append(normalize(url))
        return found

    def run(self) -> None:
        self.seen.add(page_key(self.start))
        self.queue.append((self.start, 0, "", ""))
        if self.args.sitemap:
            for url in self.sitemap_urls():
                if extension(url) in DOC_EXTENSIONS:
                    self.record_document(url, extension(url), "(sitemap)", 1, "", "sitemap")
                elif self.on_site(url) and page_key(url) not in self.seen and not (self.exclude and self.exclude.search(url)):
                    self.seen.add(page_key(url))
                    self.queue.append((url, min(1, self.args.depth), "(sitemap)", ""))
        try:
            while self.queue:
                if sum(1 for p in self.pages if p["content_type"] in HTML_TYPES) >= self.args.max_pages:
                    self.counts["stopped_at_limit"] = True
                    self.notes.append(f"Stopped at the page limit ({self.args.max_pages}). "
                                      f"{len(self.queue)} pages were still waiting.")
                    break
                url, depth, referrer, text = self.queue.popleft()
                self.fetch_page(url, depth, referrer, text)
        except KeyboardInterrupt:
            self.notes.append("Stopped early by the user (Ctrl+C). The lists are incomplete.")

    # -- downloading -------------------------------------------------------
    def download_all(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        extra_hosts = {h.strip().lower() for h in (self.args.also_download_from or "").split(",") if h.strip()}
        used = {p.name.lower() for p in folder.iterdir()}
        if used:
            self.notes.append(f"The download folder {folder} was not empty. New files with the same name as old "
                              "ones got a number added. Use an empty folder for a clean run.")
        limit = self.args.max_file_mb * 1024 * 1024
        for number, doc in enumerate(self.documents.values(), start=1):
            if doc["saved_as"] or doc["note"]:
                continue
            host = urlsplit(doc["url"]).hostname or ""
            if doc["on_site"] == "No" and host not in extra_hosts:
                doc["note"] = "Off-site link: not downloaded (add the host with --also-download-from if it is the client's)"
                continue
            if not self.robots_for(doc["url"]).allowed(doc["url"]):
                doc["note"] = "Blocked by robots.txt: not downloaded"
                continue
            try:
                response = self.request(doc["url"])
            except requests.RequestException as exc:
                doc["note"] = f"Download failed ({exc.__class__.__name__})"
                continue
            doc["http_status"] = response.status_code
            doc["content_type"] = self.content_type(response)
            doc["last_modified"] = response.headers.get("Last-Modified", "")
            if response.status_code >= 400:
                response.close()
                doc["note"] = f"Broken link (HTTP {response.status_code})"
                continue
            if doc["content_type"] in HTML_TYPES:
                response.close()
                doc["note"] = "Link returns a web page, not a document (possibly a broken link)"
                continue
            ext = self.doc_ext_from_response(response) or extension(doc["url"])
            if ext in DOC_EXTENSIONS and doc["file_type"] in ("?", ""):
                doc["file_type"], doc["type_group"] = ext.lstrip(".").upper(), doc_type_for(ext)
            size = int(response.headers.get("Content-Length") or 0)
            if size > limit:
                response.close()
                doc["note"] = f"Larger than {self.args.max_file_mb} MB: not downloaded"
                continue
            name = self.filename_from(response) or unquote(urlsplit(doc["url"]).path.rstrip("/").rsplit("/", 1)[-1])
            name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .") or f"document-{doc['doc_id']}"
            if extension("/" + name) != ext and ext:
                name += ext
            stem, suffix = name.rsplit(".", 1) if "." in name else (name, "")
            candidate, counter = name, 2
            while candidate.lower() in used:
                candidate = f"{stem}-{counter}.{suffix}" if suffix else f"{stem}-{counter}"
                counter += 1
            used.add(candidate.lower())
            written, too_big = 0, False
            with open(folder / candidate, "wb") as handle:
                for chunk in response.iter_content(65536):
                    written += len(chunk)
                    if written > limit:
                        too_big = True
                        break
                    handle.write(chunk)
            response.close()
            if too_big:
                (folder / candidate).unlink(missing_ok=True)
                doc["note"] = f"Larger than {self.args.max_file_mb} MB: not downloaded"
                continue
            doc["saved_as"], doc["size_bytes"] = candidate, written
            print(f"[download {number}/{len(self.documents)}] {candidate}", file=sys.stderr)

    # -- output ------------------------------------------------------------
    def write(self, out: Path, started: dt.datetime) -> dict:
        out.mkdir(parents=True, exist_ok=True)
        doc_fields = ["doc_id", "url", "file_type", "type_group", "on_site", "first_found_on", "found_on_depth",
                      "first_link_text", "times_linked", "linked_from_pages", "http_status", "content_type",
                      "size_bytes", "last_modified", "saved_as", "note"]
        with open(out / "documents.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=doc_fields, extrasaction="ignore")
            writer.writeheader()
            for doc in self.documents.values():
                writer.writerow({**doc, "linked_from_pages": len(doc["pages"])})
        with open(out / "document_links.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["document_url", "file_type", "type_group", "found_on",
                                                        "found_on_depth", "link_text", "link_text_note", "element"])
            writer.writeheader()
            writer.writerows(self.links)
        with open(out / "pages.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["url", "depth", "status", "content_type", "title",
                                                        "documents_linked", "note"])
            writer.writeheader()
            writer.writerows(self.pages)

        # The shortest wait the crawler left between two requests to the same host:
        # --delay, or the host's robots.txt Crawl-delay when that is longer.
        waits = [max(self.args.delay, getattr(self.robots.get(base), "crawl_delay", None) or 0)
                 for base in self.last_request]
        effective_delay = min(waits) if waits else self.args.delay
        docs = list(self.documents.values())
        by_type = {}
        for doc in docs:
            by_type[doc["type_group"]] = by_type.get(doc["type_group"], 0) + 1
        summary = {
            "start_url": self.start, "date": started.date().isoformat(),
            "started": started.isoformat(timespec="seconds"),
            "finished": dt.datetime.now().isoformat(timespec="seconds"),
            "depth": self.args.depth, "delay_seconds": self.args.delay,
            "effective_delay_seconds": effective_delay, "max_pages": self.args.max_pages,
            "user_agent": self.args.user_agent, "used_sitemap": bool(self.args.sitemap),
            "pages_crawled": sum(1 for p in self.pages if p["content_type"] in HTML_TYPES and str(p["status"]).startswith("2")),
            "pages_blocked_by_robots": self.counts["skipped_robots"],
            "links_beyond_depth": len(self.beyond_depth - self.seen),
            "links_excluded": self.counts["skipped_excluded"],
            "requests": self.counts["requests"], "stopped_at_page_limit": self.counts["stopped_at_limit"],
            "documents_found": len(docs), "document_links": len(self.links), "by_type": by_type,
            "off_site_documents": sum(1 for d in docs if d["on_site"] == "No"),
            "downloaded": sum(1 for d in docs if d["saved_as"]),
            "broken_links": sum(1 for d in docs if str(d["http_status"]).startswith(("4", "5"))),
            "blocked_by_robots": sum(1 for d in docs if "robots" in d["note"].lower()),
            "unclear_link_text": sum(1 for link in self.links if link["link_text_note"]),
            "broken_pages": sum(1 for p in self.pages if str(p["status"]).startswith(("4", "5"))),
            "notes": self.notes,
        }
        (out / "crawl_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        lines = [f"# Crawl summary: {self.start}", "",
                 f"Crawled on {summary['date']} ({summary['started']} to {summary['finished']}), up to {self.args.depth} "
                 f"clicks from the start page, one request every {effective_delay:g} "
                 f"{'second' if effective_delay == 1 else 'seconds'} or slower, "
                 f"following robots.txt.", "", "| Measure | Count |", "|---|---|"]
        for label, key in [("Web pages read", "pages_crawled"), ("Documents found", "documents_found"),
                           ("Links to documents", "document_links"), ("Documents downloaded", "downloaded"),
                           ("Documents on other sites (not downloaded)", "off_site_documents"),
                           ("Broken document links", "broken_links"),
                           ("Documents blocked by robots.txt", "blocked_by_robots"),
                           ("Pages blocked by robots.txt", "pages_blocked_by_robots"),
                           ("Links with unclear text (like 'click here')", "unclear_link_text"),
                           ("Broken page links", "broken_pages"),
                           ("Pages not visited (deeper than the depth limit)", "links_beyond_depth")]:
            lines.append(f"| {label} | {summary[key]} |")
        lines += ["", "Documents by type: " + (", ".join(f"{k} {v}" for k, v in sorted(by_type.items())) or "none"), ""]
        if self.notes:
            lines += ["## Notes", ""] + [f"- {note}" for note in self.notes] + [""]
        lines += ["## Limits", "",
                  "- Only documents linked from pages the crawler could reach are listed. Files behind logins, "
                  "inside search tools, or loaded by JavaScript may be missing. Ask the client for any document "
                  "libraries or agenda systems the crawl cannot see.",
                  "- Off-site documents are listed but not downloaded unless their host is named with "
                  "--also-download-from.", ""]
        (out / "crawl_summary.md").write_text("\n".join(lines), encoding="utf-8")
        return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List every PDF, Word, PowerPoint and Excel file a website links to.")
    parser.add_argument("start_url", help="the page to start from, usually the home page")
    parser.add_argument("--out", default="crawl", help="output folder (default: %(default)s)")
    parser.add_argument("--depth", type=int, default=3, help="how many clicks from the start page to follow (default: 3)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default: 1; robots.txt "
                        "Crawl-delay is used if it is longer)")
    parser.add_argument("--max-pages", type=int, default=500, help="stop after this many web pages (default: 500)")
    parser.add_argument("--download", metavar="DIR", help="download the documents into this folder")
    parser.add_argument("--also-download-from", metavar="HOSTS", help="other hosts whose documents are the client's, "
                        "comma separated (for example a file storage host)")
    parser.add_argument("--max-file-mb", type=int, default=100, help="skip downloads bigger than this (default: 100)")
    parser.add_argument("--sitemap", action="store_true", help="also crawl pages listed in the site's sitemap")
    parser.add_argument("--include-subdomains", action="store_true", help="treat subdomains as the same site")
    parser.add_argument("--exclude", metavar="REGEX", help="skip page URLs matching this pattern (e.g. 'calendar|/events/')")
    parser.add_argument("--user-agent", default=DEFAULT_AGENT, help="how the crawler identifies itself; include "
                        "your email, e.g. 'DocInventory/1.0 (+mailto:you@example.com)'")
    args = parser.parse_args(argv)
    if not args.start_url.startswith(("http://", "https://")):
        args.start_url = "https://" + args.start_url

    started = dt.datetime.now().replace(microsecond=0)
    crawler = Crawler(args)
    print(f"Crawling {crawler.start} (depth {args.depth}, {args.delay:g} s between requests)...", file=sys.stderr)
    crawler.run()
    if args.download:
        crawler.download_all(Path(args.download))
    summary = crawler.write(Path(args.out), started)
    print(f"\nPages read: {summary['pages_crawled']}  |  documents found: {summary['documents_found']}  |  "
          f"downloaded: {summary['downloaded']}  |  broken document links: {summary['broken_links']}  |  "
          f"blocked by robots.txt: {summary['blocked_by_robots']}")
    for note in summary["notes"]:
        print(f"Note: {note}")
    print(f"Wrote documents.csv, document_links.csv, pages.csv and crawl_summary.md to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
