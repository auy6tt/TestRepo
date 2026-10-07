# Board minutes starter kit

Everything you need to sell and deliver formal meeting minutes for HOA, condo, nonprofit, church and membership boards: scripts that turn a meeting transcript into finished Word minutes and an Excel motions table, a Claude Code skill that runs the whole process, client templates, and a fictional sample to show prospects.

**Contents:** [The offer](#the-offer) · [Who buys](#who-buys-and-where-to-find-them) · [Prices](#price-guide) · [What's in the kit](#whats-in-the-kit) · [Setup](#setup) · [Delivery process](#step-by-step-delivery-process) · [Quality checklist](#quality-checklist) · [Risks and rules](#risks-and-rules) · [The scripts](#how-to-run-each-script) · [Client templates](#using-a-clients-own-template) · [The skill](#how-to-use-the-skill) · [The sample](#the-portfolio-sample) · [Tests](#running-the-tests)

## The offer

You turn a board's Zoom, Teams or Otter transcript and agenda into formal draft minutes within 24 to 72 hours: header, attendance and quorum, approval of prior minutes, every motion with mover, seconder and vote result, short discussion summaries, action items with owners and due dates, next meeting and adjournment. You deliver them in the client's own Word template (or a clean professional layout), with a spreadsheet of motions and action items and a short list of questions for the secretary on anything the recording didn't make clear. You never guess: unclear points are marked [UNCLEAR] and asked about. The board then approves the minutes as usual.

## Who buys and where to find them

**Who pays**
- HOA and condo management companies. Their community managers often look after several associations each and are often the ones who take or arrange the minutes.
- Self-managed HOA and condo boards, usually the secretary.
- Nonprofit boards, church councils and vestries, clubs and membership associations, school foundations, and the committees of all of these.

**Where to find them**
- **HOA management companies near you.** Search "[your city] HOA management company" and "community association management". Email the office manager or a community manager.
- **Community Associations Institute (CAI):** local chapters list member management companies and hold events.
- **Nonprofit and church networks:** local nonprofit associations, volunteer centers, diocese or denomination offices, and board chairs on LinkedIn.
- **Freelance platforms:** search Upwork and Fiverr for "meeting minutes", "board minutes" and "minute taker". Small jobs build your first reviews.
- **People you know:** anyone who sits on a board or lives in an HOA. Ask who takes their minutes and how long it takes them.

**A first message to a management company (copy and edit)**

```text
Subject: Board minutes from your Zoom recordings, back in 48 hours

Hi [Name],

I write formal board meeting minutes for community associations. You send the
Zoom or Teams transcript and the agenda; within 48 hours you get draft minutes
in your template (motions, movers, seconders, votes, action items), plus a short
list of anything unclear for the secretary to confirm.

Here's a sample from a fictional HOA meeting: [link or attachment]

I'd be glad to do your next meeting free so you can judge the quality.

[Your name]
```

The playbook's one-day test: send this to 25 management companies, offer one free set with 24-hour turnaround, and count the replies.

## Price guide

| Package | Price (USD) | Notes |
|---|---|---|
| One meeting up to 1 hour, 72-hour turnaround | $75–100 | Your layout or theirs, one round of corrections |
| One meeting of 1–2 hours, or 48-hour turnaround | $100–150 | |
| 24-hour rush, meetings over 2 hours, or complex meetings | $150–200 | Elections, annual meetings, many motions |
| Monthly, one association | $100–300 a month | One regular meeting a month plus corrections; extra meetings priced separately |
| Management company with several associations | Monthly price per association, small discount from the third one | Ask for one contact and one template per association |

Plan on one to two hours of your own time per one-hour meeting at first: reading, checking and emailing. It gets faster once you know a board. For new clients, take payment for the first meeting upfront or use platform escrow.

## What's in the kit

```text
kits/board-minutes/
├── README.md                      this guide
├── SCHEMA.md                      the minutes JSON format, field by field
├── requirements.txt               Python packages
├── scripts/
│   ├── setup.sh                   creates a virtual environment and installs the packages
│   ├── clean_transcript.py        VTT/SRT/TXT/DOCX transcript -> clean speaker-labelled text
│   ├── build_minutes.py           minutes JSON -> Word minutes (.docx), Excel workbook (.xlsx), PDF
│   ├── check_minutes.py           checks the JSON (and the transcript); lists questions; --scan mode
│   ├── make_template.py           writes templates/minutes-template.docx
│   ├── minutes.schema.json        the JSON Schema the scripts check against
│   └── minutes_common.py, minutes_docx.py, minutes_xlsx.py   shared code (not run directly)
├── templates/
│   ├── minutes-template.docx      generic minutes template with {{placeholders}}
│   ├── minutes-skeleton.json      blank minutes JSON to start from
│   ├── intake-checklist.md        what to ask new clients and what to collect per meeting
│   └── client-handoff-email.md    draft, final and approved delivery emails
├── samples/                       fictional portfolio sample (see below)
├── tests/                         automated tests (pytest)
└── work/                          your client jobs go here; ignored by git, never committed
```

The skill that runs the process lives at [`.claude/skills/board-minutes/SKILL.md`](../../.claude/skills/board-minutes/SKILL.md).

## Setup

Once per session (the cloud container is temporary, so do it again in a new session):

```sh
bash kits/board-minutes/scripts/setup.sh
```

It creates a Python virtual environment in `~/.venvs/board-minutes` and installs python-docx, openpyxl, jsonschema and pytest. Then run the scripts with that Python:

```sh
PY=~/.venvs/board-minutes/bin/python
$PY kits/board-minutes/scripts/check_minutes.py --help
```

PDF output needs LibreOffice Writer. A fresh cloud session has only part of LibreOffice, so install Writer once per session with `sudo apt-get install -y --no-install-recommends libreoffice-writer`, or run `bash kits/setup.sh board-minutes`, which does both steps. Without Writer you still get the .docx and .xlsx.

## Step-by-step delivery process

1. **Intake.** Go through [`templates/intake-checklist.md`](templates/intake-checklist.md): agreement, price, board list, quorum rule, style choices, consent, deadline.
2. **Collect the files** in a job folder: `kits/board-minutes/work/<client>/<meeting date>/input/` for the transcript, agenda, board list and the client's template.
3. **Check consent and closed session.** Look for the recording announcement. Note where executive session starts and ends, and whether the recording kept running.
4. **Clean the transcript** with `clean_transcript.py`. Rename speaker labels like "Helen's iPhone" or "Speaker 2" only when it's clear who they are.
5. **Draft the minutes JSON.** Ask Claude to run the board-minutes skill. It reads the whole transcript and the agenda, writes `minutes.json`, marks anything uncertain as [UNCLEAR] and writes a question for each one.
6. **Build** the Word minutes, Excel workbook and PDF with `build_minutes.py`.
7. **Check** with `check_minutes.py --transcript`. Fix every error; read every warning.
8. **Review it yourself.** Read the PDF beside the transcript and go through the [quality checklist](#quality-checklist). If you have the recording, listen at every vote and every [UNCLEAR] point.
9. **Send the draft** with the email in [`templates/client-handoff-email.md`](templates/client-handoff-email.md). Paste in the questions file.
10. **Apply the answers.** Replace each [UNCLEAR] in the JSON, delete the answered questions, rebuild, run the checks again and send the final draft.
11. **After the board approves the minutes,** set `"status": "approved"` and `"approved_on"` in the JSON, add any changes made at the meeting, rebuild, and send the approved version. Delete the recording and transcript as agreed, and send your invoice.

## Quality checklist

Before every delivery:

- [ ] Names and titles match the client's board list, not the transcript's spelling.
- [ ] Header: association name, meeting type, date, scheduled time, location.
- [ ] Attendance: present, absent, others; late arrivals and early departures; the quorum statement.
- [ ] Prior minutes: approval recorded, with any corrections.
- [ ] Every motion has its exact wording, mover, seconder (or why there was none), vote and result.
- [ ] The number of votes in the minutes matches the votes called in the transcript (the checker counts them).
- [ ] Vote counts appear only where the chair stated them or you can count them, as in a roll call.
- [ ] Amounts, dates and vendor names match the transcript, the agenda and the board packet.
- [ ] Executive session shows only the time, the general topic and what was announced in open session.
- [ ] Residents who spoke in the open forum aren't named, unless the client wants names.
- [ ] Every action item has an owner and a due date, or [UNCLEAR] and a question.
- [ ] Next meeting and adjournment time are there.
- [ ] The tone is neutral: no quotes, opinions or loaded words ("heated", "excellent").
- [ ] Every [UNCLEAR] has a question, and `check_minutes.py` shows 0 errors.
- [ ] The DRAFT label and confidential footer are on drafts.
- [ ] The PDF looks right, and the files are this client's, for this meeting, in the latest version.

## Risks and rules

- **Never invent anything.** If the transcript doesn't say who seconded, what the vote was or what a figure is, write [UNCLEAR] and ask. A misreported vote costs you the client.
- **Recording consent.** Some US states and many countries require everyone's consent to record. Make sure the client announces recordings, and don't record meetings yourself.
- **Executive (closed) session.** Leave out what was said, even if the recording caught it. Record only what the bylaws and local law allow, usually the time, the general topic and any vote taken afterwards in open session. Tell the client if the recording ran into closed session.
- **Confidentiality.** Turn off model training in your Claude privacy settings before client work. Keep client files in `work/` (never committed) or in the client's own storage. Delete recordings and transcripts when your agreement says. Never use a client's real minutes in your portfolio without written permission.
- **Personal information.** Minutes often touch delinquencies, violations and disputes. Use the wording the board used in open session (an account number, not a name) and don't add detail.
- **You draft; the board approves.** You aren't the secretary and you don't give legal or parliamentary advice. Don't promise that minutes "comply" with a statute or the bylaws.
- **Say you use AI tools.** Tell clients you draft with AI tools and check everything yourself. If someone asks for no AI, don't use this kit for them.
- **Put it in writing.** Use a short agreement covering confidentiality, deletion, payment and a liability cap at the fee. Start from [`templates/simple-agreement.md`](../../templates/simple-agreement.md) in this repo.
- **Platform rules.** If a client found you on Upwork or Fiverr, keep the work and payment there.

## How to run each script

The examples use the sample files and run from the repo root, with `PY=~/.venvs/board-minutes/bin/python` set as in Setup. Every script has `--help`.

### 1. clean_transcript.py

Turns a transcript into one paragraph per speaker turn, with times:

```sh
$PY kits/board-minutes/scripts/clean_transcript.py \
    kits/board-minutes/samples/wrenfield-commons-2026-09-16-transcript.vtt \
    -o kits/board-minutes/samples/wrenfield-commons-2026-09-16-transcript-clean.txt \
    --speaker-map-file kits/board-minutes/samples/wrenfield-commons-speaker-map.txt
```

- Reads Zoom, Teams and YouTube `.vtt`, `.srt`, Otter/Rev/Teams/Zoom `.txt` exports, and `.docx` transcripts.
- Removes caption numbers, markup and repeated caption lines, and joins captions from the same speaker. A long speech gets a new paragraph every 90 seconds (`--split-after`).
- Removes filler words (um, uh, er, hmm, ah) but keeps "uh-huh" and "mm-hmm". Use `--keep-fillers` to keep them all.
- Prints a speaker summary and flags labels that need checking, such as device names ("Helen's iPhone") or "Speaker 2". Rename them with `--speaker-map "OLD=NEW"` (repeatable) or a `--speaker-map-file`.
- `--clock-start 19:00:30` adds clock times beside recording times. Only use it if you know when the recording started and it was never paused.
- `--format json` writes the turns as JSON.

### 2. check_minutes.py --scan

Lists the key moments in a transcript (motions, seconds, votes, results, tasks, closed session, arrivals, recording mentions) with their times. Use it as a map while you write or check the minutes:

```sh
$PY kits/board-minutes/scripts/check_minutes.py --scan kits/board-minutes/samples/wrenfield-commons-2026-09-16-transcript-clean.txt
```

### 3. build_minutes.py

Builds the Word minutes and the Excel workbook from the JSON. It checks the JSON against the schema first and stops with a clear list of problems if anything is wrong.

```sh
$PY kits/board-minutes/scripts/build_minutes.py kits/board-minutes/samples/wrenfield-commons-2026-09-16-minutes.json --pdf
```

Writes, next to the JSON (or into `--out-dir`):
- `…-minutes.docx`: the minutes, with a DRAFT box, attendance table, numbered agenda items, a box for each motion, signature lines, and two appendices (action items and a summary of motions). [UNCLEAR] markers are highlighted in yellow.
- `…-motions.xlsx`: sheets for Motions, Action Items (with a Status column), Questions (with an empty Answer column for the secretary) and Meeting facts.
- `…-minutes.pdf` with `--pdf`.

Options: `--template client.docx` (see below), `--name` (base file name), `--no-appendix`, `--no-xlsx`.

### 4. check_minutes.py

```sh
$PY kits/board-minutes/scripts/check_minutes.py \
    kits/board-minutes/samples/wrenfield-commons-2026-09-16-minutes.json \
    --transcript kits/board-minutes/samples/wrenfield-commons-2026-09-16-transcript-clean.txt \
    --questions-out kits/board-minutes/samples/wrenfield-commons-2026-09-16-questions.md
```

**Errors** must be fixed: vote counts that don't add up or don't match the result, a mover who is also the seconder, a quorum that doesn't add up, [UNCLEAR] markers with no questions, leftover TODO text, impossible dates. **Warnings** need a look: names or amounts not found in the transcript, more votes called in the transcript than recorded in the minutes, movers who aren't listed as present, missing owners or due dates, a long executive session summary, residents named in the minutes. `--questions-out` writes the questions for your email. `--strict` treats warnings as errors.

### 5. make_template.py

Rewrites `templates/minutes-template.docx`. Use `--locale en-GB` for A4 paper and `--no-appendix` to leave out the appendices:

```sh
$PY kits/board-minutes/scripts/make_template.py -o my-template-a4.docx --locale en-GB
```

## Using a client's own template

Give `build_minutes.py` any `.docx` that contains placeholders:

```sh
$PY kits/board-minutes/scripts/build_minutes.py minutes.json --template work/acme-hoa/input/acme-template.docx
```

Open the client's template in Word, type placeholders where their blanks are, and save it as `.docx`. The template's fonts, logo, header and footer stay as they are. Two kinds of placeholder:

**Short placeholders** go inside a line of text and take that line's formatting, for example `Date: {{meeting_date}}`. They also work in headers, footers and table cells. Capitals work too (`{{ORGANIZATION}}`).

| Placeholder | Becomes |
|---|---|
| `{{organization}}`, `{{organization_short}}`, `{{board_name}}` | Association name, short name, "Board of Directors" |
| `{{meeting_title}}` | "Regular Meeting of the Board of Directors" |
| `{{meeting_date}}`, `{{meeting_date_short}}` | "Wednesday, September 16, 2026", "September 16, 2026" |
| `{{scheduled_time}}`, `{{called_to_order}}`, `{{adjourned}}` | "7:00 p.m.", "7:02 p.m.", "7:36 p.m." |
| `{{location}}`, `{{meeting_when_where}}` | The location; date · time · location on one line |
| `{{presiding}}`, `{{recording_secretary}}`, `{{secretary}}` | "Diane Okafor, President" |
| `{{directors_present}}`, `{{directors_absent}}`, `{{others_present}}` | Names and titles separated by semicolons, or "None" |
| `{{members_present}}`, `{{quorum}}` | "Nine homeowners"; the quorum sentence |
| `{{next_meeting}}` | The next-meeting sentence |
| `{{status}}`, `{{status_line}}`, `{{footer_note}}` | "DRAFT"; "Draft minutes, subject to approval by the Board of Directors"; the same plus "Confidential." |
| `{{prepared_by}}`, `{{prepared_on}}`, `{{notice}}` | From the `document` section |

**Block placeholders** must be alone on their own line, in the main text (not in a header or footer):

| Placeholder | Becomes |
|---|---|
| `{{NOTICE}}` | The DRAFT box (and the notice line) |
| `{{MEETING_DETAILS}}` | Table: presiding, secretary, times, attendance, quorum |
| `{{ATTENDANCE}}` | Table: attendance and quorum only |
| `{{ITEMS}}` | Every agenda item with its heading, summary and motion boxes |
| `{{ITEM 5}}` | Just item 5's content, under a heading the template already has. `{{ITEMS}}` then skips item 5. |
| `{{ACTION_ITEMS}}` | Action items table |
| `{{MOTIONS_TABLE}}` | Summary of motions table |
| `{{ATTACHMENTS}}` | Attachments list (nothing if there are none) |
| `{{SIGNATURES}}` | "Respectfully submitted", signature and date lines, approval line |

If a placeholder is misspelled, in the wrong place or refers to a missing item, the build stops and says which one. Missing styles are added to the template automatically, using the template's own fonts. To change the kit's own look, open `templates/minutes-template.docx` in Word, change the styles whose names start with "Minutes", save it under a new name and pass it with `--template`.

## How to use the skill

The skill at `.claude/skills/board-minutes/SKILL.md` tells Claude Code how to run the whole process: setup, cleaning the transcript, writing the JSON without inventing anything, building the files, running the checks, reviewing the PDF, and reporting back with the questions for the secretary.

1. Put the client's files in a job folder, for example `kits/board-minutes/work/acme-hoa/2026-10-14/input/`.
2. In Claude Code, type `/board-minutes kits/board-minutes/work/acme-hoa/2026-10-14`, or just ask: "Draft the minutes for the transcript in kits/board-minutes/work/acme-hoa/2026-10-14/input". Mention anything the files don't say: the board list, the quorum rule, whether to name residents, the client's template.
3. Claude works through the steps and finishes with the file list, the check results, the questions for the secretary and anything you should verify yourself.
4. Do your own review (step 8 above) before anything goes to the client.

Claude Code loads project skills from `.claude/skills/` automatically, including in new cloud sessions of this repo. If `/board-minutes` doesn't appear in a session where the folder was only just created, run `/reload-skills`.

## The portfolio sample

`samples/` holds a complete, entirely fictional job: the Wrenfield Commons HOA board meeting of September 16, 2026, a 29-minute Zoom recording with eight motions (one roll call vote, one abstention, one committee motion that needed no second, one postponement), an executive session, and nine action items.

| File | What it is |
|---|---|
| `…-agenda.md` | The agenda the "client" sent, with the board list |
| `…-transcript.vtt` | The raw Zoom transcript, with realistic speech-to-text errors ("Renfield", "Lindquist", "Aqua Shore") and a device name as a speaker label |
| `wrenfield-commons-speaker-map.txt` | Renames "Helen's iPhone" to Helen Whitaker |
| `…-transcript-clean.txt` | Output of `clean_transcript.py` |
| `…-minutes.json` | The minutes data. `_note` fields explain each judgment call. |
| `…-minutes.docx` / `.pdf` | The finished draft minutes (6 pages) |
| `…-motions.xlsx` | Motions, action items, questions, meeting facts |
| `…-questions.md` | The questions for the secretary |

It also shows the hard parts done right: two directors seconding at once, two different figures quoted for one bid, a task given to no one by name, and a recording that ran into executive session. The first three are marked [UNCLEAR] and asked about; the closed-session talk is left out and the client is told.

**Showing it to prospects:** send the PDF (it's labelled as a fictional sample) and point to the yellow [UNCLEAR] highlights. They show you check and ask rather than guess, which is what boards worry about. Put your name in `document.prepared_by` and rebuild if you want it in the file properties. Never show a real client's minutes without written permission.

## Running the tests

```sh
$PY -m pytest kits/board-minutes/tests -q
```

The tests cover the transcript formats, filler removal, speaker renaming, the Word and Excel output, client templates and their error messages, UK format, all the checks, and that the committed sample files match a fresh build. If you change the sample JSON, rebuild with `build_minutes.py … --pdf` so the tests and the files stay in step.
