#!/usr/bin/env python3
"""
Check a list of official sources for changes since the last run.

For each source listed in sources.yaml this script:

  1. checks the site's robots.txt and skips the page if robots.txt says no
  2. downloads it politely: a user agent with your contact details, a pause
     between requests to the same site, and "only send it if it changed"
     headers so unchanged files are not downloaded again
  3. turns the web page, PDF, JSON data or RSS/Atom feed into normalised text
  4. compares that text with the snapshot saved on the previous run
  5. records what changed: added and removed lines, new links, new records,
     and the text of new linked documents (if you ask it to follow them)

It writes changes.json (for Claude Code and other scripts) and changes.md
(for you to read). Snapshots are kept in the data folder, so the next run
compares against this one. If you run this in a cloud session or a Routine,
commit and push the data folder: every new cloud session starts from a fresh
copy of the repository.

Examples (run from the kits/weekly-digest folder):

  .venv/bin/python scripts/watch_sources.py digests/ohio-bess/sources.yaml
  .venv/bin/python scripts/watch_sources.py digests/ohio-bess --only "Tarrow County"
  .venv/bin/python scripts/watch_sources.py digests/ohio-bess --dry-run

The sources.yaml format is explained in README.md and in the examples in
templates/sources/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

try:
    import feedparser
    import requests
    import yaml
    from bs4 import BeautifulSoup
    from bs4.element import (Comment, Declaration, Doctype, NavigableString,
                             ProcessingInstruction)
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - message for the user
    sys.exit(
        f"Missing Python package: {exc.name}\n"
        "Run the kit's scripts with its own Python, .venv/bin/python. To set it up, run\n"
        "  bash kits/setup.sh weekly-digest      (from the repository root), or\n"
        "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   (from kits/weekly-digest)"
    )

VERSION = "1.0"
TYPES = ("html", "pdf", "json", "rss")

DEFAULT_SETTINGS = {
    # Sites see this in their logs. Put your real contact email in it.
    "user_agent": "WeeklyDigestWatcher/1.0 (+mailto:you@example.com)",
    "delay_seconds": 5.0,        # pause between requests to the same site
    "timeout_seconds": 30.0,
    "max_megabytes": 25.0,       # refuse files bigger than this
    "keep_history": 8,           # old snapshots kept per source
    "max_diff_lines": 150,       # longer diffs are cut in changes.json
    "max_follow_per_source": 3,  # new linked documents fetched per source
    "keywords": [],              # highlight (html/pdf) or filter (json/rss)
}

SOURCE_FIELDS = {
    "name", "id", "url", "type", "selector", "exclude_selector", "tags",
    "keywords", "ignore_patterns", "follow_new_links", "items_path",
    "id_field", "fields", "link_field", "skip_records_where", "report_removed",
    "notes", "terms_checked", "enabled",
}

ACCEPT = {
    "html": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
    "pdf": "application/pdf,*/*;q=0.5",
    "json": "application/json,*/*;q=0.5",
    "rss": "application/rss+xml,application/atom+xml,application/xml;q=0.9,"
           "text/xml;q=0.8,*/*;q=0.5",
}

PLACEHOLDER_HOSTS = ("example.gov", "example.com", "example.org", "example.net")
DEFAULT_FOLLOW_PATTERN = r"\.pdf($|[?#])"
MAX_LIST_ITEMS = 200      # cap for added/removed lines and record lists
EXCERPT_LINES = 40
EXCERPT_CHARS = 2000

REVIEW_REMINDER = (
    "Draft items from the changed sources with status needs_review. A person "
    "must check every item against its source before anything is sent."
)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def week_label(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "source"


_SPACES = re.compile(r"\s+")
_PIPES = re.compile(r"(?:\s*\|\s*)+")
_INVISIBLE = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)


def normalise_line(text: str) -> str:
    """One tidy line: Unicode normalised, single spaces, table cells joined by |."""
    text = unicodedata.normalize("NFKC", str(text)).translate(_INVISIBLE)
    text = _SPACES.sub(" ", text)
    text = _PIPES.sub(" | ", text)
    return text.strip().strip("|").strip()


def normalise_lines(lines) -> list[str]:
    out = []
    for line in lines:
        line = normalise_line(line)
        if line:
            out.append(line)
    return out


def link_kind(url: str) -> str:
    path = urlsplit(url).path.lower()
    for ext, kind in ((".pdf", "pdf"), (".docx", "word"), (".doc", "word"),
                      (".xlsx", "excel"), (".xls", "excel"), (".csv", "csv"),
                      (".zip", "zip"), (".json", "json"), (".xml", "xml")):
        if path.endswith(ext):
            return kind
    return "page"


def keyword_regex(keyword: str) -> re.Pattern:
    """Whole-word, case-insensitive match. 'batter*' matches battery and batteries."""
    pattern = re.escape(keyword.strip()).replace(r"\*", r"\w*")
    return re.compile(r"(?<![A-Za-z0-9])" + pattern + r"(?:s|es)?(?![A-Za-z0-9])",
                      re.IGNORECASE)


def find_keywords(texts, keywords) -> list[str]:
    hits = []
    for keyword in keywords:
        rx = keyword_regex(keyword)
        if any(rx.search(text) for text in texts if text):
            hits.append(keyword)
    return hits


def dig(data, path: str | None):
    """Follow a dotted path such as 'data.items' or 'features.0.attributes'."""
    if not path:
        return data
    for part in str(path).split("."):
        if isinstance(data, list) and part.isdigit():
            index = int(part)
            data = data[index] if index < len(data) else None
        elif isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data


def plural(count: int, word: str, words: str | None = None) -> str:
    return f"{count} {word if count == 1 else (words or word + 's')}"


def short(value, limit: int = 300) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    value = normalise_line(value)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def is_placeholder(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return (host in PLACEHOLDER_HOSTS
            or any(host.endswith("." + h) for h in PLACEHOLDER_HOSTS)
            or host.endswith(".example") or host == "example")


# --------------------------------------------------------------------------
# robots.txt (RFC 9309)
# --------------------------------------------------------------------------

class RobotsRules:
    """robots.txt rules for one site.

    Follows RFC 9309: the group for our product token (or '*' if there is
    none), '*' and '$' wildcards, and the longest matching rule wins (Allow
    wins a tie). Python's built-in robotparser ignores wildcards, so this
    small parser is used instead.
    """

    def __init__(self, text: str, user_agent: str):
        self.rules: list[tuple[bool, str]] = []
        self.crawl_delay: float | None = None
        token = user_agent.split("/")[0].strip().lower()
        groups: list[dict] = []
        current = None
        last_was_agent = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key, value = key.strip().lower(), value.strip()
            if key == "user-agent":
                if current is None or not last_was_agent:
                    current = {"agents": [], "rules": [], "delay": None}
                    groups.append(current)
                current["agents"].append(value.split("/")[0].strip().lower())
                last_was_agent = True
                continue
            if key in ("allow", "disallow") and current is not None:
                current["rules"].append((key == "allow", value))
            elif key == "crawl-delay" and current is not None:
                try:
                    current["delay"] = float(value)
                except ValueError:
                    pass
            last_was_agent = False
        chosen = [g for g in groups if token and token in g["agents"]]
        if not chosen:
            chosen = [g for g in groups if "*" in g["agents"]]
        for group in chosen:
            self.rules.extend(group["rules"])
            if group["delay"] is not None:
                self.crawl_delay = max(self.crawl_delay or 0.0, group["delay"])

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        anchored = pattern.endswith("$")
        if anchored:
            pattern = pattern[:-1]
        regex = ".*".join(re.escape(part) for part in pattern.split("*"))
        return re.match("^" + regex + ("$" if anchored else ""), path) is not None

    def allows(self, url: str) -> bool:
        parts = urlsplit(url)
        path = unquote(parts.path or "/")
        if parts.query:
            path += "?" + unquote(parts.query)
        if path == "/robots.txt":
            return True
        best = None
        for allow, pattern in self.rules:
            if not pattern:
                continue  # an empty Disallow means "nothing is disallowed"
            pattern = unquote(pattern)
            if self._matches(pattern, path):
                length = len(pattern)
                if best is None or length > best[0] or (length == best[0] and allow):
                    best = (length, allow)
        return True if best is None else best[1]


# --------------------------------------------------------------------------
# Polite downloads
# --------------------------------------------------------------------------

class FetchError(Exception):
    """A download problem, with a plain-English hint for the person."""

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


@dataclass
class Response:
    status_code: int
    headers: dict
    content: bytes
    url: str


def network_hint(host: str) -> str:
    return (f"This environment's network policy blocked {host}. Open the environment "
            "settings (cloud icon above the message box, then the settings icon), "
            "set Network access to Custom (called Limited in newer apps), add the "
            "domain under Allowed domains and keep the default package-manager "
            "list ticked. A Routine uses its own environment: edit that one too.")


def describe_network_error(exc: Exception, host: str) -> tuple[str, str]:
    text = str(exc)
    if isinstance(exc, requests.exceptions.ProxyError) or "Tunnel connection failed" in text:
        if " 403" in text or " 407" in text:
            return f"Blocked by the network policy ({host})", network_hint(host)
        return ("Could not connect through the network proxy",
                "Try again later. If it keeps failing, check the environment's network settings.")
    if isinstance(exc, requests.exceptions.SSLError):
        return ("The secure (TLS) connection failed",
                "The site's certificate could not be checked. Do not turn checking off; "
                "try again later or confirm the address in a browser.")
    if isinstance(exc, requests.exceptions.Timeout):
        return ("The site did not answer in time",
                "Try again later, or raise timeout_seconds in settings.")
    if isinstance(exc, requests.exceptions.TooManyRedirects):
        return ("Too many redirects",
                "Open the address in a browser and put the final address in sources.yaml.")
    if isinstance(exc, requests.exceptions.ConnectionError):
        return ("Could not connect to the site",
                "Check the address. If the site is down the watcher will try again next run. "
                "In a cloud session, use https:// addresses.")
    return f"Download failed ({exc.__class__.__name__})", ""


def http_status_problem(status: int) -> tuple[str, str]:
    if status in (404, 410):
        return (f"Page not found (HTTP {status})",
                "The site may have moved or removed it. Find the new address on the "
                "site, update sources.yaml, and check the page by hand this week.")
    if status in (401, 403):
        return (f"The site refused access (HTTP {status})",
                "Do not try to get around this. Look for an official RSS feed, API or "
                "open-data version, or ask the agency. Check the page by hand this week.")
    if status == 429:
        return ("The site asked us to slow down (HTTP 429)",
                "Raise delay_seconds and check fewer pages on this site.")
    if status >= 500:
        return (f"The site had an error (HTTP {status})",
                "Usually temporary. The watcher will try again next run; check by hand "
                "if it matters this week.")
    return f"Unexpected answer from the site (HTTP {status})", ""


_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_DATE_REF = re.compile(r"\{\{\s*today\s*(?:([+-])\s*(\d+))?\s*(?::([^}]+))?\}\}")


def expand_dates(url: str) -> str:
    """{{today}}, {{today-30}} or {{today-30:%m/%d/%Y}} become dates, for APIs that need a date window."""
    def replace(match):
        sign, days, fmt = match.groups()
        day = dt.date.today()
        if days:
            day += dt.timedelta(days=int(days) * (-1 if sign == "-" else 1))
        return day.strftime(fmt.strip() if fmt else "%Y-%m-%d")
    return _DATE_REF.sub(replace, url)


def expand_env(url: str) -> tuple[str, dict]:
    """Fill in dates, and replace ${NAME} with the environment variable NAME so
    API keys stay out of sources.yaml. Returns the address and the secrets used."""
    url = expand_dates(url)
    found: dict[str, str] = {}

    def replace(match):
        name = match.group(1)
        value = os.environ.get(name)
        if not value:
            raise FetchError(f"The environment variable {name} is not set",
                             f"Set {name} before running (in a cloud environment: its environment "
                             "variables or API credentials). Never write keys into sources.yaml.")
        found[value] = "${" + name + "}"
        return value

    return _ENV_REF.sub(replace, url), found


class Fetcher:
    def __init__(self, settings: dict, url_map: list[tuple[str, str]]):
        self.user_agent = str(settings["user_agent"])
        self.delay = float(settings["delay_seconds"])
        self.timeout = float(settings["timeout_seconds"])
        self.max_bytes = int(float(settings["max_megabytes"]) * 1024 * 1024)
        self.url_map = url_map
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent,
                                     "Accept-Language": "en-US,en;q=0.8"})
        self._last_request: dict[str, float] = {}
        self._host_delay: dict[str, float] = {}
        self._robots: dict[str, object] = {}
        self._secrets: dict[str, str] = {}
        self.request_count = 0

    def redact(self, url: str) -> str:
        for value, placeholder in self._secrets.items():
            url = url.replace(value, placeholder)
        return url

    # URL mapping lets the demo and tests serve fictional sites from this computer.
    def map_url(self, url: str) -> str:
        for original, replacement in self.url_map:
            if url.startswith(original):
                return replacement + url[len(original):]
        return url

    def unmap_url(self, url: str) -> str:
        for original, replacement in self.url_map:
            if url.startswith(replacement):
                return original + url[len(replacement):]
        return url

    def is_mapped(self, url: str) -> bool:
        return any(url.startswith(original) for original, _ in self.url_map)

    def _pause(self, host: str) -> None:
        delay = max(self.delay, self._host_delay.get(host, 0.0))
        last = self._last_request.get(host)
        if last is not None:
            remaining = delay - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def _request(self, url: str, accept: str, headers: dict | None = None) -> Response:
        host = (urlsplit(url).hostname or "").lower()
        real_url, secrets = expand_env(url)
        self._secrets.update(secrets)
        self._pause(host)
        try:
            with self.session.get(self.map_url(real_url), headers={"Accept": accept, **(headers or {})},
                                  timeout=self.timeout, stream=True,
                                  allow_redirects=True) as resp:
                self.request_count += 1
                chunks, size = [], 0
                for chunk in resp.iter_content(65536):
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise FetchError(
                            f"File is larger than {self.max_bytes // (1024 * 1024)} MB",
                            "Raise max_megabytes in settings if you really need this file.")
                    chunks.append(chunk)
                result = Response(resp.status_code, dict(resp.headers), b"".join(chunks),
                                  self.redact(self.unmap_url(resp.url)))
        except requests.exceptions.RequestException as exc:
            raise FetchError(*describe_network_error(exc, host)) from None
        deny = {k.lower(): v for k, v in result.headers.items()}.get("x-deny-reason")
        if result.status_code == 403 and deny:
            raise FetchError(f"Blocked by the network policy ({host}: {deny})", network_hint(host))
        return result

    def robots_allows(self, url: str) -> bool:
        """True or False, or raises FetchError if robots.txt could not be checked."""
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            self._robots[origin] = self._load_robots(origin)
        rules = self._robots[origin]
        if isinstance(rules, FetchError):
            raise rules
        return rules.allows(url)

    def _load_robots(self, origin: str):
        host = (urlsplit(origin).hostname or "").lower()
        try:
            resp = self._request(origin + "/robots.txt", "text/plain,*/*;q=0.5")
        except FetchError as exc:
            return FetchError(f"Could not read robots.txt: {exc}", exc.hint)
        if resp.status_code == 200:
            text = resp.content[: 512 * 1024].decode("utf-8", errors="replace")
            rules = RobotsRules(text, self.user_agent)
            if rules.crawl_delay:
                self._host_delay[host] = min(rules.crawl_delay, 60.0)
            return rules
        if resp.status_code == 429 or resp.status_code >= 500:
            return FetchError(f"robots.txt answered HTTP {resp.status_code}",
                              "The site is busy or having problems, so nothing was fetched "
                              "from it this run. The watcher will try again next run.")
        # Any other answer (such as 404) means there is no robots.txt: RFC 9309 allows access.
        return RobotsRules("", self.user_agent)

    def fetch(self, url: str, accept: str, etag: str | None = None,
              last_modified: str | None = None) -> Response:
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        return self._request(url, accept, headers)


# --------------------------------------------------------------------------
# Turning documents into text
# --------------------------------------------------------------------------

class ExtractError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


@dataclass
class Extracted:
    lines: list[str]
    links: list[dict] = field(default_factory=list)
    records: dict | None = None      # json/rss: id -> {"text", "url"}
    info: dict = field(default_factory=dict)
    page_of_line: list | None = None  # pdf: page number for each line


BLOCK_TAGS = [
    "address", "article", "aside", "blockquote", "caption", "dd", "details", "div",
    "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre",
    "section", "summary", "table", "tbody", "tfoot", "thead", "tr", "ul",
]
DROP_TAGS = [
    "script", "style", "noscript", "template", "svg", "canvas", "iframe", "object",
    "embed", "button", "select", "option", "input", "textarea", "link", "meta",
]


def _links_in(root, base_url: str) -> list[dict]:
    links, seen = [], set()
    for a in root.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        url = urljoin(base_url, href)
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https"):
            continue
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
        if url in seen:
            continue
        seen.add(url)
        text = normalise_line(a.get_text(" ")) or normalise_line(a.get("title", "")) or url
        links.append({"text": text, "url": url, "kind": link_kind(url)})
    return links


def html_to_extracted(content: bytes, base_url: str, selector: str | None = None,
                      exclude_selector: str | None = None) -> Extracted:
    soup = BeautifulSoup(content, "html.parser")
    base = soup.find("base", href=True)
    if base:
        base_url = urljoin(base_url, base["href"])
    for tag in soup.find_all(DROP_TAGS):
        tag.decompose()
    for tag in soup.select("[hidden], [aria-hidden=true]"):
        tag.decompose()
    if soup.head:
        soup.head.decompose()
    if exclude_selector:
        for tag in soup.select(exclude_selector):
            tag.decompose()
    if selector:
        roots = soup.select(selector)
        if not roots:
            raise ExtractError(
                f"The CSS selector {selector!r} matched nothing on the page",
                "The page layout may have changed. Open the page, find the part you "
                "want to watch and update 'selector' in sources.yaml.")
    else:
        roots = soup.select("main, [role=main]")
        if not roots:
            body = soup.body or soup
            for tag in body.select("header, nav, footer, aside"):
                tag.decompose()
            roots = [body]
    # Drop roots that sit inside another root, so no text is counted twice.
    root_ids = {id(r) for r in roots}
    roots = [r for r in roots if not any(id(p) in root_ids for p in r.parents)]

    links: list[dict] = []
    lines: list[str] = []
    for root in roots:
        links.extend(_links_in(root, base_url))
        # Line breaks in the HTML source are just spaces; only block tags start new lines.
        for node in root.find_all(string=True):
            if isinstance(node, (Comment, Declaration, Doctype, ProcessingInstruction)):
                continue
            if node.find_parent("pre") is None and "\n" in node:
                node.replace_with(NavigableString(_SPACES.sub(" ", str(node))))
        for br in root.find_all("br"):
            # Inside a table cell a line break would split the row, so use "; " there.
            br.replace_with("; " if br.find_parent(["td", "th"]) else "\n")
        for cell in root.find_all(["td", "th"]):
            cell.insert_after(" | ")
        for tag in root.find_all(BLOCK_TAGS):
            tag.insert_before("\n")
            tag.insert_after("\n")
        lines.extend(normalise_lines(root.get_text().split("\n")))
    unique, seen = [], set()
    for link in links:
        if link["url"] not in seen:
            seen.add(link["url"])
            unique.append(link)
    return Extracted(lines=lines, links=unique)


def pdf_to_extracted(content: bytes) -> Extracted:
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ExtractError("The PDF is password-protected",
                                   "Check it by hand; the watcher cannot read it.") from None
        pages = list(reader.pages)
    except ExtractError:
        raise
    except Exception as exc:
        raise ExtractError(f"Could not read the PDF ({exc.__class__.__name__})",
                           "The file may be damaged or not really a PDF. Open it by hand.") from None
    lines, page_of_line, links, seen = [], [], [], set()
    pages_with_text = 0
    for number, page in enumerate(pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        page_lines = normalise_lines(text.splitlines())
        if page_lines:
            pages_with_text += 1
        lines.append(f"[Page {number}]")
        page_of_line.append(number)
        lines.extend(page_lines)
        page_of_line.extend([number] * len(page_lines))
        try:
            annotations = page.get("/Annots") or []
            for annot in annotations:
                obj = annot.get_object()
                action = obj.get("/A") or {}
                uri = action.get("/URI") if hasattr(action, "get") else None
                if uri and str(uri).startswith(("http://", "https://")) and str(uri) not in seen:
                    seen.add(str(uri))
                    links.append({"text": str(uri), "url": str(uri), "kind": link_kind(str(uri))})
        except Exception:
            pass
    info = {"pages": len(pages), "pages_with_text": pages_with_text}
    if pages and pages_with_text == 0:
        digest = hashlib.sha256(content).hexdigest()[:16]
        lines.append(f"[No text found - file fingerprint {digest}]")
        page_of_line.append(None)
        info["note"] = ("No text could be read from this PDF (it may be a scanned image). "
                        "The watcher can still tell when the file changes, but you must read it yourself.")
    return Extracted(lines=lines, links=links, info=info, page_of_line=page_of_line)


def _record_matches(record: dict, rules: dict) -> bool:
    for field_name, values in rules.items():
        value = dig(record, field_name)
        if value is not None and str(value).strip().lower() in values:
            return True
    return False


def json_to_extracted(content: bytes, source: dict) -> Extracted:
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise ExtractError(f"The answer was not valid JSON ({exc})",
                           "Open the address in a browser: it may now return a web page or an error.") from None
    items = dig(data, source.get("items_path"))
    if items is None:
        raise ExtractError(f"Nothing found at items_path {source.get('items_path')!r}",
                           "The data layout may have changed. Open the address and update items_path.")
    if not isinstance(items, list):
        text = json.dumps(items, ensure_ascii=False, sort_keys=True, indent=1)
        return Extracted(lines=normalise_lines(text.splitlines()))
    fields = source.get("fields") or []
    id_field = source.get("id_field")
    link_field = source.get("link_field")
    skip_rules = source.get("skip_records_where") or {}
    records, links, skipped = {}, [], 0
    for item in items:
        if not isinstance(item, dict):
            item = {"value": item}
        if skip_rules and _record_matches(item, skip_rules):
            skipped += 1
            continue
        kept = {f: dig(item, f) for f in fields} if fields else item
        parts = [f"{name}: {short(value)}" for name, value in kept.items()
                 if value not in (None, "", [], {}) and name != id_field]
        text = " | ".join(parts)
        record_id = dig(item, id_field) if id_field else None
        if record_id in (None, ""):
            record_id = hashlib.sha1(text.encode()).hexdigest()[:12]
        record_id = normalise_line(record_id)
        url = dig(item, link_field) if link_field else None
        if isinstance(url, dict):  # Socrata stores some links as {"url": ...}
            url = url.get("url")
        url = str(url) if url and str(url).startswith(("http://", "https://")) else None
        records[record_id] = {"text": text, "url": url}
        if url:
            links.append({"text": f"{record_id}", "url": url, "kind": link_kind(url)})
    lines = [f"{rid} | {rec['text']}" for rid, rec in sorted(records.items())]
    info = {"records": len(records), "records_skipped_by_rule": skipped}
    return Extracted(lines=normalise_lines(lines), links=links, records=records, info=info)


def feed_to_extracted(content: bytes) -> Extracted:
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ExtractError(f"Could not read the feed ({parsed.get('bozo_exception')})",
                           "Open the address in a browser: it may no longer be an RSS or Atom feed.")
    records, links = {}, []
    for entry in parsed.entries:
        link = entry.get("link") or ""
        title = normalise_line(entry.get("title", ""))
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        date = time.strftime("%Y-%m-%d", stamp) if stamp else normalise_line(
            entry.get("published") or entry.get("updated") or "")
        summary_html = entry.get("summary") or entry.get("description") or ""
        summary = short(BeautifulSoup(summary_html, "html.parser").get_text(" "), 600)
        record_id = normalise_line(entry.get("id") or link or title)
        if not record_id:
            continue
        text = " | ".join(x for x in (date, title, summary) if x)
        records[record_id] = {"text": text, "url": link or None, "title": title}
        if link:
            links.append({"text": title or link, "url": link, "kind": link_kind(link)})
    # Newest first: each line starts with the item's date.
    lines = sorted((f"{rec['text']} | {rec['url'] or ''}" for rec in records.values()), reverse=True)
    return Extracted(lines=normalise_lines(lines), links=links, records=records,
                     info={"records": len(records)})


def extract(source: dict, resp: Response, warnings: list[str]) -> Extracted:
    kind = source["type"]
    content = resp.content
    looks_pdf = b"%PDF" in content[:1024]
    if kind == "pdf" and not looks_pdf:
        ctype = resp.headers.get("Content-Type") or resp.headers.get("content-type") or "unknown"
        raise ExtractError(f"Expected a PDF but received something else ({ctype})",
                           "The link may now point to a web page or a login screen. Open it "
                           "in a browser and update the address or type in sources.yaml.")
    if kind == "html" and looks_pdf:
        warnings.append("This address returns a PDF. Set type: pdf in sources.yaml.")
        kind = "pdf"
    if kind == "html":
        return html_to_extracted(content, resp.url, source.get("selector"),
                                 source.get("exclude_selector"))
    if kind == "pdf":
        return pdf_to_extracted(content)
    if kind == "json":
        return json_to_extracted(content, source)
    return feed_to_extracted(content)


def apply_ignore_patterns(ext: Extracted, patterns: list[re.Pattern]) -> None:
    if not patterns:
        return
    keep = [not any(p.search(line) for p in patterns) for line in ext.lines]
    ext.lines = [line for line, k in zip(ext.lines, keep) if k]
    if ext.page_of_line is not None:
        ext.page_of_line = [page for page, k in zip(ext.page_of_line, keep) if k]


def content_hash(ext: Extracted) -> str:
    payload = "\n".join(ext.lines) + "\n--links--\n" + "\n".join(sorted(l["url"] for l in ext.links))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Snapshots
# --------------------------------------------------------------------------

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def _write_json(path: Path, data) -> None:
    _write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


class Store:
    """Keeps one folder per source under data/snapshots/."""

    def __init__(self, data_dir: Path, keep_history: int, dry_run: bool):
        self.data_dir = data_dir
        self.keep_history = max(0, int(keep_history))
        self.dry_run = dry_run

    def folder(self, sid: str) -> Path:
        return self.data_dir / "snapshots" / sid

    def load(self, sid: str) -> dict | None:
        folder = self.folder(sid)
        meta_path = folder / "meta.json"
        if not meta_path.exists() or not (folder / "current.txt").exists():
            return None
        snap = {
            "meta": json.loads(meta_path.read_text(encoding="utf-8")),
            "lines": (folder / "current.txt").read_text(encoding="utf-8").splitlines(),
            "links": [],
            "records": None,
        }
        if (folder / "links.json").exists():
            snap["links"] = json.loads((folder / "links.json").read_text(encoding="utf-8"))
        if (folder / "records.json").exists():
            snap["records"] = json.loads((folder / "records.json").read_text(encoding="utf-8"))
        return snap

    def save(self, sid: str, ext: Extracted, meta: dict, previous: dict | None) -> None:
        if self.dry_run:
            return
        folder = self.folder(sid)
        if previous is not None and self.keep_history:
            stamp = re.sub(r"[^0-9TZ]", "", previous["meta"].get("last_checked", "")) or "previous"
            history = folder / "history"
            history.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / "current.txt", history / f"{stamp}.txt")
            old = sorted(history.glob("*.txt"))
            for extra in old[: max(0, len(old) - self.keep_history)]:
                extra.unlink()
        _write(folder / "current.txt", "\n".join(ext.lines) + "\n")
        _write_json(folder / "links.json", ext.links)
        if ext.records is not None:
            _write_json(folder / "records.json", ext.records)
        _write_json(folder / "meta.json", meta)

    def save_meta(self, sid: str, meta: dict) -> None:
        if not self.dry_run:
            _write_json(self.folder(sid) / "meta.json", meta)

    def save_document(self, url: str, header: list[str], lines: list[str]) -> Path:
        path = self.data_dir / "documents" / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")
        if not self.dry_run:
            _write(path, "\n".join(header) + "\n\n" + "\n".join(lines) + "\n")
        return path


# --------------------------------------------------------------------------
# Comparing
# --------------------------------------------------------------------------

def diff_lines(old: list[str], new: list[str], max_diff: int,
               page_of_line: list | None) -> dict:
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=len(old) + len(new) > 6000)
    added, removed = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed.extend(line for line in old[i1:i2] if not line.startswith("[Page "))
        if tag in ("replace", "insert"):
            for j in range(j1, j2):
                line = new[j]
                if line.startswith("[Page "):
                    continue
                page = page_of_line[j] if page_of_line and j < len(page_of_line) else None
                added.append(f"[p. {page}] {line}" if page else line)
    diff = list(difflib.unified_diff(old, new, "previous", "current", n=1, lineterm=""))[2:]
    result = {"added": added[:MAX_LIST_ITEMS], "removed": removed[:MAX_LIST_ITEMS],
              "diff": diff[:max_diff]}
    if len(added) > MAX_LIST_ITEMS:
        result["added_not_shown"] = len(added) - MAX_LIST_ITEMS
    if len(removed) > MAX_LIST_ITEMS:
        result["removed_not_shown"] = len(removed) - MAX_LIST_ITEMS
    if len(diff) > max_diff:
        result["diff_not_shown"] = len(diff) - max_diff
    result["counts"] = (len(added), len(removed))
    return result


def compare_records(old: dict, new: dict, keywords: list[str], report_removed: bool = False) -> dict:
    new_ids = [rid for rid in new if rid not in old]
    removed_ids = [rid for rid in old if rid not in new]
    changed_ids = [rid for rid in new if rid in old and new[rid]["text"] != old[rid]["text"]]

    def wanted(text: str) -> list[str] | None:
        if not keywords:
            return []
        hits = find_keywords([text], keywords)
        return hits or None

    out = {"new_records": [], "changed_records": [], "removed_records": [],
           "other_records_not_matching_keywords": 0}
    for rid in new_ids:
        hits = wanted(new[rid]["text"])
        if hits is None:
            out["other_records_not_matching_keywords"] += 1
            continue
        rec = {"id": rid, "text": new[rid]["text"], "url": new[rid].get("url")}
        if new[rid].get("title"):
            rec["title"] = new[rid]["title"]
        if hits:
            rec["keywords"] = hits
        out["new_records"].append(rec)
    for rid in changed_ids:
        hits = wanted(new[rid]["text"] + " " + old[rid]["text"])
        if hits is None:
            out["other_records_not_matching_keywords"] += 1
            continue
        out["changed_records"].append({"id": rid, "before": old[rid]["text"],
                                       "after": new[rid]["text"], "url": new[rid].get("url")})
    if report_removed:
        for rid in removed_ids:
            if wanted(old[rid]["text"]) is None:
                out["other_records_not_matching_keywords"] += 1
                continue
            out["removed_records"].append({"id": rid, "text": old[rid]["text"]})
    elif removed_ids:
        out["records_dropped_out"] = len(removed_ids)  # feeds and API windows drop old records
    for key in ("new_records", "changed_records", "removed_records"):
        out[key] = out[key][:MAX_LIST_ITEMS]
    return out


# --------------------------------------------------------------------------
# Checking one source
# --------------------------------------------------------------------------

def follow_documents(source: dict, candidates: list[dict], fetcher: Fetcher, store: Store,
                     digest_dir: Path, settings: dict) -> tuple[list[dict], list[str]]:
    follow = source.get("follow_new_links")
    if not follow or not candidates:
        return [], []
    limit = min(follow["max"], int(settings["max_follow_per_source"]))
    documents, notes = [], []
    matching = [c for c in candidates if c.get("url") and follow["pattern"].search(c["url"])]
    for link in matching[:limit]:
        url = link["url"]
        try:
            if not fetcher.robots_allows(url):
                notes.append(f"Not fetched (robots.txt does not allow it): {url}")
                continue
            resp = fetcher.fetch(url, "application/pdf,text/html;q=0.9,*/*;q=0.5")
            if resp.status_code >= 400:
                notes.append(f"Could not fetch {url}: HTTP {resp.status_code}")
                continue
            if b"%PDF" in resp.content[:1024]:
                ext, kind = pdf_to_extracted(resp.content), "pdf"
            else:
                ext, kind = html_to_extracted(resp.content, resp.url), "page"
        except (FetchError, ExtractError) as exc:
            notes.append(f"Could not fetch {url}: {exc}")
            continue
        header = [f"Source: {url}", f"Link text: {link.get('text', '')}",
                  f"Fetched: {iso(utc_now())}", f"Type: {kind}"
                  + (f", {ext.info.get('pages')} pages" if kind == "pdf" else "")]
        path = store.save_document(url, header, ext.lines)
        excerpt, size = [], 0
        for line in ext.lines:
            if len(excerpt) >= EXCERPT_LINES or size > EXCERPT_CHARS:
                break
            excerpt.append(line)
            size += len(line)
        doc = {"title": link.get("text", ""), "url": url, "type": kind,
               "text_file": os.path.relpath(path, digest_dir).replace(os.sep, "/"),
               "excerpt": excerpt}
        if kind == "pdf":
            doc["pages"] = ext.info.get("pages")
            if ext.info.get("note"):
                doc["note"] = ext.info["note"]
        documents.append(doc)
    if len(matching) > limit:
        notes.append(f"{len(matching) - limit} more new linked documents were not fetched "
                     f"(limit {limit}). Open them from new_links.")
    return documents, notes


def summary_text(entry: dict) -> str:
    parts = []
    added, removed = entry.pop("counts", (0, 0))
    if added:
        parts.append(f"{added} line{'s' if added != 1 else ''} added")
    if removed:
        parts.append(f"{removed} line{'s' if removed != 1 else ''} removed")
    for key, one, many in (("new_links", "new link", "new links"),
                           ("new_records", "new record", "new records"),
                           ("changed_records", "changed record", "changed records"),
                           ("removed_records", "removed record", "removed records"),
                           ("documents", "document fetched", "documents fetched")):
        count = len(entry.get(key) or [])
        if count:
            parts.append(f"{count} {one if count == 1 else many}")
    other = entry.get("other_records_not_matching_keywords")
    if other:
        parts.append(f"{other} other record change{'s' if other != 1 else ''} without your keywords")
    dropped = entry.get("records_dropped_out")
    if dropped and not parts:
        parts.append(f"{plural(dropped, 'older record')} dropped out of the feed")
    return ", ".join(parts) or "content changed"


def config_fingerprint(source: dict) -> str:
    """Changes when the way a source is read changes (address, selector, fields...)."""
    keys = ("url", "type", "selector", "exclude_selector", "items_path", "id_field",
            "fields", "link_field")
    data = {k: source.get(k) for k in keys}
    data["ignore"] = [p.pattern for p in source.get("ignore_patterns_compiled") or []]
    data["skip"] = {k: sorted(v) for k, v in (source.get("skip_records_where") or {}).items()}
    return hashlib.sha1(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]


def check_source(source: dict, fetcher: Fetcher, store: Store, settings: dict,
                 digest_dir: Path) -> dict:
    sid, name, url, kind = source["id"], source["name"], source["url"], source["type"]
    base = {"id": sid, "name": name, "url": url, "type": kind}
    now = iso(utc_now())

    if is_placeholder(url) and not fetcher.is_mapped(url):
        return {**base, "status": "skipped",
                "reason": "Placeholder address. Replace it with the real address of the official page."}

    try:
        if not fetcher.robots_allows(url):
            return {**base, "status": "skipped",
                    "reason": "robots.txt does not allow automated access to this address. "
                              "Do not fetch it another way: look for an RSS feed, API or "
                              "open-data version, or check it by hand."}
    except FetchError as exc:
        return {**base, "status": "error", "error": str(exc), "hint": exc.hint}

    previous = store.load(sid)
    fingerprint = config_fingerprint(source)
    settings_changed = previous is not None and previous["meta"].get("config") not in (None, fingerprint)
    if settings_changed:
        previous = None  # read it fresh and save a new baseline
    prev_meta = (previous or {}).get("meta", {})
    try:
        resp = fetcher.fetch(url, ACCEPT[kind],
                             etag=prev_meta.get("etag") if previous else None,
                             last_modified=prev_meta.get("last_modified") if previous else None)
    except FetchError as exc:
        return {**base, "status": "error", "error": str(exc), "hint": exc.hint}

    if resp.status_code == 304 and previous is not None:
        meta = {**prev_meta, "last_checked": now}
        store.save_meta(sid, meta)
        return {**base, "status": "unchanged", "last_changed": prev_meta.get("last_changed"),
                "first_checked": prev_meta.get("first_checked"), "note": "not modified (HTTP 304)"}
    if resp.status_code >= 300:
        message, hint = http_status_problem(resp.status_code)
        return {**base, "status": "error", "error": message, "hint": hint}

    warnings: list[str] = []
    final_url = resp.url
    if urlsplit(final_url).netloc != urlsplit(url).netloc:
        try:
            if not fetcher.robots_allows(final_url):
                return {**base, "status": "skipped",
                        "reason": f"Redirected to {final_url}, which robots.txt does not allow."}
        except FetchError as exc:
            return {**base, "status": "error", "error": str(exc), "hint": exc.hint}
    if final_url != url:
        warnings.append(f"Redirected to {final_url}. Consider updating the address in sources.yaml.")

    try:
        ext = extract(source, resp, warnings)
    except ExtractError as exc:
        return {**base, "status": "error", "error": str(exc), "hint": exc.hint}
    apply_ignore_patterns(ext, source.get("ignore_patterns_compiled") or [])
    if ext.info.get("note"):
        warnings.append(ext.info["note"])
    if not ext.lines:
        warnings.append("No text was found. Check the selector or open the page by hand.")

    headers = {k.lower(): v for k, v in resp.headers.items()}
    sha = content_hash(ext)
    meta = {
        "id": sid, "name": name, "url": url, "type": kind,
        "first_checked": prev_meta.get("first_checked", now),
        "last_checked": now,
        "last_changed": prev_meta.get("last_changed"),  # None until a change is seen
        "sha256": sha,
        "etag": headers.get("etag"),
        "last_modified": headers.get("last-modified"),
        "config": fingerprint,
    }
    snapshot_path = os.path.relpath(store.folder(sid) / "current.txt", digest_dir).replace(os.sep, "/")

    if previous is None:
        store.save(sid, ext, meta, None)
        note = ("The settings for this source changed, so a new snapshot was saved. "
                if settings_changed else "First check: snapshot saved. ")
        entry = {**base, "status": "first_run", "snapshot": snapshot_path,
                 "note": note + "Changes will be reported from the next run."}
        if warnings:
            entry["warnings"] = warnings
        return entry

    if sha == prev_meta.get("sha256"):
        store.save_meta(sid, meta)
        entry = {**base, "status": "unchanged", "last_changed": prev_meta.get("last_changed"),
                 "first_checked": prev_meta.get("first_checked")}
        if warnings:
            entry["warnings"] = warnings
        return entry

    meta["last_changed"] = now
    keywords = source.get("keywords", settings.get("keywords") or [])
    entry = {**base, "status": "changed", "tags": source.get("tags", []),
             "checked_at": now, "previous_check": prev_meta.get("last_checked")}
    if source.get("notes"):
        entry["notes"] = source["notes"]
    if final_url != url:
        entry["final_url"] = final_url

    prev_urls = {l["url"] for l in previous["links"]}
    new_urls = {l["url"] for l in ext.links}
    if ext.records is not None and previous.get("records") is not None:
        entry.update(compare_records(previous["records"], ext.records, keywords,
                                     bool(source.get("report_removed"))))
        if not (entry["new_records"] or entry["changed_records"] or entry["removed_records"]):
            # Nothing that matches the keywords: save the snapshot, but there is nothing to draft.
            store.save(sid, ext, meta, previous)
            quiet = {**base, "status": "no_match",
                     "other_records_not_matching_keywords": entry["other_records_not_matching_keywords"]}
            if entry.get("records_dropped_out"):
                quiet["records_dropped_out"] = entry["records_dropped_out"]
            quiet["summary"] = summary_text(dict(quiet))
            return quiet
        candidates = [{"text": r.get("title") or r["id"], "url": r["url"]}
                      for r in entry["new_records"] if r.get("url")]
        hit_texts = [r["text"] for r in entry["new_records"]] + \
                    [r["after"] for r in entry["changed_records"]]
    else:
        changes = diff_lines(previous["lines"], ext.lines, int(settings["max_diff_lines"]),
                             ext.page_of_line)
        entry.update(changes)
        entry["new_links"] = [l for l in ext.links if l["url"] not in prev_urls][:MAX_LIST_ITEMS]
        entry["removed_links"] = [l for l in previous["links"] if l["url"] not in new_urls][:MAX_LIST_ITEMS]
        candidates = entry["new_links"]
        hit_texts = changes["added"] + [l["text"] for l in entry["new_links"]]
    entry["keyword_hits"] = find_keywords(hit_texts, keywords)

    documents, notes = follow_documents(source, candidates, fetcher, store, digest_dir, settings)
    if documents:
        entry["documents"] = documents
        found = set(entry["keyword_hits"]) | set(
            find_keywords([" ".join(d["excerpt"]) for d in documents], keywords))
        entry["keyword_hits"] = [k for k in keywords if k in found]
    warnings.extend(notes)
    entry["summary"] = summary_text(entry)
    entry["snapshot"] = snapshot_path
    if warnings:
        entry["warnings"] = warnings
    store.save(sid, ext, meta, previous)
    return entry


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def load_config(path: Path) -> tuple[dict | None, list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"File not found: {path}"], []
    except yaml.YAMLError as exc:
        return None, [f"{path} is not valid YAML: {exc}"], []
    if not isinstance(raw, dict) or not isinstance(raw.get("sources"), list):
        return None, [f"{path} must contain a 'sources:' list. See templates/sources/."], []

    settings = dict(DEFAULT_SETTINGS)
    for key, value in (raw.get("settings") or {}).items():
        if key not in DEFAULT_SETTINGS:
            warnings.append(f"settings: unknown option '{key}' is ignored")
            continue
        settings[key] = value
    if not isinstance(settings["keywords"], list):
        problems.append("settings: keywords must be a list, for example [battery, moratorium]")

    sources, seen = [], set()
    for number, src in enumerate(raw["sources"], start=1):
        where = f"source #{number}"
        if not isinstance(src, dict):
            problems.append(f"{where}: each source must be a set of 'key: value' lines")
            continue
        name = str(src.get("name") or "").strip()
        where = f"source #{number} ({name or 'no name'})"
        url = str(src.get("url") or "").strip()
        kind = str(src.get("type") or "").strip().lower()
        if not name:
            problems.append(f"{where}: 'name' is missing")
        if not re.match(r"^https?://[^\s/]+", url):
            problems.append(f"{where}: 'url' must start with https:// (or http://)")
        if kind not in TYPES:
            problems.append(f"{where}: 'type' must be one of: {', '.join(TYPES)}")
        for key in src:
            if key not in SOURCE_FIELDS:
                warnings.append(f"{where}: unknown option '{key}' is ignored")
        sid = slugify(src.get("id") or name)
        if sid in seen:
            problems.append(f"{where}: two sources share the id '{sid}'. Give one a different 'id'.")
        seen.add(sid)

        compiled = []
        for pattern in src.get("ignore_patterns") or []:
            try:
                compiled.append(re.compile(str(pattern), re.IGNORECASE))
            except re.error as exc:
                problems.append(f"{where}: ignore pattern {pattern!r} is not a valid regular expression ({exc})")

        follow = src.get("follow_new_links")
        follow_cfg = None
        if follow:
            pattern, limit = DEFAULT_FOLLOW_PATTERN, int(settings["max_follow_per_source"])
            if isinstance(follow, str):
                pattern = follow
            elif isinstance(follow, dict):
                pattern = str(follow.get("pattern") or pattern)
                limit = int(follow.get("max") or limit)
            try:
                follow_cfg = {"pattern": re.compile(pattern, re.IGNORECASE), "max": limit}
            except re.error as exc:
                problems.append(f"{where}: follow_new_links pattern is not valid ({exc})")

        skip_rules = {}
        for field_name, values in (src.get("skip_records_where") or {}).items():
            values = values if isinstance(values, list) else [values]
            skip_rules[str(field_name)] = {str(v).strip().lower() for v in values}

        source = {
            "id": sid, "name": name, "url": url, "type": kind,
            "selector": src.get("selector"), "exclude_selector": src.get("exclude_selector"),
            "tags": [str(t) for t in (src.get("tags") or [])],
            "ignore_patterns_compiled": compiled,
            "follow_new_links": follow_cfg,
            "items_path": src.get("items_path"), "id_field": src.get("id_field"),
            "fields": [str(f) for f in (src.get("fields") or [])],
            "link_field": src.get("link_field"),
            "skip_records_where": skip_rules,
            "report_removed": bool(src.get("report_removed")),
            "notes": src.get("notes"),
            "terms_checked": str(src["terms_checked"]) if src.get("terms_checked") else None,
            "enabled": src.get("enabled", True) is not False,
        }
        if "keywords" in src:
            source["keywords"] = [str(k) for k in (src.get("keywords") or [])]
        sources.append(source)

    agent = str(settings["user_agent"])
    if "@" not in agent or any(x in agent.lower() for x in ("example.com", "yourdomain", "you@")):
        warnings.append("settings.user_agent has no real contact email. Sites should be able to "
                        "reach you: use something like 'YourDigest/1.0 (+mailto:you@yourdomain.com)'.")
    no_terms = [s["name"] for s in sources if s["enabled"] and not s["terms_checked"]
                and not is_placeholder(s["url"])]
    if no_terms:
        warnings.append(f"{len(no_terms)} source(s) have no terms_checked date. Read each site's "
                        "terms of use and note the date you checked them.")
    return {"digest": raw.get("digest") or {}, "settings": settings, "sources": sources}, problems, warnings


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------

def build_report(config: dict, results: list[dict], started: dt.datetime, finished: dt.datetime,
                 sources_path: Path, digest_dir: Path, warnings: list[str], dry_run: bool) -> dict:
    groups = {key: [r for r in results if r["status"] == key]
              for key in ("changed", "no_match", "first_run", "unchanged", "skipped", "error")}
    digest = config.get("digest") or {}
    report = {
        "tool": f"weekly-digest watch_sources.py {VERSION}",
        "digest": digest.get("name", ""),
        "scope": digest.get("scope", ""),
        "sources_file": os.path.relpath(sources_path, digest_dir).replace(os.sep, "/"),
        "paths_relative_to": "the folder that holds the sources file",
        "week": week_label(started.astimezone().date()),
        "run_started": iso(started),
        "run_finished": iso(finished),
        "dry_run": dry_run,
        "summary": {
            "sources": len(results),
            "changed": len(groups["changed"]),
            "no_keyword_match": len(groups["no_match"]),
            "first_run": len(groups["first_run"]),
            "unchanged": len(groups["unchanged"]),
            "skipped": len(groups["skipped"]),
            "errors": len(groups["error"]),
        },
        "next_step": REVIEW_REMINDER,
        "changed": groups["changed"],
        "changed_without_keyword_match": [
            {k: r.get(k) for k in ("id", "name", "url", "summary")} for r in groups["no_match"]],
        "errors": [{k: r.get(k) for k in ("id", "name", "url", "error", "hint")} for r in groups["error"]],
        "skipped": [{k: r.get(k) for k in ("id", "name", "url", "reason")} for r in groups["skipped"]],
        "first_run": [{k: v for k, v in r.items() if k != "status"} for r in groups["first_run"]],
        "unchanged": [{k: r.get(k) for k in ("id", "name", "url", "last_changed", "first_checked")}
                      for r in groups["unchanged"]],
        "warnings": warnings,
    }
    return report


def counts_text(s: dict) -> str:
    quiet = f" ({s['no_keyword_match']} more with no keyword match)" if s.get("no_keyword_match") else ""
    return (f"{s['changed']} changed{quiet}, {s['unchanged']} unchanged, {s['first_run']} first check, "
            f"{s['skipped']} skipped, {plural(s['errors'], 'error')}")


def _md_link(text: str, url: str) -> str:
    text = text.replace("[", "(").replace("]", ")")
    return f"[{text}]({url.replace(' ', '%20').replace(')', '%29')})"


def report_markdown(report: dict) -> str:
    s = report["summary"]
    out = [f"# Changes found: {report['digest'] or 'weekly digest'}", ""]
    out.append(f"Checked {report['run_started'].replace('T', ' ').replace('Z', ' UTC')} "
               f"(week {report['week']}). {plural(s['sources'], 'source')}: {counts_text(s)}.")
    if report.get("dry_run"):
        out.append("")
        out.append("**Dry run:** snapshots were not updated.")
    out += ["", f"> **Next step:** {report['next_step']}", ""]

    if report["changed"]:
        out += [f"## Changed ({len(report['changed'])})", ""]
    for entry in report["changed"]:
        out += [f"### {entry['name']}", ""]
        meta = f"<{entry['url']}> · {entry['type']}"
        if entry.get("tags"):
            meta += " · tags: " + ", ".join(entry["tags"])
        out += [meta, "", f"- **What changed:** {entry['summary']}"]
        if entry.get("keyword_hits"):
            out.append(f"- **Keywords found:** {', '.join(entry['keyword_hits'])}")
        if entry.get("notes"):
            out.append(f"- **Your note:** {entry['notes']}")
        out.append("")
        if entry.get("diff"):
            out += ["```diff"] + entry["diff"] + ["```"]
            if entry.get("diff_not_shown"):
                out.append(f"_{entry['diff_not_shown']} more diff lines not shown; see {entry['snapshot']}._")
            out.append("")
        for key, title in (("new_records", "New records"), ("changed_records", "Changed records"),
                           ("removed_records", "Removed records")):
            if entry.get(key):
                out += [f"**{title}**", ""]
                for rec in entry[key]:
                    text = rec.get("text") or f"before: {rec.get('before')}\n  after: {rec.get('after')}"
                    label = "" if rec["id"] == rec.get("url") else f"`{rec['id']}`: "
                    line = f"- {label}{text}"
                    if rec.get("url"):
                        line += f" ({_md_link('link', rec['url'])})"
                    out.append(line)
                out.append("")
        if entry.get("other_records_not_matching_keywords"):
            out += [f"_{entry['other_records_not_matching_keywords']} other record change(s) did not "
                    "match your keywords and are not listed._", ""]
        if entry.get("new_links"):
            out += ["**New links**", ""]
            out += [f"- {_md_link(l['text'], l['url'])} ({l['kind']})" for l in entry["new_links"]]
            out.append("")
        if entry.get("documents"):
            out += ["**New documents fetched**", ""]
            for doc in entry["documents"]:
                pages = f", {plural(doc['pages'], 'page')}" if doc.get("pages") else ""
                out.append(f"- {_md_link(doc['title'] or doc['url'], doc['url'])}{pages}. "
                           f"Full text: `{doc['text_file']}`")
                for line in doc["excerpt"][:12]:
                    out.append(f"  > {line}")
            out.append("")
        if entry.get("warnings"):
            out += ["**Notes**", ""] + [f"- {w}" for w in entry["warnings"]] + [""]

    if report.get("changed_without_keyword_match"):
        out += [f"## Changed, but nothing matched your keywords ({len(report['changed_without_keyword_match'])})", ""]
        out += [f"- {e['name']}: {e['summary']}" for e in report["changed_without_keyword_match"]]
        out.append("")
    if report["errors"]:
        out += [f"## Errors ({len(report['errors'])}): check these by hand", ""]
        for e in report["errors"]:
            out.append(f"- **{e['name']}** <{e['url']}>: {e['error']}.")
            if e.get("hint"):
                out.append(f"  {e['hint']}")
        out.append("")
    if report["skipped"]:
        out += [f"## Skipped ({len(report['skipped'])})", ""]
        out += [f"- **{e['name']}** <{e['url']}>: {e['reason']}" for e in report["skipped"]]
        out.append("")
    if report["first_run"]:
        out += [f"## First check ({len(report['first_run'])})", ""]
        out += [f"- {e['name']} <{e['url']}>" for e in report["first_run"]]
        out.append("")
    if report["unchanged"]:
        out += [f"## Unchanged ({len(report['unchanged'])})", ""]
        for e in report["unchanged"]:
            if e.get("last_changed"):
                when = f"last changed {e['last_changed'][:10]}"
            else:
                when = f"no change seen since the first check on {(e.get('first_checked') or '?')[:10]}"
            out.append(f"- {e['name']} ({when})")
        out.append("")
    if report["warnings"]:
        out += ["## Setup warnings", ""] + [f"- {w}" for w in report["warnings"]] + [""]
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check official sources for changes and write changes.json and changes.md.")
    parser.add_argument("sources", help="path to sources.yaml, or the folder that contains it")
    parser.add_argument("--data", help="folder for snapshots (default: 'data' next to sources.yaml)")
    parser.add_argument("--out", help="where to write changes.json "
                        "(default: issues/<year>-W<week>/changes.json next to sources.yaml)")
    parser.add_argument("--only", action="append", default=[],
                        help="check only sources whose name or id contains this text (repeatable)")
    parser.add_argument("--delay", type=float, help="seconds between requests to the same site")
    parser.add_argument("--timeout", type=float, help="seconds to wait for a site to answer")
    parser.add_argument("--user-agent", help="user agent to send (include a contact email)")
    parser.add_argument("--dry-run", action="store_true",
                        help="check and report, but do not update the snapshots")
    parser.add_argument("--map-url", action="append", default=[], metavar="FROM=TO",
                        help="for testing: fetch addresses that start with FROM from TO instead. "
                             "Reports keep the original addresses.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    args = parse_args(argv)
    sources_path = Path(args.sources)
    if sources_path.is_dir():
        sources_path = sources_path / "sources.yaml"
    config, problems, warnings = load_config(sources_path)
    if problems:
        print("The sources file has problems:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2

    settings = config["settings"]
    if args.delay is not None:
        settings["delay_seconds"] = args.delay
    if args.timeout is not None:
        settings["timeout_seconds"] = args.timeout
    if args.user_agent:
        settings["user_agent"] = args.user_agent
        warnings = [w for w in warnings if not w.startswith("settings.user_agent")]

    url_map = []
    for item in args.map_url:
        if "=" not in item:
            print(f"--map-url needs FROM=TO, got {item!r}", file=sys.stderr)
            return 2
        original, replacement = item.split("=", 1)
        url_map.append((original, replacement))

    digest_dir = sources_path.resolve().parent
    data_dir = Path(args.data).resolve() if args.data else digest_dir / "data"
    started = utc_now()
    out_path = (Path(args.out) if args.out
                else digest_dir / "issues" / week_label(started.astimezone().date()) / "changes.json")

    sources = [s for s in config["sources"] if s["enabled"]]
    if args.only:
        wanted = [w.lower() for w in args.only]
        sources = [s for s in sources if any(w in s["name"].lower() or w in s["id"] for w in wanted)]
    if not sources:
        print("No sources to check (check --only and 'enabled').", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"Warning: {warning}")
    print(f"Checking {len(sources)} source(s) from {sources_path} "
          f"(pause {float(settings['delay_seconds']):g}s between requests to the same site)")

    fetcher = Fetcher(settings, url_map)
    store = Store(data_dir, settings["keep_history"], args.dry_run)
    results = []
    width = len(str(len(sources)))
    for number, source in enumerate(sources, start=1):
        result = check_source(source, fetcher, store, settings, digest_dir)
        results.append(result)
        detail = (result.get("summary") or result.get("error") or result.get("reason")
                  or result.get("note") or "")
        print(f"  [{number:>{width}}/{len(sources)}] {result['status'].upper():<9} {source['name']}"
              + (f": {detail}" if detail else ""))

    finished = utc_now()
    report = build_report(config, results, started, finished, sources_path, digest_dir,
                          warnings, args.dry_run)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(out_path, report)
    md_path = out_path.with_suffix(".md")
    _write(md_path, report_markdown(report))
    if not args.dry_run:
        _write_json(data_dir / "runs" / f"{iso(started).replace(':', '')}-changes.json", report)

    s = report["summary"]
    print(f"\nDone: {counts_text(s)}. {plural(fetcher.request_count, 'request')}.")
    print(f"Wrote {out_path} and {md_path.name}")
    if report["errors"]:
        print("Check the sources with errors by hand this week (see the Errors section in "
              f"{md_path.name}).")
    if s["changed"]:
        print("Next: draft items from the changes (status: needs_review), then check each "
              "one against its source.")
    if s["errors"] and s["errors"] == s["sources"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
