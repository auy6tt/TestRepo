---
name: board-minutes
description: Drafts formal board meeting minutes for HOA, condo, nonprofit, church and membership boards from a Zoom, Teams or Otter transcript (VTT, SRT, TXT or DOCX) and the agenda. Cleans the transcript, writes the minutes JSON without inventing anything (unclear points marked [UNCLEAR]), builds the Word minutes and Excel motions table, runs the quality checks and lists questions for the secretary. Use when someone asks for meeting minutes or board minutes, or wants a meeting transcript or recording turned into minutes.
argument-hint: "[job folder or transcript file]"
---

# Board minutes

Turn a meeting transcript into draft minutes with the kit in `${CLAUDE_PROJECT_DIR}/kits/board-minutes` (read its README.md if you need background). The user's job: $ARGUMENTS

## Ground rules (never break these)

1. **Never invent.** Every name, motion, mover, seconder, vote count, amount, date and time must come from the transcript, the agenda or the user. If something is unclear or two sources disagree, write `[UNCLEAR]` or `[UNCLEAR: option A or option B]` and add a question to `questions`.
2. **Spellings and titles come from the board list or agenda**, never from speech-to-text ("Renfield" in a transcript is "Wrenfield" if the agenda says so).
3. **Executive (closed) session:** record only the start and end times, the general topic and anything announced afterwards in open session. If the recording caught closed-session discussion, leave all of it out and add a question telling the secretary.
4. **Residents** who speak in the open forum are not named, unless the user says the client wants names.
5. **Record decisions, not conversation:** neutral, third person, past tense, no quotes, no opinions or loaded words.
6. **Confidential files** stay in the job folder (`kits/board-minutes/work/...` is ignored by git). Don't copy client content anywhere else, and never commit it.
7. **Consent:** if the transcript has no announcement that the meeting was recorded, tell the user to confirm consent with the client.
8. **The board approves the minutes.** Output is a draft unless the user says the board has approved it.

## Step 0: Setup (once per session)

```bash
bash ${CLAUDE_PROJECT_DIR}/kits/board-minutes/scripts/setup.sh
```

Run the kit's scripts with `~/.venvs/board-minutes/bin/python`, as below.

## Step 1: Job folder and inputs

- Use the job folder in the user's request, with the client's files in `<job>/input/` and everything you make in `<job>/output/`. If the user gave loose files, create `${CLAUDE_PROJECT_DIR}/kits/board-minutes/work/<client-name>/<YYYY-MM-DD>/input/` and copy them there.
- You need: the transcript file, the agenda, and the board list with titles (often on the agenda). Useful: the quorum rule, the client's .docx template, past minutes for style, the secretary's notes, and whether to name residents.
- If the agenda or board list is missing, ask the user before writing the JSON (you can clean the transcript first).
- If there is only audio or video, ask for the transcript file the meeting software produced. This kit does not transcribe audio.

## Step 2: Clean the transcript

```bash
~/.venvs/board-minutes/bin/python ${CLAUDE_PROJECT_DIR}/kits/board-minutes/scripts/clean_transcript.py <job>/input/<transcript> -o <job>/output/transcript-clean.txt
```

Read the speaker summary it prints. For flagged labels (device names, "Speaker 2", first names only), rename a label only when the transcript or the user makes the identity clear: write `<job>/input/speaker-map.txt` with lines `OLD = NEW` and a `#` comment saying how you know, then run again with `--speaker-map-file <job>/input/speaker-map.txt`. Otherwise keep the label and add a question. Don't use `--clock-start` if the recording was paused.

## Step 3: Map the meeting, then read everything

```bash
~/.venvs/board-minutes/bin/python ${CLAUDE_PROJECT_DIR}/kits/board-minutes/scripts/check_minutes.py --scan <job>/output/transcript-clean.txt
```

This lists motions, seconds, votes, results, tasks, closed session and arrivals with their times. Then read the **whole** clean transcript (use offset/limit for long files; don't skip any part) and the agenda. Note for each agenda item what was decided, by whom, and the recording time.

## Step 4: Write the minutes JSON

Write `<job>/output/minutes.json` in the format in `${CLAUDE_PROJECT_DIR}/kits/board-minutes/SCHEMA.md`. Model it on `${CLAUDE_PROJECT_DIR}/kits/board-minutes/samples/wrenfield-commons-2026-09-16-minutes.json`, whose `_note` fields show the judgment calls. Follow [extraction-rules.md](extraction-rules.md) for each section. The most important rules:

- Items follow the agenda's numbering and the order things happened. Use `kind` for call to order, roll call, approval of minutes, open forum, reports, business, executive session, next meeting and adjournment.
- Times are the ones the chair announced, in 24-hour `HH:MM`.
- Motion `text` is the wording voted on, starting with "To". Vote counts only when stated or countable (a roll call). "Carries unanimously" with no count means `"unanimous": true` and no numbers.
- Every action item has an owner and a due date. Turn relative dates into dates only when certain ("by Friday" after a Wednesday meeting); otherwise use words or `[UNCLEAR]`.
- Every `[UNCLEAR]` gets a specific question with the recording time.
- Add `"source"` times so the user can check each motion and task.

## Step 5: Build

```bash
~/.venvs/board-minutes/bin/python ${CLAUDE_PROJECT_DIR}/kits/board-minutes/scripts/build_minutes.py <job>/output/minutes.json --pdf
```

Add `--template <job>/input/<client-template>.docx` if the client has a template with placeholders (see the kit README). If the build lists format errors, fix the JSON and run it again.

## Step 6: Check and fix

```bash
~/.venvs/board-minutes/bin/python ${CLAUDE_PROJECT_DIR}/kits/board-minutes/scripts/check_minutes.py <job>/output/minutes.json --transcript <job>/output/transcript-clean.txt --questions-out <job>/output/questions.md
```

Fix every error. For each warning, either fix it or make sure your report to the user explains it. If the transcript has more vote calls than the minutes have votes, go back to those times and look for a missed motion. Rebuild after every change to the JSON.

## Step 7: Look at the output

Render the PDF and look at every page:

```bash
pdftoppm -png -r 60 <job>/output/<name>-minutes.pdf <job>/output/page
```

Check headings, motion boxes and tables, that no `{{placeholder}}` is left, and that the yellow [UNCLEAR] highlights are where you expect. Delete the page images when you're done.

## Step 8: Report to the user

Reply with:
1. The files made (paths): minutes .docx and .pdf, motions .xlsx, questions.md, the JSON and the clean transcript.
2. One line of totals: motions (carried or failed), action items, [UNCLEAR] markers.
3. The check result, and the remaining warnings with a one-line reason for each.
4. The questions for the secretary, numbered.
5. The judgment calls the user should verify: speaker renames, spelling fixes from the agenda, relative dates you converted, anything left out of executive session, consent.
6. A reminder that the user reviews the draft before sending it, using the email in `kits/board-minutes/templates/client-handoff-email.md`.

## When the secretary answers

Replace each `[UNCLEAR]` with the confirmed value, remove the answered questions, rebuild and check again. When the board has approved the minutes, set `"status": "approved"` and `"approved_on"` in `document`, apply any changes made at the approval meeting, and rebuild.
