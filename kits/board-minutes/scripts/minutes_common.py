"""Shared code for the board-minutes scripts.

build_minutes.py, check_minutes.py and the tests import this file.
You don't run it directly.

It loads and validates the minutes JSON (see SCHEMA.md), formats dates and
times, finds [UNCLEAR] markers and builds the standard sentences used in the
minutes (vote lines, quorum statement, next meeting, and so on).
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Iterator

SCRIPTS_DIR = Path(__file__).resolve().parent
KIT_DIR = SCRIPTS_DIR.parent
SCHEMA_PATH = SCRIPTS_DIR / "minutes.schema.json"
SCHEMA_VERSION = "1.0"

# "[UNCLEAR]" or "[UNCLEAR: short note]"
UNCLEAR_RE = re.compile(r"\[UNCLEAR(?:[:\s][^\[\]]*)?\]")

# Field names that hold a time, used to give clearer validation hints.
_TIME_FIELDS = {"called_to_order", "adjourned", "scheduled_time", "arrived", "left", "start", "end", "time"}
_DATE_FIELDS = {"date", "prepared_on", "approved_on"}


class MinutesError(Exception):
    """A problem the user needs to fix (bad file, invalid JSON, and so on)."""


# --------------------------------------------------------------------------
# Loading and validation
# --------------------------------------------------------------------------

def load_minutes(path: str | Path) -> dict:
    """Read a minutes JSON file and return it as a dict."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise MinutesError(f"File not found: {path}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MinutesError(
            f"{path.name} is not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from None
    if not isinstance(data, dict):
        raise MinutesError(f"{path.name} must contain a JSON object at the top level.")
    return data


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def format_path(parts) -> str:
    """Turn ['items', 3, 'motions', 0] into $.items[3].motions[0]."""
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out


def _hint(error) -> str:
    field = next((p for p in reversed(list(error.absolute_path)) if isinstance(p, str)), "")
    if field in _TIME_FIELDS:
        return " Use 24-hour HH:MM (for example 19:02) or [UNCLEAR]."
    if field in _DATE_FIELDS or field == "due":
        return " Use YYYY-MM-DD (for example 2026-09-16) or [UNCLEAR]."
    if field == "source":
        return " Use the recording time, for example 00:12:40 or 00:12:40-00:15:05."
    return ""


def schema_errors(data: dict) -> list[str]:
    """Return a list of readable schema errors (empty if the JSON is valid)."""
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - only when requirements are missing
        raise MinutesError(
            "The 'jsonschema' package is missing. Install the kit requirements: "
            "pip install -r requirements.txt"
        ) from None
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    messages = []
    for err in errors:
        message = err.message
        if err.validator in ("anyOf", "oneOf"):
            message = f"{err.instance!r} is not an allowed value here."
        messages.append(f"{format_path(err.absolute_path)}: {message}{_hint(err)}")
    return messages


# --------------------------------------------------------------------------
# Small accessors with defaults
# --------------------------------------------------------------------------

def locale_of(m: dict) -> str:
    return (m.get("document") or {}).get("locale", "en-US")


def status_of(m: dict) -> str:
    return (m.get("document") or {}).get("status", "draft")


def is_confidential(m: dict) -> bool:
    doc = m.get("document") or {}
    if "confidential" in doc:
        return bool(doc["confidential"])
    return status_of(m) == "draft"


def board_name(m: dict) -> str:
    return (m.get("organization") or {}).get("board_name", "Board of Directors")


def board_short(m: dict) -> str:
    return (m.get("organization") or {}).get("board_short", "Board")


def group_label(m: dict) -> str:
    """Plural word for board members, e.g. 'Directors' or 'Trustees'."""
    return (m.get("attendance") or {}).get("group_label", "Directors")


def word(locale: str, us: str, gb: str) -> str:
    return gb if locale == "en-GB" else us


# --------------------------------------------------------------------------
# Dates and times
# --------------------------------------------------------------------------

def parse_date(value: Any) -> dt.date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def parse_time(value: Any) -> dt.time | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value)
    return dt.time(int(match[1]), int(match[2])) if match else None


_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"]
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def format_date(value: Any, locale: str = "en-US", weekday: bool = True) -> str:
    """'2026-09-16' -> 'Wednesday, September 16, 2026' (US) or 'Wednesday 16 September 2026' (UK).

    Anything that is not a YYYY-MM-DD date (for example '[UNCLEAR]') is returned unchanged.
    """
    d = parse_date(value)
    if d is None:
        return "" if value is None else str(value)
    month, day_name = _MONTHS[d.month - 1], _WEEKDAYS[d.weekday()]
    if locale == "en-GB":
        core = f"{d.day} {month} {d.year}"
        return f"{day_name} {core}" if weekday else core
    core = f"{month} {d.day}, {d.year}"
    return f"{day_name}, {core}" if weekday else core


def format_time(value: Any, locale: str = "en-US") -> str:
    """'19:02' -> '7:02 p.m.' (US) or '7.02pm' (UK). Other values are returned unchanged."""
    t = parse_time(value)
    if t is None:
        return "" if value is None else str(value)
    hour = t.hour % 12 or 12
    if locale == "en-GB":
        return f"{hour}.{t.minute:02d}{'am' if t.hour < 12 else 'pm'}"
    return f"{hour}:{t.minute:02d} {'a.m.' if t.hour < 12 else 'p.m.'}"


def source_seconds(value: Any) -> float | None:
    """'00:12:40' or '12:40' (or the first part of a range) -> seconds."""
    if not isinstance(value, str):
        return None
    first = re.split(r"\s*[-–]\s*", value.strip())[0]
    parts = first.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return None


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def smart_quotes(text: str) -> str:
    """Turn straight quotes into typographic ones: don't -> don’t, "x" -> “x”."""
    if not text or ("'" not in text and '"' not in text):
        return text
    text = re.sub(r"(?<=\w)'(?=\w)", "’", text)
    text = re.sub(r"(^|[\s(\[{—–/-])'", lambda m: m.group(1) + "‘", text)
    text = text.replace("'", "’")
    text = re.sub(r'(^|[\s(\[{—–/-])"', lambda m: m.group(1) + "“", text)
    return text.replace('"', "”")


def iter_strings(obj: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    """Yield (json_path, text) for every string in the data, skipping '_' keys."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.startswith("_"):
                continue
            yield from iter_strings(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from iter_strings(value, f"{path}[{index}]")
    elif isinstance(obj, str):
        yield path, obj


def find_unclear(m: dict) -> list[tuple[str, str]]:
    """List every [UNCLEAR] marker as (json_path, marker), outside the questions list."""
    found = []
    for path, text in iter_strings(m):
        if path.startswith("$.questions"):
            continue
        for marker in UNCLEAR_RE.findall(text):
            found.append((path, marker))
    return found


_TITLE_WORDS = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "director", "president", "treasurer", "secretary",
    "vice", "chair", "chairman", "chairwoman", "chairperson", "pastor", "rev", "reverend",
    "father", "trustee", "member", "councillor", "councilor", "elder", "deacon",
}


def normalize_name(name: str) -> str:
    """Lower-case a name and drop titles and punctuation, for comparisons."""
    cleaned = re.sub(r"[^\w\s'-]", " ", (name or "").lower())
    return " ".join(t for t in cleaned.split() if t not in _TITLE_WORDS)


def person_text(person: Any, locale: str = "en-US", details: bool = True) -> str:
    """{'name': 'Helen Whitaker', 'role': 'Director', 'arrived': '19:14'} ->
    'Helen Whitaker, Director (arrived 7:14 p.m.)'."""
    if not person:
        return ""
    if isinstance(person, str):
        return person
    text = person.get("name", "")
    if person.get("role"):
        text += f", {person['role']}"
    if details:
        extra = []
        attended = person.get("attended")
        if attended == "remote":
            extra.append("by video")
        elif attended == "phone":
            extra.append("by phone")
        elif attended == "in_person":
            extra.append("in person")
        if person.get("arrived"):
            extra.append(f"arrived {format_time(person['arrived'], locale)}")
        if person.get("left"):
            extra.append(f"left {format_time(person['left'], locale)}")
        if person.get("note"):
            extra.append(person["note"])
        if extra:
            text += f" ({'; '.join(extra)})"
    return text


def role_and_name(person: Any) -> str:
    """{'name': 'Diane Okafor', 'role': 'President'} -> 'President Diane Okafor'."""
    if not person:
        return ""
    if isinstance(person, str):
        return person
    role = person.get("role", "")
    # Only short, title-like roles read well before a name.
    if role and len(role.split()) <= 3 and "," not in role:
        return f"{role} {person.get('name', '')}".strip()
    return person.get("name", "")


# --------------------------------------------------------------------------
# Items and motions
# --------------------------------------------------------------------------

def item_heading(item: dict) -> str:
    number = str(item.get("number") or "").strip()
    title = str(item.get("title") or "").strip()
    if not number:
        return title
    if number[-1] in ".):":
        return f"{number} {title}"
    return f"{number}. {title}"


def iter_motions(m: dict) -> Iterator[tuple[int, dict, dict]]:
    """Yield (number, item, motion) for every motion in document order, numbered from 1."""
    number = 0
    for item in m.get("items") or []:
        for motion in item.get("motions") or []:
            number += 1
            yield number, item, motion


def motion_label(number: int, motion: dict) -> str:
    return motion.get("label") or f"Motion {number}"


RESULT_LABELS = {
    "carried": "Carried",
    "failed": "Failed",
    "withdrawn": "Withdrawn",
    "tabled": "Tabled",
    "postponed": "Postponed",
    "referred": "Referred",
    "ruled_out_of_order": "Ruled out of order",
    "no_vote": "No vote taken",
    "[UNCLEAR]": "[UNCLEAR]",
}

METHOD_LABELS = {
    "voice": "voice vote",
    "show_of_hands": "show of hands",
    "roll_call": "roll call vote",
    "ballot": "ballot",
    "unanimous_consent": "unanimous consent",
    "electronic": "electronic vote",
    "[UNCLEAR]": "method [UNCLEAR]",
}


def result_label(result: str | None) -> str:
    return RESULT_LABELS.get(result or "", result or "")


def vote_counts_text(vote: dict | None, locale: str = "en-US") -> str:
    """'4 in favor, 1 opposed, 0 abstained (roll call vote)', 'Unanimous (voice vote)', ..."""
    if not vote:
        return ""
    counts = []
    if vote.get("in_favor") is not None:
        counts.append(f"{vote['in_favor']} in {word(locale, 'favor', 'favour')}")
    if vote.get("opposed") is not None:
        counts.append(f"{vote['opposed']} opposed")
    if vote.get("abstained") is not None:
        counts.append(f"{vote['abstained']} abstained")
    text = ", ".join(counts)
    if vote.get("unanimous"):
        text = f"{text} (unanimous)" if text else "Unanimous"
    method = vote.get("method")
    if method == "unanimous_consent" and not counts:
        return "By unanimous consent"
    if method:
        label = METHOD_LABELS.get(method, method)
        text = f"{text} ({label})" if text else label[0].upper() + label[1:]
    return text


_ROLL_WORDS = {"yes": "yes", "no": "no", "abstain": "abstained", "recused": "recused",
               "absent": "absent", "[UNCLEAR]": "[UNCLEAR]"}


def roll_call_text(vote: dict | None) -> str:
    if not vote or not vote.get("roll_call"):
        return ""
    return "; ".join(f"{entry['name']}: {_ROLL_WORDS.get(entry['vote'], entry['vote'])}"
                     for entry in vote["roll_call"])


def roll_call_counts(vote: dict) -> dict[str, int]:
    counts = {"yes": 0, "no": 0, "abstain": 0, "recused": 0, "absent": 0, "[UNCLEAR]": 0}
    for entry in vote.get("roll_call") or []:
        counts[entry["vote"]] = counts.get(entry["vote"], 0) + 1
    return counts


# --------------------------------------------------------------------------
# Standard sentences
# --------------------------------------------------------------------------

def quorum_text(m: dict) -> str:
    """The quorum line for the attendance block."""
    quorum = (m.get("attendance") or {}).get("quorum") or {}
    if quorum.get("statement"):
        return quorum["statement"]
    met = quorum.get("met")
    if met is None:
        return "[UNCLEAR] Whether a quorum was present was not stated."
    label = group_label(m).lower()
    details = []
    if quorum.get("present_count") is not None and quorum.get("board_size"):
        details.append(f"{quorum['present_count']} of {quorum['board_size']} {label} present")
    elif quorum.get("present_count") is not None:
        details.append(f"{quorum['present_count']} {label} present")
    if quorum.get("required"):
        details.append(f"{quorum['required']} required")
    head = "A quorum was present" if met else "A quorum was not present"
    return f"{head} ({'; '.join(details)})." if details else f"{head}."


def auto_item_text(m: dict, item: dict) -> list[str]:
    """Standard wording for items that have no summary of their own."""
    locale = locale_of(m)
    meeting = m.get("meeting") or {}
    kind = item.get("kind", "business")
    if kind == "call_to_order":
        who = role_and_name(meeting.get("presiding")) or "The presiding officer"
        return [f"{who} called the meeting to order at {format_time(meeting.get('called_to_order'), locale)}."]
    if kind == "roll_call":
        return [quorum_text(m)]
    if kind == "adjournment":
        return [f"The meeting was adjourned at {format_time(meeting.get('adjourned'), locale)}."]
    if kind == "next_meeting":
        return [next_meeting_text(m)]
    if kind == "executive_session":
        return [executive_session_text(m, item)]
    return []


def executive_session_text(m: dict, item: dict) -> str:
    locale = locale_of(m)
    sentence = f"The {board_short(m)} met in executive session"
    start, end = item.get("start"), item.get("end")
    if start and end:
        sentence += f" from {format_time(start, locale)} to {format_time(end, locale)}"
    elif start:
        sentence += f" at {format_time(start, locale)}"
    topics = item.get("topics") or []
    if topics:
        if len(topics) == 1:
            joined = topics[0]
        else:
            joined = ", ".join(topics[:-1]) + " and " + topics[-1]
        sentence += f" to discuss {joined}"
    return sentence + "."


def next_meeting_text(m: dict) -> str:
    locale = locale_of(m)
    nxt = m.get("next_meeting")
    if not nxt:
        return "Next meeting: [UNCLEAR] No date was stated."
    description = nxt.get("description", "meeting")
    text = f"The next {description} of the {board_short(m)} will be held"
    if nxt.get("date"):
        text += f" on {format_date(nxt['date'], locale)}"
    if nxt.get("time"):
        text += f", at {format_time(nxt['time'], locale)}"
    if nxt.get("location"):
        location = nxt["location"]
        joiner = "" if re.match(r"(?i)(by|via|online|at|in|on)\b", location) else "at "
        text += f", {joiner}{location}"
    text += "."
    if nxt.get("note"):
        text += f" {nxt['note']}"
    return text


def when_where_line(m: dict) -> str:
    """'Wednesday, September 16, 2026 · 7:00 p.m. · By Zoom videoconference'."""
    locale = locale_of(m)
    meeting = m.get("meeting") or {}
    parts = [format_date(meeting.get("date"), locale)]
    if meeting.get("scheduled_time"):
        parts.append(format_time(meeting["scheduled_time"], locale))
    if meeting.get("location"):
        parts.append(meeting["location"])
    return " · ".join(p for p in parts if p)


def status_line(m: dict) -> str:
    locale = locale_of(m)
    if status_of(m) == "approved":
        approved_on = (m.get("document") or {}).get("approved_on")
        if approved_on:
            return f"Approved by the {board_name(m)} on {format_date(approved_on, locale, weekday=False)}"
        return f"Approved by the {board_name(m)}"
    return f"Draft minutes, subject to approval by the {board_name(m)}"


def people_list(people: list | None, locale: str = "en-US") -> str:
    if not people:
        return "None"
    return "; ".join(person_text(p, locale) for p in people)
