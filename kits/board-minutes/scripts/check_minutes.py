#!/usr/bin/env python3
"""Check a minutes JSON file before delivery, and list the questions for the secretary.

Checks on the JSON:
  * it matches the minutes format (SCHEMA.md)
  * times and dates make sense (adjournment after call to order, next meeting
    after this one, due dates not before the meeting)
  * quorum numbers add up
  * every motion has a mover and a seconder (or a note saying why there is no second)
  * vote counts add up and match the result; roll calls match the counts
  * movers, seconders and voters are directors who were present
  * action items have an owner and a due date
  * every [UNCLEAR] marker is covered by a question for the secretary
  * no leftover TODO, ???, [INAUDIBLE] or similar
With --transcript (the cleaned transcript or the original VTT/SRT/TXT/DOCX):
  * names in the minutes appear in the transcript
  * dollar amounts in the minutes appear in the transcript
  * the number of votes called in the transcript matches the votes in the minutes
  * residents who spoke are not named in the minutes (a reminder only)

Exit code: 0 = no errors (warnings allowed), 1 = errors (or any warning with --strict).

Examples:
  python check_minutes.py minutes.json
  python check_minutes.py minutes.json --transcript transcript-clean.txt --questions-out questions.md
  python check_minutes.py --scan transcript-clean.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from clean_transcript import TranscriptError, format_offset, load_turns
from minutes_common import (
    UNCLEAR_RE,
    MinutesError,
    find_unclear,
    format_date,
    format_time,
    item_heading,
    iter_motions,
    iter_strings,
    load_minutes,
    locale_of,
    motion_label,
    normalize_name,
    parse_date,
    parse_time,
    roll_call_counts,
    schema_errors,
    source_seconds,
    status_of,
)

LEFTOVER_ERROR_RE = re.compile(r"\bTODO\b|\bXXX\b|lorem ipsum|REPLACE ME", re.I)
LEFTOVER_WARN_RE = re.compile(r"\?\?\?|\[\s*inaudible\s*\]|\[\?\]|\bTBD\b|\[\s*crosstalk\s*\]", re.I)
GROUP_WORDS_RE = re.compile(
    r"(?i)\b(committee|board|management|manager|company|co\.|inc\.?|llc|ltd|association|staff|"
    r"office|team|council|vestry|session|attorney|counsel|treasurer|secretary|president|all directors)\b")
AMOUNT_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?")
TRANSCRIPT_NUMBER_RE = re.compile(r"\$?\s?\d[\d,]*(?:\.\d+)?")
VOTE_CALL_RE = re.compile(
    r"(?i)\b(all (?:those )?in favou?r|those in favou?r|roll[- ]call|please say aye|by show of hands)\b")

SCAN_PATTERNS = [
    ("MOTION", re.compile(r"(?i)\b(i (?:would like to |'d like to |want to |will |'ll )?move\b|so moved|"
                          r"move (?:that|to|we)\b|motion to\b|entertain a motion|is there a motion|"
                          r"make a motion|committee'?s? (?:motion|recommendation))")),
    ("SECOND", re.compile(r"(?i)(^(?:i'?ll |i )?second(?:ed)?\b|\bseconded by\b|\bi'll second\b|\bi second\b)")),
    ("VOTE", re.compile(r"(?i)\b(all (?:those )?in favou?r|those in favou?r|any opposed|opposed\?|"
                        r"abstentions?|abstaining|roll[- ]call|please say aye|show of hands)\b")),
    ("RESULT", re.compile(r"(?i)\b(motion (?:carries|carried|passes|passed|fails|failed)|"
                          r"(?:that|it|this) (?:carries|passes|fails)|carries|unanimous(?:ly)?|"
                          r"approved as|(?:is|are) approved|\d+ to \d+|"
                          r"(?:one|two|three|four|five|six|seven|eight|nine|ten),? (?:to )?"
                          r"(?:nothing|zero|none|one|two|three|four|five))\b")),
    ("TASK", re.compile(r"(?i)\b(i'?ll (?:send|get|call|follow up|reach out|email|put|sign|check|draft|"
                        r"schedule|contact|ask|look|have|let|make sure|take care)|will (?:send|get|follow up|"
                        r"reach out|email)|by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
                        r"tomorrow|next week|the end of)|action item|can (?:you|somebody|someone) "
                        r"(?:get|send|look|check))\b")),
    ("CLOSED", re.compile(r"(?i)\b(executive session|closed session|in camera|attorney[- ]client)\b")),
    ("TIME", re.compile(r"(?i)\b(call(?:ing|ed)? (?:this|the) [\w\s]{0,80}?to order|adjourn(?:ed)?|"
                        r"it'?s \d{1,2}:\d{2}|it is \d{1,2}:\d{2})")),
    ("PEOPLE", re.compile(r"(?i)\b(just joined|i'?m here|has left|had to leave|dropping off|quorum|"
                          r"recuse|abstain(?:ing)? on)\b")),
    ("RECORDING", re.compile(r"(?i)\b(recording|being recorded|we record)\b")),
]


@dataclass
class Finding:
    level: str  # "error" or "warning"
    where: str
    message: str


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _names_present(m: dict) -> set[str]:
    attendance = m["attendance"]
    return {normalize_name(p["name"]) for p in attendance["directors_present"]}


def _all_attendee_names(m: dict) -> set[str]:
    attendance = m["attendance"]
    people = (attendance["directors_present"] + (attendance.get("directors_absent") or [])
              + (attendance.get("others_present") or []))
    return {normalize_name(p["name"]) for p in people}


def _is_unclear(value) -> bool:
    return isinstance(value, str) and bool(UNCLEAR_RE.search(value))


def _matches_person(name: str, known: set[str]) -> bool:
    target = normalize_name(name)
    if not target:
        return False
    if target in known:
        return True
    # "Director Bell" or "Bell" against "marcus bell"
    return any(k.split()[-1] == target.split()[-1] and len(target.split()) == 1 for k in known if k)


def _amount_key(text: str) -> str:
    digits = text.replace("$", "").replace(",", "").strip()
    if "." in digits:
        digits = digits.rstrip("0").rstrip(".")
    return digits


def _where_item(item: dict) -> str:
    return f"Item {item['number']}" if item.get("number") else f"Item '{item.get('title', '')}'"


# --------------------------------------------------------------------------
# Checks on the JSON
# --------------------------------------------------------------------------

def check_minutes(m: dict, today: dt.date | None = None) -> list[Finding]:
    findings: list[Finding] = []

    def error(where, message):
        findings.append(Finding("error", where, message))

    def warn(where, message):
        findings.append(Finding("warning", where, message))

    problems = schema_errors(m)
    if problems:
        return [Finding("error", "format", p) for p in problems]

    today = today or dt.date.today()
    locale = locale_of(m)
    meeting, attendance = m["meeting"], m["attendance"]
    board_vote = meeting.get("voting_body", "board") == "board"
    present = _names_present(m)
    attendees = _all_attendee_names(m)

    # Leftover placeholders ------------------------------------------------
    for path, text in iter_strings(m):
        if LEFTOVER_ERROR_RE.search(text):
            error(path, f"Leftover placeholder text: {text!r}.")
        elif LEFTOVER_WARN_RE.search(text):
            warn(path, f"{text!r}: use [UNCLEAR] (and add a question) for anything you could not hear or confirm.")

    # Dates and times --------------------------------------------------------
    meeting_date = parse_date(meeting["date"])
    if meeting_date is None:
        error("meeting.date", f"{meeting['date']!r} is not a real date.")
    elif meeting_date > today:
        warn("meeting.date", f"The meeting date {meeting['date']} is in the future. Is it right?")
    start, end = parse_time(meeting.get("called_to_order")), parse_time(meeting.get("adjourned"))
    if start and end and end <= start:
        error("meeting", f"Adjourned at {meeting['adjourned']} is not after the call to order at "
                         f"{meeting['called_to_order']}.")
    document = m.get("document") or {}
    for key in ("prepared_on", "approved_on"):
        value = parse_date(document.get(key))
        if document.get(key) and value is None:
            error(f"document.{key}", f"{document[key]!r} is not a real date.")
        elif value and meeting_date and value < meeting_date:
            error(f"document.{key}", f"{document[key]} is before the meeting date.")
    if status_of(m) == "approved" and not document.get("approved_on"):
        warn("document.approved_on", "Status is 'approved' but approved_on (the board's approval date) is missing.")

    for group in ("directors_present", "directors_absent", "others_present"):
        for person in attendance.get(group) or []:
            for key in ("arrived", "left"):
                value = parse_time(person.get(key))
                if value and start and end and not (start <= value <= end):
                    warn(f"attendance.{group}", f"{person['name']} {key} at {person[key]}, outside the meeting "
                                                f"({meeting['called_to_order']}-{meeting['adjourned']}).")

    # Attendance and quorum ---------------------------------------------------
    present_list = [normalize_name(p["name"]) for p in attendance["directors_present"]]
    for name in {n for n in present_list if present_list.count(n) > 1}:
        error("attendance.directors_present", f"{name!r} is listed twice.")
    absent = {normalize_name(p["name"]) for p in attendance.get("directors_absent") or []}
    for name in present & absent:
        error("attendance", f"{name!r} is listed as both present and absent.")
    quorum = attendance["quorum"]
    count = quorum.get("present_count")
    if count is not None and count > len(attendance["directors_present"]):
        error("attendance.quorum", f"present_count is {count} but only {len(attendance['directors_present'])} "
                                   "directors are listed as present.")
    if quorum.get("met") is True and count is not None and quorum.get("required") and count < quorum["required"]:
        error("attendance.quorum", f"Quorum marked as met, but {count} present is fewer than the "
                                   f"{quorum['required']} required.")
    if quorum.get("met") is False and count is not None and quorum.get("required") and count >= quorum["required"]:
        warn("attendance.quorum", "Quorum marked as not met although the numbers say it was. Check.")
    if quorum.get("met") is None:
        warn("attendance.quorum", "Whether a quorum was present is unclear. Ask the secretary.")
    if quorum.get("met") is False and any(True for _ in iter_motions(m)):
        warn("attendance.quorum", "No quorum, but motions are recorded. Without a quorum a board usually "
                                  "cannot act; ask the client how to record these.")
    size = quorum.get("board_size")
    listed = len(attendance["directors_present"]) + len(attendance.get("directors_absent") or [])
    if size and listed != size:
        warn("attendance", f"Board size is {size} but {listed} directors are listed (present + absent).")
    if board_vote and not _matches_person(meeting["presiding"]["name"], present):
        warn("meeting.presiding", f"{meeting['presiding']['name']} is presiding but is not listed as a "
                                  "director present.")

    # Items ----------------------------------------------------------------------
    items = m["items"]
    kinds = [item.get("kind", "business") for item in items]
    if "approval_of_minutes" not in kinds:
        warn("items", "No 'approval_of_minutes' item. Check whether prior minutes were approved at this meeting.")
    if "adjournment" not in kinds:
        warn("items", "No 'adjournment' item. Minutes should end with the adjournment time.")
    numbers = [str(item.get("number")).strip().lower() for item in items if item.get("number")]
    for number in {n for n in numbers if numbers.count(n) > 1}:
        warn("items", f"Item number {number!r} is used more than once.")
    for item in items:
        where = _where_item(item)
        kind = item.get("kind", "business")
        has_content = item.get("summary") or item.get("motions")
        auto_kinds = {"call_to_order", "roll_call", "adjournment", "next_meeting", "executive_session"}
        if kind not in auto_kinds | {"heading"} and not has_content:
            warn(where, f"'{item_heading(item)}' has no summary and no motions.")
        if kind == "executive_session":
            words = sum(len(s.split()) for s in item.get("summary") or [])
            if words > 40:
                warn(where, f"The executive session summary has {words} words. Record only what the bylaws "
                            "allow (usually the time, the general topic and any vote).")
            if not item.get("topics") and not item.get("summary"):
                warn(where, "Executive session without 'topics' (the general nature of the business).")
            for key in ("start", "end"):
                value = parse_time(item.get(key))
                if value and start and end and not (start <= value <= end):
                    warn(where, f"Executive session {key} {item[key]} is outside the meeting times.")
        summary_text = " ".join(item.get("summary") or [])
        if kind == "call_to_order" and summary_text and start:
            if format_time(meeting["called_to_order"], locale) not in summary_text:
                warn(where, f"The call to order text does not mention {format_time(meeting['called_to_order'], locale)}"
                            " (meeting.called_to_order).")
        if kind == "adjournment" and summary_text and end:
            if format_time(meeting["adjourned"], locale) not in summary_text:
                warn(where, f"The adjournment text does not mention {format_time(meeting['adjourned'], locale)}"
                            " (meeting.adjourned).")

    # Motions ------------------------------------------------------------------------
    for number, item, motion in iter_motions(m):
        where = f"{_where_item(item)}, {motion_label(number, motion)}"
        _check_motion(motion, where, present, board_vote, len(attendance["directors_present"]), error, warn)
        for index, amendment in enumerate(motion.get("amendments") or [], start=1):
            _check_motion(amendment, f"{where}, amendment {index}", present, board_vote,
                          len(attendance["directors_present"]), error, warn)

    # Action items -------------------------------------------------------------------
    for index, action in enumerate(m.get("action_items") or [], start=1):
        where = f"Action item {index}"
        owner = action["owner"]
        if _is_unclear(owner):
            warn(where, "Owner is [UNCLEAR]; make sure a question asks who owns it.")
        elif not GROUP_WORDS_RE.search(owner) and not _matches_person(owner, attendees):
            warn(where, f"Owner {owner!r} is not in the attendance lists. Check the spelling or the roster.")
        due = parse_date(action["due"])
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", action["due"]) and due is None:
            error(where, f"Due date {action['due']!r} is not a real date.")
        elif due and meeting_date and due < meeting_date:
            warn(where, f"Due date {action['due']} is before the meeting.")

    nxt = m.get("next_meeting")
    if nxt and parse_date(nxt.get("date")) and meeting_date and parse_date(nxt["date"]) <= meeting_date:
        warn("next_meeting", f"Next meeting date {nxt['date']} is not after this meeting.")
    if "next_meeting" not in m:
        warn("next_meeting", "No next_meeting. If a date was announced, add it; if not, set it to null.")

    # [UNCLEAR] markers and questions --------------------------------------------------
    markers = find_unclear(m)
    questions = m.get("questions") or []
    if markers and not questions:
        error("questions", f"{len(markers)} [UNCLEAR] marker(s) but no questions for the secretary.")
    elif len(markers) > len(questions):
        warn("questions", f"{len(markers)} [UNCLEAR] markers but only {len(questions)} questions. "
                          "Make sure every marker is covered.")
    if markers and status_of(m) == "approved":
        error("document.status", "Approved minutes cannot contain [UNCLEAR] markers.")
    return findings


def _check_motion(motion: dict, where: str, present: set[str], board_vote: bool, present_count: int,
                  error, warn) -> None:
    vote = motion.get("vote") or {}
    result = motion.get("result")
    mover, seconder = motion.get("moved_by"), motion.get("seconded_by")
    if not mover and vote.get("method") != "unanimous_consent" and not motion.get("on_behalf_of"):
        warn(where, "No mover recorded (moved_by is null).")
    if not seconder and not motion.get("second_note") and vote.get("method") != "unanimous_consent":
        warn(where, "No seconder recorded. If none was needed (for example a committee motion), "
                    "say so in second_note.")
    if mover and seconder and not _is_unclear(mover) and normalize_name(mover) == normalize_name(seconder):
        error(where, f"{mover} is recorded as both mover and seconder.")
    for role, name in (("Mover", mover), ("Seconder", seconder)):
        if name and not _is_unclear(name) and board_vote and not _matches_person(name, present):
            warn(where, f"{role} {name!r} is not a director listed as present. Check the name.")
    if _is_unclear(mover) or _is_unclear(seconder):
        warn(where, "Mover or seconder is [UNCLEAR]; make sure a question covers it.")
    if result == "[UNCLEAR]":
        warn(where, "Result is [UNCLEAR]; make sure a question covers it.")

    has_vote = any(vote.get(k) is not None for k in ("in_favor", "opposed", "abstained")) or \
        vote.get("unanimous") or vote.get("method") or vote.get("roll_call")
    if result in ("carried", "failed") and not has_vote:
        warn(where, f"Result is '{result}' but no vote is recorded (method, counts or 'unanimous').")
    in_favor, opposed, abstained = vote.get("in_favor"), vote.get("opposed"), vote.get("abstained")
    total = sum(n for n in (in_favor, opposed, abstained) if n is not None)
    if board_vote and total > present_count:
        error(where, f"Vote total {total} is more than the {present_count} directors present.")
    if vote.get("unanimous") and opposed:
        error(where, "Marked unanimous but someone voted against.")
    threshold = motion.get("threshold", "majority")
    if in_favor is not None and opposed is not None and result in ("carried", "failed"):
        if threshold == "majority":
            if result == "carried" and in_favor <= opposed:
                error(where, f"Recorded as carried, but {in_favor} for and {opposed} against is not a majority.")
            if result == "failed" and in_favor > opposed:
                error(where, f"Recorded as failed, but {in_favor} for and {opposed} against is a majority.")
        elif threshold == "two_thirds":
            if result == "carried" and in_favor < 2 * opposed:
                error(where, f"Recorded as carried, but {in_favor}-{opposed} is not a two-thirds vote.")
        elif threshold == "unanimous" and result == "carried" and opposed:
            error(where, "Needs a unanimous vote but someone voted against.")
    if vote.get("method") == "roll_call" and not vote.get("roll_call"):
        warn(where, "Roll call vote without the list of names and votes (vote.roll_call).")
    if vote.get("roll_call"):
        counts = roll_call_counts(vote)
        names = [normalize_name(entry["name"]) for entry in vote["roll_call"]]
        for name in {n for n in names if names.count(n) > 1}:
            error(where, f"{name!r} appears twice in the roll call.")
        for key, field in (("yes", "in_favor"), ("no", "opposed"), ("abstain", "abstained")):
            if vote.get(field) is not None and vote[field] != counts[key]:
                error(where, f"{field} is {vote[field]} but the roll call has {counts[key]} '{key}' votes.")
        for entry in vote["roll_call"]:
            if board_vote and not _is_unclear(entry["name"]) and not _matches_person(entry["name"], present):
                warn(where, f"Roll call name {entry['name']!r} is not a director listed as present.")


# --------------------------------------------------------------------------
# Checks against the transcript
# --------------------------------------------------------------------------

def check_against_transcript(m: dict, turns: list) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    notes: list[str] = []
    transcript_text = " ".join(f"{t.speaker or ''} {t.text}" for t in turns)
    lowered = transcript_text.lower()
    speakers = {t.speaker for t in turns if t.speaker}

    # Names ---------------------------------------------------------------------
    names: dict[str, str] = {}
    meeting, attendance = m["meeting"], m["attendance"]
    for person in [meeting.get("presiding"), meeting.get("recording_secretary")] + \
            attendance["directors_present"] + (attendance.get("directors_absent") or []) + \
            (attendance.get("others_present") or []):
        if person:
            names.setdefault(normalize_name(person["name"]), person["name"])
    for _, _, motion in iter_motions(m):
        for key in ("moved_by", "seconded_by"):
            if motion.get(key):
                names.setdefault(normalize_name(motion[key]), motion[key])
        for entry in (motion.get("vote") or {}).get("roll_call") or []:
            names.setdefault(normalize_name(entry["name"]), entry["name"])
    for action in m.get("action_items") or []:
        if not GROUP_WORDS_RE.search(action["owner"]):
            names.setdefault(normalize_name(action["owner"]), action["owner"])
    for key, name in names.items():
        if not key or _is_unclear(name):
            continue
        surname = key.split()[-1]
        in_text = re.search(rf"\b{re.escape(surname)}\b", lowered) is not None
        in_labels = any(normalize_name(s) == key for s in speakers)
        if not (in_text or in_labels):
            findings.append(Finding("warning", "names", f"{name!r} does not appear in the transcript. "
                                    "Check the spelling against the roster."))

    # Amounts -------------------------------------------------------------------
    transcript_amounts = {_amount_key(a) for a in TRANSCRIPT_NUMBER_RE.findall(transcript_text)}
    seen = set()
    for path, text in iter_strings(m):
        if path.startswith("$.questions"):
            continue
        for amount in AMOUNT_RE.findall(text):
            key = _amount_key(amount)
            if key and key not in transcript_amounts and key not in seen:
                seen.add(key)
                findings.append(Finding("warning", path, f"{amount.strip()} is not in the transcript as digits. "
                                        "Check the figure (ignore this if it was spoken in words or comes "
                                        "from a document the client sent)."))

    # Vote calls ----------------------------------------------------------------
    calls: list[float] = []
    for turn in turns:
        if turn.start is None or not VOTE_CALL_RE.search(turn.text):
            continue
        if calls and turn.start - calls[-1] < 45:
            continue
        calls.append(turn.start)
    voted = 0
    for _, _, motion in iter_motions(m):
        for entry in [motion] + list(motion.get("amendments") or []):
            vote = entry.get("vote") or {}
            if vote.get("method") == "unanimous_consent":
                continue
            if vote or entry.get("result") in ("carried", "failed"):
                voted += 1
    if calls:
        stamps = ", ".join(format_offset(c) for c in calls)
        notes.append(f"Votes called in the transcript: {len(calls)} ({stamps}). Votes in the minutes: {voted}.")
        if len(calls) > voted:
            findings.append(Finding("warning", "motions", f"The transcript has {len(calls)} vote calls but the "
                                    f"minutes record {voted} votes. Look for a missed motion at: {stamps}."))
        elif len(calls) < voted:
            notes.append("Fewer vote calls than votes: some votes may have been taken without the usual "
                         "words (for example 'any objection?'). Check them.")

    # Sources -------------------------------------------------------------------
    timed = [t.end or t.start for t in turns if t.start is not None]
    length = max(timed) if timed else None
    if length:
        for path, text in iter_strings(m):
            if path.endswith(".source"):
                seconds = source_seconds(text)
                if seconds is not None and seconds > length + 5:
                    findings.append(Finding("warning", path, f"Recording time {text} is after the end of the "
                                            f"transcript ({format_offset(length)})."))

    # Residents named in the minutes -------------------------------------------
    known = _all_attendee_names(m)
    minutes_text = " ".join(text for path, text in iter_strings(m) if not path.startswith("$.questions"))
    for speaker in sorted(speakers):
        key = normalize_name(speaker)
        if not key or key in known or re.fullmatch(r"(speaker|participant|guest|unknown)( \w+)?", key):
            continue
        if any(k.split()[-1] == key.split()[-1] for k in known if k):
            continue
        tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z'’-]+", speaker) if len(t) >= 4]
        hits = [t for t in tokens if re.search(rf"\b{re.escape(t)}\b", minutes_text)]
        if hits:
            findings.append(Finding("warning", "privacy", f"Speaker {speaker!r} (not on the attendance lists) "
                                    f"seems to be named in the minutes ({', '.join(hits)}). Most associations "
                                    "leave residents unnamed unless they ask otherwise."))
    return findings, notes


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def questions_markdown(m: dict) -> str:
    locale = locale_of(m)
    meeting = m["meeting"]
    lines = ["# Questions for the secretary", "",
             f"{m['organization']['name']} · {meeting['title']} · {format_date(meeting['date'], locale)}",
             ""]
    questions = m.get("questions") or []
    if not questions:
        lines.append("No open questions.")
        return "\n".join(lines) + "\n"
    lines += ["Please answer these so I can finish the minutes. Items marked [UNCLEAR] are highlighted in "
              "yellow in the draft.", ""]
    for index, question in enumerate(questions, start=1):
        lead = f"**{question['where']}:** " if question.get("where") else ""
        tail = f" (recording at {question['source']})" if question.get("source") else ""
        lines.append(f"{index}. {lead}{question['question']}{tail}")
    return "\n".join(lines) + "\n"


def summary_line(m: dict) -> str:
    motions = [motion for _, _, motion in iter_motions(m)]
    carried = sum(1 for mo in motions if mo.get("result") == "carried")
    failed = sum(1 for mo in motions if mo.get("result") == "failed")
    other = len(motions) - carried - failed
    return (f"{len(motions)} motions ({carried} carried, {failed} failed, {other} other) · "
            f"{len(m.get('action_items') or [])} action items · {len(m.get('questions') or [])} questions "
            f"· {len(find_unclear(m))} [UNCLEAR] markers")


def scan_transcript(path: str) -> int:
    try:
        turns, info = load_turns(path, keep_fillers=True)
    except TranscriptError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Key moments in {info.source}. Check each one against the minutes.\n")
    for turn in turns:
        tags, snippet = [], None
        for tag, pattern in SCAN_PATTERNS:
            match = pattern.search(turn.text)
            if match:
                tags.append(tag)
                if snippet is None:
                    begin = max(0, match.start() - 60)
                    snippet = ("…" if begin else "") + turn.text[begin:begin + 170].strip()
                    if begin + 170 < len(turn.text):
                        snippet += "…"
        if tags:
            stamp = format_offset(turn.start) if turn.start is not None else "--:--:--"
            print(f"[{stamp}] {'+'.join(tags):<14} {turn.speaker or 'Unknown speaker'}: {snippet}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a minutes JSON file and list questions for the secretary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:" + __doc__.split("Examples:", 1)[1],
    )
    parser.add_argument("json", nargs="?", help="minutes JSON file")
    parser.add_argument("--transcript", help="transcript to compare against (cleaned .txt or the original file)")
    parser.add_argument("--questions-out", metavar="FILE", help="write the questions for the secretary to this file (Markdown)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors (exit code 1)")
    parser.add_argument("--scan", metavar="TRANSCRIPT", help="only list motions, votes, tasks and other key moments in a transcript")
    args = parser.parse_args(argv)

    if args.scan:
        return scan_transcript(args.scan)
    if not args.json:
        parser.error("give a minutes JSON file (or use --scan TRANSCRIPT)")

    try:
        minutes = load_minutes(args.json)
    except MinutesError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    findings = check_minutes(minutes)
    notes: list[str] = []
    print(f"Checking {Path(args.json).name}")
    if args.transcript and not any(f.where == "format" for f in findings):
        try:
            turns, info = load_turns(args.transcript)
        except TranscriptError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Against transcript {info.source} ({len(turns)} speaker turns)")
        extra, notes = check_against_transcript(minutes, turns)
        findings += extra

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    print()
    print("ERRORS (fix before delivery):" if errors else "ERRORS: none")
    for index, finding in enumerate(errors, start=1):
        print(f"  E{index}. [{finding.where}] {finding.message}")
    print("WARNINGS (review each one):" if warnings else "WARNINGS: none")
    for index, finding in enumerate(warnings, start=1):
        print(f"  W{index}. [{finding.where}] {finding.message}")
    if any(f.where == "format" for f in findings):
        print("\nFix the format errors first; the other checks run after that.")
        return 1
    print()
    print("Summary: " + summary_line(minutes))
    for note in notes:
        print(note)
    questions = minutes.get("questions") or []
    if questions:
        print("\nQuestions for the secretary:")
        for index, question in enumerate(questions, start=1):
            lead = f"{question['where']}: " if question.get("where") else ""
            print(f"  {index}. {lead}{question['question']}")
    if args.questions_out:
        Path(args.questions_out).write_text(questions_markdown(minutes), encoding="utf-8")
        print(f"\nWrote {args.questions_out}")
    failed = bool(errors) or (args.strict and bool(warnings))
    print(f"\nResult: {'FAIL' if failed else 'PASS'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
