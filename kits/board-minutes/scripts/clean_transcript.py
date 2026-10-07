#!/usr/bin/env python3
"""Clean a meeting transcript into speaker-labelled text with timestamps.

Reads:  WebVTT (.vtt) from Zoom, Teams or YouTube; SRT subtitles (.srt);
        text exports (.txt) from Otter, Rev, Teams, Zoom and similar tools;
        Word transcripts (.docx), for example the Teams "Download as .docx" file.
Writes: one paragraph per speaker turn, like
        [00:04:12] Diane Okafor: Is there a motion to approve the minutes?

What it changes:
  * removes caption markup, cue numbers and repeated caption lines
  * joins back-to-back captions from the same speaker into one paragraph
    (a new paragraph starts after a pause or every 90 seconds, so you can
    still find things in the recording)
  * removes filler words (um, uh, er, erm, hmm, ah) unless you add --keep-fillers
  * renames speakers with --speaker-map, for example "Helen's iPhone=Helen Whitaker"
It never rewords what people said.

Examples:
  python clean_transcript.py meeting.vtt
  python clean_transcript.py meeting.vtt -o meeting-clean.txt
  python clean_transcript.py otter.txt --speaker-map "Speaker 1=Diane Okafor"
  python clean_transcript.py zoom.vtt --speaker-map-file speakers.txt --clock-start 19:00:30
  python clean_transcript.py teams.docx --format json -o turns.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TS = r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?"
TIMING_RE = re.compile(rf"^\s*(?P<start>{TS})\s*-->\s*(?P<end>{TS})(?:\s+.*)?$")
INLINE_TS_TAG_RE = re.compile(r"<\d{1,2}:\d{2}:\d{2}[.,]\d{3}>")
TAG_RE = re.compile(r"</?(?:[a-zA-Z][^<>]*|\d[^<>]*)>")
ASS_TAG_RE = re.compile(r"\{\\[^}]*\}")
VOICE_RE = re.compile(r"<v(?:\.[^\s>]+)*\s+([^>]+)>(.*?)(?:</v>|$)")
SPEAKER_PREFIX_RE = re.compile(r"^(?P<name>[^:]{1,60}?):\s+(?P<text>.*)$")
NAME_ONLY_RE = re.compile(r"^(?:\[(?P<bracketed>[^\]]{1,60})\]|(?P<name>[^:\[\]]{1,60}?):)\s*$")

# Text exports: a speaker line followed by what they said on the next lines.
HEADER_PATTERNS = [
    re.compile(rf"^\[(?P<name>[^\]]{{1,60}})\]\s*(?P<ts>{TS})\s*$"),                   # [Diane Okafor] 19:02:15
    re.compile(rf"^(?P<name>[^\[\]:]{{1,60}}?)\s*[\[(](?P<ts>{TS})[\])]\s*:?\s*$"),     # Diane Okafor (00:03):
    re.compile(rf"^(?P<name>[^\[\]:]{{1,60}}?)\s+[-–|]\s+(?P<ts>{TS})\s*$"),        # Diane Okafor - 00:03
    re.compile(rf"^(?P<name>[^\[\]:]{{1,60}}?)\s+(?P<ts>{TS})\s*$"),                    # Diane Okafor  0:03
]
# Text exports: timestamp and/or speaker and the words on one line.
INLINE_PATTERNS = [
    re.compile(rf"^[\[(](?P<ts>{TS})(?:\s*\|[^\])]*)?[\])]\s*[-–|]?\s*(?P<name>[^\[\]:]{{1,60}}?)\s*:\s+(?P<text>.+)$"),
    re.compile(rf"^(?P<ts>{TS})\s+[-–|]?\s*(?P<name>[^\[\]:]{{1,60}}?)\s*:\s+(?P<text>.+)$"),
    re.compile(rf"^(?P<name>[^\[\]:]{{1,60}}?)\s*[\[(](?P<ts>{TS})[\])]\s*:\s*(?P<text>.+)$"),
    re.compile(r"^(?P<name>[^\[\]:]{1,60}?):\s+(?P<text>.+)$"),
    re.compile(rf"^[\[(](?P<ts>{TS})(?:\s*\|[^\])]*)?[\])]\s*(?P<text>.+)$"),
]

NOT_NAMES = {
    "note", "notes", "motion", "question", "answer", "item", "agenda", "update", "reminder",
    "action", "summary", "re", "subject", "time", "example", "yes", "no", "okay", "ok", "so",
    "and", "but", "well", "also", "second", "vote", "result", "resolved", "whereas", "total",
    "amount", "date", "location", "attendees", "present", "absent", "minutes", "next", "now",
    "then", "first", "last", "today", "tonight", "here", "there", "aye", "nay", "transcript",
    "speakers", "source", "length", "times", "recording", "meeting", "q", "a", "p.s", "ps",
}
NAME_CONNECTORS = {"de", "da", "del", "della", "di", "du", "van", "von", "der", "den", "la", "le",
                   "bin", "binti", "al", "el", "y", "and", "&", "of", "st."}
SUSPICIOUS_LABEL_RE = re.compile(
    r"(?i)(iphone|ipad|android|galaxy|pixel|samsung|laptop|desktop|\bpc\b|macbook|\bphone\b|"
    r"\bguest\b|\buser\b|unknown|speaker\s*\d+|participant|\bzoom\b|\broom\b|conference|"
    r"family|household|\w's\b)"
)
FILLER = r"(?:[Uu]m+|[Uu]hm+|[Uu]h+|[Ee]rm+|[Ee]r|[Hh]mm+|[Aa]h+)"
FILLER_RE = re.compile(rf"(?<![\w'’-]){FILLER}(?![\w'’-])[,…]*\s*")
FILLER_AFTER_STOP_RE = re.compile(rf"([.?!]\s+)(?:{FILLER}(?![\w'’-])[,…]*\s*)+([a-z])")


@dataclass
class Cue:
    start: float | None
    end: float | None
    speaker: str | None
    text: str


@dataclass
class TranscriptInfo:
    source: str
    format: str
    captions: int = 0
    fillers_removed: int = 0
    skipped_preamble: int = 0
    speaker_seconds: dict = field(default_factory=dict)


class TranscriptError(Exception):
    pass


# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------

def read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")  # pragma: no cover


def read_docx_text(path: Path) -> str:
    """Return the text of a .docx file, one paragraph per line, tables included."""
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:  # pragma: no cover
        raise TranscriptError("Reading .docx needs the python-docx package (pip install -r requirements.txt).")
    document = Document(str(path))
    lines: list[str] = []
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lines.append(Paragraph(child, document).text)
        elif tag == "tbl":
            for row in Table(child, document).rows:
                cells = []
                for cell in row.cells:
                    text = cell.text.strip()
                    if text and (not cells or cells[-1] != text):
                        cells.append(text)
                lines.append("  ".join(cells))
    return "\n".join(lines)


def detect_format(path: Path, text: str) -> str:
    ext = path.suffix.lower()
    if ext == ".docx":
        return "DOCX"
    if ext == ".vtt" or text.lstrip("\ufeff \r\n").startswith("WEBVTT"):
        return "WebVTT"
    if ext == ".srt":
        return "SRT"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2 and lines[0].isdigit() and TIMING_RE.match(lines[1]):
        return "SRT"
    return "Text"


# --------------------------------------------------------------------------
# Speaker labels
# --------------------------------------------------------------------------

def looks_like_speaker(name: str | None) -> bool:
    """True if a label such as 'Diane Okafor', 'Speaker 2' or "Helen's iPhone" looks like a speaker."""
    if not name:
        return False
    name = name.strip()
    if not name or len(name) > 60 or name.lower().rstrip(".") in NOT_NAMES:
        return False
    if re.search(r"https?://|www\.|[.!?]$", name) and not re.search(r"\b[A-Z]\.$", name):
        return False
    if re.fullmatch(r"(?i)(speaker|participant|guest|unknown|user)\s*\d*", name):
        return True
    tokens = re.sub(r"[()]", " ", name).split()
    if not 1 <= len(tokens) <= 6:
        return False
    if not (tokens[0][0].isupper() or re.match(r"^i[A-Z]", tokens[0])):
        return False
    for token in tokens:
        if token.lower() in NAME_CONNECTORS or re.fullmatch(r"[-–&/|]", token):
            continue
        if token[0].isupper() or token[0].isdigit() or re.match(r"^i[A-Z]", token):
            continue
        return False
    return True


def parse_speaker_map(pairs: list[str] | None, files: list[str] | None) -> dict[str, str]:
    """Build {old label (case-folded): new name} from 'OLD=NEW' strings and map files."""
    mapping: dict[str, str] = {}
    entries: list[tuple[str, str]] = []
    for pair in pairs or []:
        entries.append((pair, "--speaker-map"))
    for file_name in files or []:
        path = Path(file_name)
        if not path.exists():
            raise TranscriptError(f"Speaker map file not found: {path}")
        for line in read_text_file(path).splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                entries.append((line, str(path)))
    for entry, origin in entries:
        parts = re.split(r"\s*(?:=|->|\t)\s*", entry.strip(), maxsplit=1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise TranscriptError(f"Bad speaker map entry in {origin}: {entry!r}. Use OLD=NEW.")
        mapping[parts[0].strip().casefold()] = parts[1].strip()
    return mapping


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_timestamp(value: str) -> float:
    parts = value.strip().replace(",", ".").split(":")
    seconds = float(parts[-1])
    minutes = int(parts[-2]) if len(parts) >= 2 else 0
    hours = int(parts[-3]) if len(parts) >= 3 else 0
    return hours * 3600 + minutes * 60 + seconds


def clean_markup(text: str) -> str:
    text = INLINE_TS_TAG_RE.sub("", text)
    text = TAG_RE.sub("", text)
    text = ASS_TAG_RE.sub("", text)
    text = html.unescape(text).replace("\u00a0", " ").replace("♪", "")
    return re.sub(r"\s+", " ", text).strip()


def _payload_to_cues(lines: list[str], start: float, end: float, name_lines: bool) -> list[Cue]:
    joined = " ".join(lines)
    voices = list(VOICE_RE.finditer(joined))
    if voices:
        cues = []
        for voice in voices:
            text = clean_markup(voice.group(2))
            if text:
                cues.append(Cue(start, end, clean_markup(voice.group(1)), text))
        return cues

    segments: list[list] = []  # [speaker, [texts]]
    for index, raw in enumerate(lines):
        line = clean_markup(raw)
        if not line:
            continue
        dash = re.match(r"^[-–—]\s+(.*)$", line)
        if dash:
            line = dash.group(1)
        prefix = SPEAKER_PREFIX_RE.match(line)
        if prefix and looks_like_speaker(prefix["name"]):
            segments.append([prefix["name"].strip(), [prefix["text"].strip()]])
            continue
        only = NAME_ONLY_RE.match(line)
        if only:
            label = (only["bracketed"] or only["name"] or "").strip()
            if looks_like_speaker(label):
                segments.append([label, []])
                continue
        if (name_lines and index == 0 and len(lines) > 1 and looks_like_speaker(line)
                and not line.endswith((".", "?", "!", ","))):
            segments.append([line, []])
            continue
        if dash or not segments:
            segments.append([None, [line]])
        else:
            segments[-1][1].append(line)
    cues = []
    for speaker, texts in segments:
        text = " ".join(t for t in texts if t).strip()
        if text:
            cues.append(Cue(start, end, speaker, text))
    return cues


def parse_timed_blocks(text: str, name_lines: bool = False) -> list[Cue]:
    """Parse WebVTT or SRT style text: a timing line ('00:00:01.000 --> 00:00:04.000')
    followed by caption lines. Header, NOTE and STYLE blocks are skipped."""
    rolling = bool(INLINE_TS_TAG_RE.search(text))  # YouTube-style captions repeat lines
    cues: list[Cue] = []
    timing: tuple[float, float] | None = None
    payload: list[str] = []
    previous_lines: list[str] = []

    def flush() -> None:
        nonlocal timing, payload, previous_lines
        if timing is not None and payload:
            lines = payload
            if rolling:
                cleaned = [clean_markup(line) for line in payload]
                cleaned = [line for line in cleaned if line]
                current = list(cleaned)
                while cleaned and cleaned[0] in previous_lines:
                    cleaned.pop(0)
                previous_lines = current
                lines = cleaned
            cues.extend(_payload_to_cues(lines, timing[0], timing[1], name_lines))
        timing, payload = None, []

    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        match = TIMING_RE.match(line)
        if match:
            if timing is not None:
                while payload and payload[-1].isdigit():  # cue number of the next cue
                    payload.pop()
                flush()
            timing = (parse_timestamp(match["start"]), parse_timestamp(match["end"]))
            payload = []
            continue
        if not line:
            flush()
            continue
        if timing is not None:
            payload.append(line)
    flush()
    return cues


def _match_header(line: str):
    for pattern in HEADER_PATTERNS:
        match = pattern.match(line)
        if match and looks_like_speaker(match["name"]):
            return match["name"].strip(), parse_timestamp(match["ts"])
    return None


def _match_inline(line: str):
    for pattern in INLINE_PATTERNS:
        match = pattern.match(line)
        if not match:
            continue
        groups = match.groupdict()
        name = groups.get("name")
        if name is not None and not looks_like_speaker(name):
            continue
        ts = groups.get("ts")
        return (name.strip() if name else None,
                parse_timestamp(ts) if ts else None,
                groups["text"].strip())
    return None


def parse_text_transcript(text: str, info: TranscriptInfo) -> list[Cue]:
    """Parse plain-text exports (Otter, Rev, Teams, Zoom, and this script's own output)."""
    lines = text.splitlines()
    if lines and lines[0].lstrip("\ufeff").startswith("# CLEAN TRANSCRIPT"):
        lines = [line for line in lines if not line.startswith("#")]
    if sum(1 for line in lines if TIMING_RE.match(line.strip())) >= 2:
        return parse_timed_blocks("\n".join(lines), name_lines=True)

    cues: list[Cue] = []
    current: Cue | None = None
    for raw in lines:
        line = clean_markup(raw)
        if not line:
            continue
        header = _match_header(line)
        if header:
            current = Cue(header[1], None, header[0], "")
            cues.append(current)
            continue
        inline = _match_inline(line)
        if inline:
            name, start, words = inline
            current = Cue(start, None, name, words)
            cues.append(current)
            continue
        if current is None:
            current = Cue(None, None, None, line)
            cues.append(current)
        else:
            current.text = f"{current.text} {line}".strip()

    # Drop title lines before the first speaker label (Teams and Otter add a few).
    labelled = [i for i, cue in enumerate(cues) if cue.speaker]
    if len(labelled) >= 3 and labelled[0] > 0:
        info.skipped_preamble = labelled[0]
        cues = cues[labelled[0]:]
    # A turn ends where the next one starts.
    for cue, nxt in zip(cues, cues[1:]):
        if cue.end is None and cue.start is not None and nxt.start is not None and nxt.start >= cue.start:
            cue.end = nxt.start
    return [cue for cue in cues if cue.text]


# --------------------------------------------------------------------------
# Cleaning and merging
# --------------------------------------------------------------------------

def remove_fillers(text: str) -> tuple[str, int]:
    """Remove um/uh/er/erm/hmm/ah. Keeps 'uh-huh' and 'mm-hmm', which can mean yes."""
    count = len(FILLER_RE.findall(text))
    if not count:
        return text, 0
    new = FILLER_AFTER_STOP_RE.sub(lambda m: m.group(1) + m.group(2).upper(), text)
    starts_with_filler = bool(re.match(rf"^\s*{FILLER}(?![\w'’-])", new))
    new = FILLER_RE.sub("", new)
    new = re.sub(r"\s+([,.;:?!])", r"\1", new)
    new = re.sub(r",\s*([,.;:?!])", r"\1", new)
    new = re.sub(r"^[,.;:\s]+", "", new)
    new = re.sub(r"\s{2,}", " ", new).strip()
    if starts_with_filler and new[:1].islower():
        new = new[0].upper() + new[1:]
    new = re.sub(r"(^|[.?!]\s+)i\b", lambda m: m.group(1) + "I", new)
    return new, count


@dataclass
class Turn:
    start: float | None
    end: float | None
    speaker: str | None
    text: str


def merge_cues(cues: list[Cue], merge_gap: float = 8.0, split_after: float = 90.0) -> list[Turn]:
    """Join back-to-back captions from the same speaker into turns."""
    if cues and all(cue.start is not None for cue in cues):
        cues = sorted(cues, key=lambda cue: cue.start)  # stable: keeps order of equal starts
    turns: list[Turn] = []
    for cue in cues:
        last = turns[-1] if turns else None
        same = last is not None and last.speaker == cue.speaker
        close = (last is None or cue.start is None or last.end is None
                 or cue.start - last.end <= merge_gap)
        short = (last is None or cue.end is None or last.start is None
                 or cue.end - last.start <= split_after)
        if last is not None and same and close and short:
            last.text = f"{last.text} {cue.text}".strip()
            if cue.end is not None:
                last.end = max(last.end or cue.end, cue.end)
        else:
            turns.append(Turn(cue.start, cue.end, cue.speaker, cue.text))
    return turns


def load_turns(path: str | Path, speaker_map: dict[str, str] | None = None, keep_fillers: bool = False,
               merge_gap: float = 8.0, split_after: float = 90.0) -> tuple[list[Turn], TranscriptInfo]:
    """Read any supported transcript file and return cleaned speaker turns."""
    path = Path(path)
    if not path.exists():
        raise TranscriptError(f"File not found: {path}")
    text = read_docx_text(path) if path.suffix.lower() == ".docx" else read_text_file(path)
    fmt = detect_format(path, text)
    info = TranscriptInfo(source=path.name, format=fmt)
    if fmt in ("WebVTT", "SRT"):
        cues = parse_timed_blocks(text)
    else:
        cues = parse_text_transcript(text, info)
    if not cues:
        raise TranscriptError(f"No transcript text found in {path.name}. Is it a VTT, SRT, TXT or DOCX transcript?")
    info.captions = len(cues)

    mapping = speaker_map or {}
    for cue in cues:
        if cue.speaker and cue.speaker.strip().casefold() in mapping:
            cue.speaker = mapping[cue.speaker.strip().casefold()]
        if cue.start is not None and cue.end is not None and cue.end >= cue.start:
            key = cue.speaker or "Unknown speaker"
            info.speaker_seconds[key] = info.speaker_seconds.get(key, 0.0) + (cue.end - cue.start)

    turns = merge_cues(cues, merge_gap=merge_gap, split_after=split_after)
    if not keep_fillers:
        for turn in turns:
            turn.text, removed = remove_fillers(turn.text)
            info.fillers_removed += removed
    turns = [turn for turn in turns if turn.text]
    return turns, info


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def format_offset(seconds: float) -> str:
    whole = int(seconds)
    hours, rest = divmod(whole, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_clock(value: str) -> float:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value.strip())
    if not match or int(match[1]) > 23 or int(match[2]) > 59:
        raise TranscriptError(f"--clock-start must look like 19:00 or 19:00:30, not {value!r}")
    return int(match[1]) * 3600 + int(match[2]) * 60 + int(match[3] or 0)


def speaker_stats(turns: list[Turn], info: TranscriptInfo) -> list[tuple[str, int, float]]:
    words: dict[str, int] = {}
    for turn in turns:
        key = turn.speaker or "Unknown speaker"
        words[key] = words.get(key, 0) + len(turn.text.split())
    return sorted(((name, count, info.speaker_seconds.get(name, 0.0)) for name, count in words.items()),
                  key=lambda row: -row[1])


def render_text(turns: list[Turn], info: TranscriptInfo, clock_start: float | None = None) -> str:
    stats = speaker_stats(turns, info)
    timed = [t for t in turns if t.start is not None]
    length = format_offset(max((t.end or t.start) for t in timed)) if timed else "unknown"
    header = [
        "# CLEAN TRANSCRIPT",
        f"# Source: {info.source} ({info.format})",
        f"# Length: {length} | Speaker turns: {len(turns)} | Filler words removed: {info.fillers_removed}",
        "# Speakers (words): " + ", ".join(f"{name} ({count:,})" for name, count, _ in stats),
    ]
    if clock_start is not None:
        header.append(f"# Times: [recording time | clock time]. Clock times assume the recording "
                      f"started at {format_offset(clock_start)}.")
    elif timed:
        header.append("# Times in [brackets] are from the start of the recording.")
    header.append("# " + "-" * 66)
    body = []
    for turn in turns:
        stamp = ""
        if turn.start is not None:
            stamp = format_offset(turn.start)
            if clock_start is not None:
                stamp += " | " + format_offset((clock_start + turn.start) % 86400)
            stamp = f"[{stamp}] "
        body.append(f"{stamp}{turn.speaker or 'Unknown speaker'}: {turn.text}")
    return "\n".join(header) + "\n\n" + "\n\n".join(body) + "\n"


def render_json(turns: list[Turn], info: TranscriptInfo, clock_start: float | None = None) -> str:
    data = {
        "source": info.source,
        "format": info.format,
        "filler_words_removed": info.fillers_removed,
        "speakers": {name: {"words": count, "seconds": round(seconds, 1)}
                     for name, count, seconds in speaker_stats(turns, info)},
        "turns": [],
    }
    for turn in turns:
        row = {"speaker": turn.speaker or "Unknown speaker", "text": turn.text}
        if turn.start is not None:
            row["start"] = format_offset(turn.start)
            row["start_seconds"] = round(turn.start, 3)
            if clock_start is not None:
                row["clock"] = format_offset((clock_start + turn.start) % 86400)
        if turn.end is not None:
            row["end_seconds"] = round(turn.end, 3)
        data["turns"].append(row)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def report(turns: list[Turn], info: TranscriptInfo, output: str) -> str:
    lines = [f"Read {info.captions} captions or lines from {info.source} ({info.format}).",
             f"Wrote {len(turns)} speaker turns to {output}."]
    if info.skipped_preamble:
        lines.append(f"Skipped {info.skipped_preamble} title line(s) before the first speaker label.")
    lines.append("Speakers:")
    for name, count, seconds in speaker_stats(turns, info):
        talk = f"   {format_offset(seconds)} talk time" if seconds else ""
        lines.append(f"  {name:<32} {count:>6,} words{talk}")
    odd = [name for name, _, _ in speaker_stats(turns, info)
           if name == "Unknown speaker" or SUSPICIOUS_LABEL_RE.search(name) or len(name.split()) == 1]
    if odd:
        lines.append("Check these speaker labels (device names, generic labels or first names only):")
        for name in odd:
            lines.append(f"  - {name}")
        lines.append('Rename a label only when you know who it is: --speaker-map "OLD=NEW".')
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clean a VTT, SRT, TXT or DOCX meeting transcript into speaker-labelled text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:" + __doc__.split("Examples:", 1)[1],
    )
    parser.add_argument("input", help="transcript file (.vtt, .srt, .txt or .docx)")
    parser.add_argument("-o", "--output", help="output file (default: <input name>-clean.txt next to the input; '-' prints it)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format (default: text)")
    parser.add_argument("--speaker-map", action="append", metavar="OLD=NEW",
                        help="rename a speaker label; repeat for more than one")
    parser.add_argument("--speaker-map-file", action="append", metavar="FILE",
                        help="file with one OLD=NEW pair per line")
    parser.add_argument("--clock-start", metavar="HH:MM[:SS]",
                        help="clock time when the recording started; adds clock times next to recording times")
    parser.add_argument("--keep-fillers", action="store_true", help="keep um, uh, er, erm, hmm and ah")
    parser.add_argument("--merge-gap", type=float, default=8.0, metavar="SECONDS",
                        help="join captions from the same speaker if the pause is at most this long (default 8)")
    parser.add_argument("--split-after", type=float, default=90.0, metavar="SECONDS",
                        help="start a new paragraph after this many seconds of one speaker (default 90)")
    parser.add_argument("-q", "--quiet", action="store_true", help="don't print the speaker summary")
    args = parser.parse_args(argv)

    try:
        mapping = parse_speaker_map(args.speaker_map, args.speaker_map_file)
        clock = parse_clock(args.clock_start) if args.clock_start else None
        turns, info = load_turns(args.input, mapping, args.keep_fillers, args.merge_gap, args.split_after)
    except TranscriptError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    content = render_json(turns, info, clock) if args.format == "json" else render_text(turns, info, clock)
    if args.output == "-":
        sys.stdout.write(content)
        output_name = "standard output"
    else:
        source = Path(args.input)
        suffix = ".json" if args.format == "json" else ".txt"
        out_path = Path(args.output) if args.output else source.with_name(f"{source.stem}-clean{suffix}")
        if out_path.resolve() == source.resolve():
            print("Error: the output file would overwrite the input. Choose another name with -o.", file=sys.stderr)
            return 1
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        output_name = str(out_path)
    if not args.quiet:
        print(report(turns, info, output_name), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
