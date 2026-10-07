#!/usr/bin/env python3
"""
Rebuild the fictional sample issue from the simulated sources.

What it does:

  1. starts a small web server on this computer that pretends to be the
     fictional county, township and city websites in
     samples/battery-storage-ohio-week41/site/
  2. puts the "week 40" copy of those sites online and runs the watcher
     (first check, so it only saves snapshots)
  3. swaps in the "week 41" copy (a new agenda, a replaced PDF, new notices,
     new open-data records, a page that moved) and runs the watcher again.
     This writes the sample's changes.json and changes.md
  4. builds the sample issue (HTML email, PDF, xlsx tracker, ics calendar)
     from the reviewed items file, items.reviewed.yaml

Nothing goes over the internet. Run it from the kits/weekly-digest folder:

  python scripts/run_demo.py            # rebuild everything in the sample folder
  python scripts/run_demo.py --serve    # only serve the week 41 sites so you can browse them
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SAMPLE = KIT / "samples" / "battery-storage-ohio-week41"
WATCH = KIT / "scripts" / "watch_sources.py"
BUILD = KIT / "scripts" / "build_digest.py"

# File dates the fake sites report, so "only send it if it changed" works like on real sites.
WEEK40_TIME = dt.datetime(2026, 9, 30, 10, 0, tzinfo=dt.timezone.utc).timestamp()
WEEK41_TIME = dt.datetime(2026, 10, 7, 9, 0, tzinfo=dt.timezone.utc).timestamp()


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Serves files quietly and remembers every request (the self-test reads the log)."""

    def log_message(self, format, *args):  # noqa: A002 - name set by the base class
        pass

    def log_request(self, code="-", size="-"):
        try:
            status = int(code)
        except (TypeError, ValueError):
            status = code
        self.server.request_log.append(
            {"path": self.path, "status": status,
             "user_agent": self.headers.get("User-Agent", ""),
             "if_modified_since": self.headers.get("If-Modified-Since")})


class DemoServer:
    """A web server on 127.0.0.1 that serves one folder. Each top-level
    folder name is a fictional host, e.g. /www.tarrowcounty.example/..."""

    def __init__(self, root: Path, port: int = 0):
        root.mkdir(parents=True, exist_ok=True)
        handler = functools.partial(_Handler, directory=str(root))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.httpd.request_log = []
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def log(self) -> list[dict]:
        return self.httpd.request_log

    @property
    def map_url(self) -> str:
        """--map-url value: https://host/path is fetched from http://127.0.0.1:port/host/path."""
        return f"https://=http://127.0.0.1:{self.port}/"

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def sync_site(source: Path, live: Path, stamp: float) -> dict:
    """Make the live folder match source. Changed or new files get the new date."""
    live.mkdir(parents=True, exist_ok=True)
    src_files = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
    live_files = {p.relative_to(live) for p in live.rglob("*") if p.is_file()}
    report = {"added": [], "changed": [], "removed": []}
    for rel in sorted(live_files - src_files):
        (live / rel).unlink()
        report["removed"].append(str(rel))
    # Remove folders left empty, so a removed page answers "404 Not Found" like a real site.
    for folder in sorted((p for p in live.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
    for rel in sorted(src_files):
        target = live / rel
        data = (source / rel).read_bytes()
        if target.exists() and target.read_bytes() == data:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        os.utime(target, (stamp, stamp))
        report["changed" if rel in live_files else "added"].append(str(rel))
    return report


def run_watch(sources: Path, data: Path, out: Path, server: DemoServer,
              extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(WATCH), str(sources), "--data", str(data), "--out", str(out),
           "--map-url", server.map_url, "--delay", "0.2"] + (extra or [])
    return subprocess.run(cmd, check=False).returncode


def describe(report: dict) -> str:
    parts = [f"{len(report[k])} {k}" for k in ("added", "changed", "removed") if report[k]]
    return ", ".join(parts) or "no file changes"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild the fictional sample issue offline.")
    parser.add_argument("--serve", action="store_true",
                        help="only serve the week 41 fake sites until you press Ctrl+C")
    parser.add_argument("--port", type=int, default=0, help="port for the local server (default: any free port)")
    parser.add_argument("--no-build", action="store_true", help="run the watcher only")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        live = Path(tmp) / "live"
        server = DemoServer(live, args.port)
        try:
            if args.serve:
                sync_site(SAMPLE / "site" / "week41", live, WEEK41_TIME)
                base = f"http://127.0.0.1:{server.port}"
                print(f"Serving the week 41 sample sites at {base}/ (Ctrl+C to stop). Try:")
                for path in ("www.tarrowcounty.example/commissioners/agendas/",
                             "www.marlowefalls.example/council/legislation/",
                             "www.wrenfieldtwp.example/notices/feed.xml"):
                    print(f"  {base}/{path}")
                while True:
                    time.sleep(3600)

            data = SAMPLE / "data"
            if data.exists():
                shutil.rmtree(data)

            print("Week 40: putting the first copy of the sample sites online")
            print("  " + describe(sync_site(SAMPLE / "site" / "week40", live, WEEK40_TIME)))
            if run_watch(SAMPLE / "sources.yaml", data, Path(tmp) / "week40" / "changes.json", server) != 0:
                print("The week 40 run failed.", file=sys.stderr)
                return 1

            print("\nWeek 41: swapping in the changed copy of the sample sites")
            print("  " + describe(sync_site(SAMPLE / "site" / "week41", live, WEEK41_TIME)))
            if run_watch(SAMPLE / "sources.yaml", data, SAMPLE / "changes.json", server) != 0:
                print("The week 41 run failed.", file=sys.stderr)
                return 1
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
        finally:
            server.stop()

    items = SAMPLE / "items.reviewed.yaml"
    if args.no_build or not items.exists():
        return 0
    print("\nBuilding the sample issue from items.reviewed.yaml")
    return subprocess.run([sys.executable, str(BUILD), str(items), "--out", str(SAMPLE / "output"),
                           "--changes", str(SAMPLE / "changes.json")], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
