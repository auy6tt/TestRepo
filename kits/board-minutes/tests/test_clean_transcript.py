"""Tests for clean_transcript.py."""

import json

import pytest

import clean_transcript as ct
from conftest import SAMPLE_CLEAN, SAMPLE_SPEAKERS, SAMPLE_VTT


def turns_of(tmp_path, name, content, **kwargs):
    path = tmp_path / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    turns, info = ct.load_turns(path, **kwargs)
    return turns, info


ZOOM_VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.000
Diane Okafor: Um, okay, it's 7:02. Let's start.

2
00:00:04.500 --> 00:00:06.000
Diane Okafor: Is there a motion?

3
00:00:06.200 --> 00:00:07.000
Marcus Bell: So moved.

4
00:00:07.100 --> 00:00:07.900
Raymond Castillo: Second.

5
00:00:07.150 --> 00:00:07.800
Grace Lindqvist: Second.

6
00:00:08.000 --> 00:00:09.000
Helen's iPhone: Uh-huh, I agree. Note: it's 7:03.
"""


def test_zoom_vtt_merges_same_speaker_and_keeps_crosstalk(tmp_path):
    turns, info = turns_of(tmp_path, "zoom.vtt", ZOOM_VTT)
    assert info.format == "WebVTT"
    assert [t.speaker for t in turns] == ["Diane Okafor", "Marcus Bell", "Raymond Castillo",
                                          "Grace Lindqvist", "Helen's iPhone"]
    assert turns[0].text == "Okay, it's 7:02. Let's start. Is there a motion?"
    assert turns[0].start == pytest.approx(1.0)
    # "Note:" inside the text is not mistaken for a speaker, and "Uh-huh" is kept.
    assert turns[-1].text == "Uh-huh, I agree. Note: it's 7:03."


def test_teams_voice_tags_cue_ids_notes_and_entities(tmp_path):
    vtt = ("WEBVTT\n\nNOTE exported by Teams\n\n0f3c-12/1-0\n00:00:00.000 --> 00:00:03.000\n"
           "<v Diane Okafor>Good evening everyone.</v>\n\n0f3c-12/2-0\n00:00:03.000 --> 00:00:05.000\n"
           "<v Diane Okafor>Uh, we have a quorum.</v>\n\n0f3c-12/3-0\n00:00:05.000 --> 00:00:06.000\n"
           "<v Marcus Bell>Thanks &amp; welcome.</v>\n")
    turns, _ = turns_of(tmp_path, "teams.vtt", vtt)
    assert [(t.speaker, t.text) for t in turns] == [
        ("Diane Okafor", "Good evening everyone. We have a quorum."),
        ("Marcus Bell", "Thanks & welcome."),
    ]


def test_srt_with_dialogue_dashes_tags_and_windows_line_endings(tmp_path):
    srt = ("1\r\n00:00:01,000 --> 00:00:03,000\r\n- Diane Okafor: Hello.\r\n- Marcus Bell: Hi.\r\n\r\n"
           "2\r\n00:00:03,500 --> 00:00:05,000\r\n<i>No speaker here.</i>\r\n")
    turns, info = turns_of(tmp_path, "meeting.srt", srt)
    assert info.format == "SRT"
    assert [(t.speaker, t.text) for t in turns] == [
        ("Diane Okafor", "Hello."), ("Marcus Bell", "Hi."), (None, "No speaker here.")]


def test_srt_without_blank_lines_between_cues(tmp_path):
    srt = "1\n00:00:01,000 --> 00:00:02,000\nAnn Lee: One.\n2\n00:00:20,000 --> 00:00:21,000\nAnn Lee: Two.\n"
    turns, _ = turns_of(tmp_path, "tight.srt", srt)
    assert [t.text for t in turns] == ["One.", "Two."]  # 18 s pause: separate paragraphs, no stray "2"


def test_otter_txt_headers_and_title_lines(tmp_path):
    otter = ("Board meeting transcript\nSeptember 16, 2026\n\nDiane Okafor  0:03\nUm, okay, let's get started.\n\n"
             "Speaker 2  0:15\nI move we approve the minutes.\nAnd the agenda.\n\nDiane Okafor  1:02:03\nThanks.\n")
    turns, info = turns_of(tmp_path, "otter.txt", otter)
    assert info.skipped_preamble == "Board meeting transcript September 16, 2026"
    assert [(t.speaker, t.start) for t in turns] == [("Diane Okafor", 3), ("Speaker 2", 15), ("Diane Okafor", 3723)]
    assert turns[1].text == "I move we approve the minutes. And the agenda."


def test_rev_and_zoom_saved_and_inline_text_formats(tmp_path):
    rev, _ = turns_of(tmp_path, "rev.txt", "Speaker 1 (00:00:03):\nHello there.\n\nSpeaker 2 (00:00:09):\nHi.\n")
    assert [(t.speaker, t.start, t.text) for t in rev] == [("Speaker 1", 3, "Hello there."), ("Speaker 2", 9, "Hi.")]
    saved, _ = turns_of(tmp_path, "saved.txt", "[Diane Okafor] 19:02:15\nGood evening.\n[Marcus Bell] 19:02:20\nHi all.\n")
    assert [(t.speaker, t.start) for t in saved] == [("Diane Okafor", 68535), ("Marcus Bell", 68540)]
    inline, _ = turns_of(tmp_path, "inline.txt",
                         "[00:00:03] Diane Okafor: Hello.\n(00:00:05) Marcus Bell: Hi.\nTotal: 5 items\n")
    assert [(t.speaker, t.text) for t in inline] == [("Diane Okafor", "Hello."), ("Marcus Bell", "Hi. Total: 5 items")]


def test_youtube_style_rolling_captions_are_not_repeated(tmp_path):
    vtt = ("WEBVTT\nKind: captions\n\n00:00:00.000 --> 00:00:02.000 align:start position:0%\n"
           "good<00:00:00.500><c> evening</c>\n\n00:00:02.000 --> 00:00:02.010\ngood evening\n\n"
           "00:00:02.010 --> 00:00:04.000\ngood evening\nwelcome<00:00:02.500><c> everyone</c>\n")
    turns, _ = turns_of(tmp_path, "yt.vtt", vtt)
    assert len(turns) == 1
    assert turns[0].text == "good evening welcome everyone"


def test_docx_transcript(tmp_path):
    from docx import Document
    doc = Document()
    for line in ["Transcript", "September 16, 2026, 7:00PM", "", "Diane Okafor   0:03", "Okay, let's start.",
                 "Marcus Bell   0:09", "I move we approve the agenda.", "Raymond Castillo   0:12", "Second."]:
        doc.add_paragraph(line)
    path = tmp_path / "teams.docx"
    doc.save(str(path))
    turns, info = ct.load_turns(path)
    assert info.format == "DOCX"
    assert [(t.speaker, t.start, t.text) for t in turns] == [
        ("Diane Okafor", 3, "Okay, let's start."), ("Marcus Bell", 9, "I move we approve the agenda."),
        ("Raymond Castillo", 12, "Second.")]


@pytest.mark.parametrize("raw, expected", [
    ("Um, I think so.", "I think so."),
    ("So uh we should vote.", "So we should vote."),
    ("Okay. Um, so we start.", "Okay. So we start."),
    ("Uh-huh, and mm-hmm.", "Uh-huh, and mm-hmm."),
    ("The umbrella and the error.", "The umbrella and the error."),
    ("Hmm. Okay.", "Okay."),
    ("I think, uh, it's fine.", "I think, it's fine."),
])
def test_remove_fillers(raw, expected):
    assert ct.remove_fillers(raw)[0] == expected


def test_keep_fillers_option(tmp_path):
    turns, _ = turns_of(tmp_path, "zoom.vtt", ZOOM_VTT, keep_fillers=True)
    assert turns[0].text.startswith("Um, okay")


def test_speaker_map_from_pairs_and_file(tmp_path):
    map_file = tmp_path / "speakers.txt"
    map_file.write_text("# comment\nHelen's iPhone = Helen Whitaker\nspeaker 2 -> Marcus Bell\n", encoding="utf-8")
    mapping = ct.parse_speaker_map(["Raymond Castillo=Ray Castillo"], [str(map_file)])
    assert mapping == {"raymond castillo": "Ray Castillo", "helen's iphone": "Helen Whitaker",
                       "speaker 2": "Marcus Bell"}
    turns, _ = turns_of(tmp_path, "zoom.vtt", ZOOM_VTT, speaker_map=mapping)
    assert "Helen Whitaker" in [t.speaker for t in turns]
    with pytest.raises(ct.TranscriptError):
        ct.parse_speaker_map(["no equals sign"], None)


def test_long_monologue_is_split_into_paragraphs(tmp_path):
    cues = [f"{i}\n00:{i:02d}:00.000 --> 00:{i:02d}:59.000\nGrace Lindqvist: Part {i}.\n" for i in range(1, 5)]
    turns, _ = turns_of(tmp_path, "long.vtt", "WEBVTT\n\n" + "\n".join(cues), merge_gap=8, split_after=90)
    assert [t.text for t in turns] == ["Part 1.", "Part 2.", "Part 3.", "Part 4."]  # 1 s gaps, but >90 s each


def test_looks_like_speaker():
    for good in ["Diane Okafor", "Speaker 2", "Helen's iPhone", "J. Moreno", "Mary de la Cruz", "Lot 112 - Sato"]:
        assert ct.looks_like_speaker(good), good
    for bad in ["Note", "Motion", "So the thing is", "It's 7", "Okay.", "the treasurer", ""]:
        assert not ct.looks_like_speaker(bad), bad


def test_cli_text_output_with_clock_and_report(tmp_path, capsys):
    source = tmp_path / "zoom.vtt"
    source.write_text(ZOOM_VTT, encoding="utf-8")
    out = tmp_path / "clean.txt"
    code = ct.main([str(source), "-o", str(out), "--clock-start", "19:00:30"])
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# CLEAN TRANSCRIPT")
    assert "[00:00:01 | 19:00:31] Diane Okafor: Okay, it's 7:02." in text
    report = capsys.readouterr().err
    assert "Helen's iPhone" in report and "Check these speaker labels" in report


def test_cli_json_output(tmp_path):
    source = tmp_path / "zoom.vtt"
    source.write_text(ZOOM_VTT, encoding="utf-8")
    out = tmp_path / "turns.json"
    assert ct.main([str(source), "--format", "json", "-o", str(out), "-q"]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["format"] == "WebVTT"
    assert data["turns"][0] == {"speaker": "Diane Okafor", "text": "Okay, it's 7:02. Let's start. Is there a motion?",
                                "start": "00:00:01", "start_seconds": 1.0, "end_seconds": 6.0}
    assert data["speakers"]["Diane Okafor"]["words"] == 9


def test_cli_errors(tmp_path, capsys):
    assert ct.main([str(tmp_path / "missing.vtt")]) == 1
    source = tmp_path / "zoom.vtt"
    source.write_text(ZOOM_VTT, encoding="utf-8")
    assert ct.main([str(source), "--clock-start", "25:99"]) == 1
    assert ct.main([str(source), "-o", str(source)]) == 1
    empty = tmp_path / "empty.txt"
    empty.write_text("\n\n", encoding="utf-8")
    assert ct.main([str(empty)]) == 1
    assert "Error" in capsys.readouterr().err


def test_recleaning_clean_output_changes_nothing(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    assert ct.main([str(SAMPLE_VTT), "-o", str(first), "--speaker-map-file", str(SAMPLE_SPEAKERS), "-q"]) == 0
    assert ct.main([str(first), "-o", str(second), "-q"]) == 0
    body = lambda p: p.read_text(encoding="utf-8").split("# " + "-" * 66, 1)[1]  # noqa: E731
    assert body(first) == body(second)


def test_committed_sample_matches_fresh_output(tmp_path):
    fresh = tmp_path / "fresh.txt"
    assert ct.main([str(SAMPLE_VTT), "-o", str(fresh), "--speaker-map-file", str(SAMPLE_SPEAKERS), "-q"]) == 0
    assert fresh.read_text(encoding="utf-8") == SAMPLE_CLEAN.read_text(encoding="utf-8")


def test_sample_transcript_length_and_speakers():
    turns, info = ct.load_turns(SAMPLE_VTT)
    length = max(t.end for t in turns)
    assert 25 * 60 <= length <= 40 * 60
    assert {"Diane Okafor", "Raymond Castillo", "Grace Lindqvist", "Marcus Bell", "Helen's iPhone",
            "Priya Raman"} <= {t.speaker for t in turns}
