"""Tests for check_minutes.py and the shared helpers in minutes_common.py."""

import datetime as dt

import pytest

import check_minutes as cm
import minutes_common as mc
from clean_transcript import load_turns
from conftest import SAMPLE_CLEAN, SAMPLE_JSON, SAMPLE_VTT

TODAY = dt.date(2026, 10, 7)


def messages(findings, level=None):
    return [f.message for f in findings if level is None or f.level == level]


def test_sample_passes(sample):
    findings = cm.check_minutes(sample, today=TODAY)
    assert messages(findings, "error") == []
    warnings = messages(findings, "warning")
    assert len(warnings) == 2 and all("[UNCLEAR]" in w for w in warnings)


@pytest.mark.parametrize("transcript", [SAMPLE_CLEAN, SAMPLE_VTT])
def test_sample_against_transcript(sample, transcript):
    turns, _ = load_turns(transcript)
    findings, notes = cm.check_against_transcript(sample, turns)
    assert findings == []
    assert notes[0].startswith("Votes called in the transcript: 8") and notes[0].endswith("Votes in the minutes: 8.")


def test_cli_on_sample(tmp_path, capsys):
    questions = tmp_path / "questions.md"
    code = cm.main([str(SAMPLE_JSON), "--transcript", str(SAMPLE_CLEAN), "--questions-out", str(questions)])
    out = capsys.readouterr().out
    assert code == 0 and "Result: PASS (0 errors, 2 warnings)" in out
    text = questions.read_text(encoding="utf-8")
    assert text.startswith("# Questions for the secretary")
    assert "1. **Item 6, Motion 2:** Who seconded the motion" in text and "(recording at 00:12:51)" in text
    assert cm.main([str(SAMPLE_JSON), "--strict"]) == 1  # warnings count as failures with --strict


def item(sample, number):
    return next(i for i in sample["items"] if i.get("number") == number)


def first_motion(sample, number):
    return [m for _, _, m in mc.iter_motions(sample)][number - 1]


@pytest.mark.parametrize("change, expected", [
    (lambda s: first_motion(s, 3)["vote"].update(in_favor=6), "Vote total 6 is more than the 5 directors present"),
    (lambda s: first_motion(s, 3)["vote"].update(in_favor=2, opposed=3), "is not a majority"),
    (lambda s: first_motion(s, 3).update(result="failed"), "Recorded as failed, but 5 for and 0 against"),
    (lambda s: first_motion(s, 1).update(seconded_by="Marcus Bell"), "recorded as both mover and seconder"),
    (lambda s: first_motion(s, 4)["vote"].update(opposed=0), "opposed is 0 but the roll call has 1 'no' votes"),
    (lambda s: first_motion(s, 7)["vote"].update(opposed=1), "Marked unanimous but someone voted against"),
    (lambda s: s.update(questions=[]), "[UNCLEAR] marker(s) but no questions"),
    (lambda s: item(s, "3")["summary"].append("TODO check this"), "Leftover placeholder text"),
    (lambda s: s["meeting"].update(adjourned="18:30"), "is not after the call to order"),
    (lambda s: s["attendance"]["quorum"].update(present_count=2), "fewer than the 3 required"),
    (lambda s: s["attendance"]["directors_absent"].append({"name": "Marcus Bell"}), "both present and absent"),
    (lambda s: s["document"].update(status="approved", approved_on="2026-10-21"), "cannot contain [UNCLEAR]"),
    (lambda s: s["action_items"][0].update(due="2026-02-30"), "is not a real date"),
])
def test_errors(sample, change, expected):
    change(sample)
    errors = messages(cm.check_minutes(sample, today=TODAY), "error")
    assert any(expected in e for e in errors), errors


@pytest.mark.parametrize("change, expected", [
    (lambda s: first_motion(s, 1).update(moved_by="Kevin Tran"), "Mover 'Kevin Tran' is not a director"),
    (lambda s: first_motion(s, 3).update(seconded_by=None), "No seconder recorded"),
    (lambda s: first_motion(s, 3).update(moved_by=None), "No mover recorded"),
    (lambda s: first_motion(s, 4)["vote"].pop("roll_call"), "Roll call vote without the list"),
    (lambda s: first_motion(s, 8).pop("vote"), "no vote is recorded"),
    (lambda s: s["action_items"][0].update(owner="Pria Raman"), "is not in the attendance lists"),
    (lambda s: s["action_items"][0].update(due="2026-09-01"), "is before the meeting"),
    (lambda s: s["items"].remove(item(s, "5")), "No 'approval_of_minutes' item"),
    (lambda s: s["items"].pop(), "No 'adjournment' item"),
    (lambda s: item(s, "10").update(summary=["word " * 45]), "Record only what the bylaws allow"),
    (lambda s: item(s, "1")["summary"].__setitem__(0, "The meeting started."), "does not mention 7:02 p.m."),
    (lambda s: s["next_meeting"].update(date="2026-09-01"), "is not after this meeting"),
    (lambda s: item(s, "3")["summary"].__setitem__(0, "Approved [inaudible]"), "use [UNCLEAR]"),
    (lambda s: s["attendance"]["quorum"].update(met=None), "Whether a quorum was present is unclear"),
    (lambda s: s["meeting"].update(date="2027-01-01"), "is in the future"),
])
def test_warnings(sample, change, expected):
    change(sample)
    warnings = messages(cm.check_minutes(sample, today=TODAY), "warning")
    assert any(expected in w for w in warnings), warnings


def test_transcript_checks_find_problems(sample):
    turns, _ = load_turns(SAMPLE_CLEAN)
    item(sample, "7")["summary"].append("A resident, Julia Moreno, thanked the Board.")
    item(sample, "6")["summary"].append("- Legal fees were $9,999.")
    sample["attendance"]["others_present"].append({"name": "Pat Quinlan", "role": "Attorney"})
    item(sample, "8a")["motions"] = []  # as if the postponement motion had been missed
    findings, notes = cm.check_against_transcript(sample, turns)
    text = " ".join(messages(findings))
    assert "'Pat Quinlan' does not appear in the transcript" in text
    assert "$9,999 is not in the transcript" in text
    assert "8 vote calls but the minutes record 7 votes" in text
    assert "Speaker 'J Moreno'" in text and "Moreno" in text


def test_scan_mode(capsys):
    assert cm.main(["--scan", str(SAMPLE_CLEAN)]) == 0
    out = capsys.readouterr().out
    assert "[00:09:27] MOTION" in out
    assert "SECOND         Grace Lindqvist: Second." in out
    assert "CLOSED" in out and "executive session" in out
    assert "I'll add it to the list for the budget workshop" in out
    assert "I'm finally here" in out


def test_format_errors_are_reported_first(tmp_path, sample, write_json, capsys):
    sample["items"][0]["kind"] = "opening"
    path = write_json(sample)
    assert cm.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "$.items[0].kind" in out and "Fix the format errors first" in out


# ---------------------------------------------------------------- helpers

def test_dates_and_times():
    assert mc.format_date("2026-09-16") == "Wednesday, September 16, 2026"
    assert mc.format_date("2026-09-16", "en-GB") == "Wednesday 16 September 2026"
    assert mc.format_date("2026-09-16", weekday=False) == "September 16, 2026"
    assert mc.format_date("[UNCLEAR]") == "[UNCLEAR]"
    assert mc.format_time("19:02") == "7:02 p.m."
    assert mc.format_time("00:05") == "12:05 a.m."
    assert mc.format_time("12:00", "en-GB") == "12.00pm"
    assert mc.source_seconds("00:12:40-00:13:00") == 760
    assert mc.parse_date("2026-02-30") is None


def test_vote_text():
    assert mc.vote_counts_text({"method": "voice", "in_favor": 4, "opposed": 0}) == "4 in favor, 0 opposed (voice vote)"
    assert mc.vote_counts_text({"method": "voice", "in_favor": 5, "opposed": 0, "unanimous": True}) == \
        "5 in favor, 0 opposed (unanimous, voice vote)"
    assert mc.vote_counts_text({"method": "voice", "unanimous": True}) == "Unanimous (voice vote)"
    assert mc.vote_counts_text({"method": "roll_call"}) == "Roll call vote"
    assert mc.vote_counts_text({"method": "unanimous_consent"}) == "By unanimous consent"
    assert mc.vote_counts_text({"in_favor": 3, "opposed": 1}, "en-GB") == "3 in favour, 1 opposed"


def test_text_helpers(sample):
    assert mc.smart_quotes('The Board\'s "plan" isn\'t final') == "The Board’s “plan” isn’t final"
    assert mc.normalize_name("Director Marcus Bell") == "marcus bell"
    assert mc.item_heading({"number": "8a", "title": "Pool"}) == "8a. Pool"
    assert mc.item_heading({"number": "IV.", "title": "Reports"}) == "IV. Reports"
    assert mc.quorum_text(sample) == "A quorum was present at the call to order: 4 of 5 directors (3 required)."
    sample["attendance"]["quorum"].pop("statement")
    assert mc.quorum_text(sample) == "A quorum was present (4 of 5 directors present; 3 required)."
    assert len(mc.find_unclear(sample)) == 3
    assert mc.next_meeting_text(sample) == ("The next regular meeting of the Board will be held on Wednesday, "
                                            "October 21, 2026, at 7:00 p.m., by Zoom videoconference. The "
                                            "Community Manager will send the link with the meeting packet.")
