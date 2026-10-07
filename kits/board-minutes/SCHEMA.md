# The minutes JSON format (version 1.0)

Every set of minutes starts as one JSON file. `build_minutes.py` turns it into the Word minutes and the Excel workbook, and `check_minutes.py` checks it. This page explains each field.

- Machine-readable version: [`scripts/minutes.schema.json`](scripts/minutes.schema.json) (JSON Schema). The scripts check every file against it.
- Full example: [`samples/wrenfield-commons-2026-09-16-minutes.json`](samples/wrenfield-commons-2026-09-16-minutes.json)
- Blank starting point: [`templates/minutes-skeleton.json`](templates/minutes-skeleton.json)

## Rules that apply everywhere

- **Dates** are `YYYY-MM-DD` (`2026-09-16`). **Times** are 24-hour `HH:MM` (`19:02` for 7:02 p.m.). The scripts format them for the document, for example "Wednesday, September 16, 2026" and "7:02 p.m.".
- **`[UNCLEAR]`**: put `[UNCLEAR]` or `[UNCLEAR: short note]` wherever you can't confirm something, for example `"seconded_by": "[UNCLEAR: Raymond Castillo or Grace Lindqvist]"`. Time fields and the next meeting date also accept it. Each marker is highlighted in yellow in the Word file and needs a matching entry in `questions`.
- **Write text exactly as it should appear in the minutes:** full sentences, past tense, neutral wording. Straight quotes become curly quotes automatically.
- **Names:** use full names, spelled as on the client's board list, every time.
- **Your own notes:** any key that starts with `_` (for example `"_note": "..."`) is ignored by the scripts and never printed.
- **`source`:** where something is in the recording, as `00:12:40` or `00:12:40-00:15:05`. It isn't printed in the minutes, but it appears in the spreadsheet and helps you check things later.
- **Typos are caught:** a misspelled field name (such as `seconder` instead of `seconded_by`) stops the build with a clear message.

## Top level

| Field | Required | What it holds |
|---|---|---|
| `schema_version` | yes | Always `"1.0"`. |
| `document` | no | Draft or approved, US or UK format, notice box. |
| `organization` | yes | The association's name. |
| `meeting` | yes | Title, date, times, place, who presided. |
| `attendance` | yes | Who was there, and the quorum. |
| `items` | yes | The agenda items in the order they were taken up. |
| `action_items` | no | Tasks: who does what, by when. |
| `next_meeting` | no | The next meeting, or `null` if none was announced. |
| `attachments` | no | List of documents attached to the minutes, as text. |
| `questions` | no | Questions for the secretary. Every `[UNCLEAR]` needs one. |
| `signatures` | no | Who signs, and the approval line. |

## `document`

| Field | Values | What it does |
|---|---|---|
| `status` | `"draft"` (default) or `"approved"` | Drafts get a DRAFT box at the top and "Draft minutes, subject to approval" in the footer. |
| `locale` | `"en-US"` (default) or `"en-GB"` | US: Letter paper, "September 16, 2026", "7:02 p.m.", "in favor". UK: A4 paper, "16 September 2026", "7.02pm", "in favour". |
| `notice` | text | Extra line in the box at the top, for example "Portfolio sample: ... fictional." |
| `prepared_by` | text | Your name or business. Saved as the file's author. |
| `prepared_on` | date | When you prepared the draft. |
| `approved_on` | date | When the board approved the minutes (use with `"status": "approved"`). |
| `confidential` | `true` / `false` | Adds "Confidential." to the footer. Default: `true` for drafts, `false` for approved minutes. |

## `organization`

| Field | Required | Example |
|---|---|---|
| `name` | yes | `"Wrenfield Commons Homeowners Association"` |
| `short_name` | no | `"Wrenfield Commons HOA"` (page header and file title) |
| `board_name` | no | Default `"Board of Directors"`. Use `"Board of Trustees"`, `"Parish Council"` and so on. |
| `board_short` | no | Default `"Board"`. Used in sentences such as "The Board met in executive session". |

## `meeting`

| Field | Required | Example / notes |
|---|---|---|
| `title` | yes | `"Regular Meeting of the Board of Directors"`. The document adds "Minutes of the" in front. |
| `date` | yes | `"2026-09-16"` |
| `scheduled_time` | no | `"19:00"`, from the agenda or notice |
| `called_to_order` | yes | `"19:02"` or `"[UNCLEAR]"`. Use the time the chair announced, not one worked out from the recording. |
| `adjourned` | yes | `"19:36"` or `"[UNCLEAR]"` |
| `location` | no | `"Clubhouse, 210 Wrenfield Drive"` or `"By Zoom videoconference"` |
| `format` | no | `"in_person"`, `"virtual"` or `"hybrid"` (for your records) |
| `presiding` | yes | A person (see below), for example `{"name": "Diane Okafor", "role": "President"}` |
| `recording_secretary` | no | A person. Signs the minutes unless `signatures.secretary` is set. |
| `voting_body` | no | `"board"` (default) or `"members"`. For members' meetings the checker doesn't expect movers to be directors. |

## A person

| Field | Required | Example / notes |
|---|---|---|
| `name` | yes | `"Helen Whitaker"` |
| `role` | no | `"Director at Large"`, `"Community Manager, Hartwell & Finch Community Management"` |
| `attended` | no | `"in_person"`, `"remote"` or `"phone"`. Prints "(by video)" or "(by phone)". Use it for hybrid meetings. |
| `arrived` | no | `"19:14"`. Prints "(arrived 7:14 p.m.)". |
| `left` | no | `"20:05"` |
| `note` | no | `"excused"`, `"left during Item 9"` |

## `attendance`

| Field | Required | Notes |
|---|---|---|
| `group_label` | no | Default `"Directors"`. Use `"Trustees"`, `"Council members"` and so on. |
| `directors_present` | yes | List of people. Include anyone who arrived late, with `arrived`. |
| `directors_absent` | yes | List of people; `[]` if everyone came. |
| `others_present` | no | Manager, attorney, guests. |
| `members_present` | no | Text, for example `"Nine homeowners"`. |
| `quorum` | yes | `met`: `true`, `false` or `null` (unclear). Optional numbers: `present_count` (at the call to order), `board_size`, `required`. Optional `statement` replaces the standard wording. |

## `items`: the agenda items

List them in the order they happened, numbered as on the agenda.

| Field | Required | Notes |
|---|---|---|
| `number` | no | As on the agenda: `"5"`, `"8a"`, `"IV"` |
| `title` | yes | `"Treasurer's Report: August 2026 Financial Statements"` |
| `kind` | no | See the next table. Default `"business"`. |
| `level` | no | `1` (default) or `2` for sub-items such as 8a |
| `presenter` | no | `"Grace Lindqvist, Treasurer"`. Prints "Presenter: ..." under the heading. |
| `summary` | no | List of paragraphs. Start a line with `"- "` to make it a bullet. End a lead-in line with `:` to keep it on the same page as its list. |
| `motions` | no | List of motions (see below). |
| `start`, `end` | no | Executive session only: times. |
| `topics` | no | Executive session only: the general nature, for example `["a delinquent account", "a vendor contract matter"]`. |
| `outcome` | no | Executive session only, for example `"The President reported that no action was taken in executive session."` |
| `source` | no | Recording time. |

Kinds, and the standard wording used when an item has no `summary`:

| `kind` | Use for | Standard wording if `summary` is empty |
|---|---|---|
| `call_to_order` | Call to order | "President Diane Okafor called the meeting to order at 7:02 p.m." |
| `roll_call` | Roll call, quorum | The quorum statement |
| `agenda_approval` | Approval of the agenda | (none) |
| `approval_of_minutes` | Approval of earlier minutes | (none). The checker warns if no item has this kind. |
| `open_forum` | Homeowner or member comments | (none) |
| `report` | Officer, manager and committee reports | (none) |
| `business` | Old and new business (the default) | (none) |
| `executive_session` | Closed session | "The Board met in executive session from 7:26 p.m. to 7:35 p.m. to discuss ...", then `outcome` |
| `next_meeting` | Next meeting | Built from `next_meeting` |
| `adjournment` | Adjournment | "The meeting was adjourned at 7:36 p.m." The checker warns if no item has this kind. |
| `heading` | A heading with nothing under it, such as "8. Old Business" | (none) |
| `other` | Anything else | (none) |

## Motions

| Field | Required | Notes |
|---|---|---|
| `label` | no | Default "Motion 1", "Motion 2" and so on. Use it if the board numbers resolutions, for example `"Resolution 2026-07"`. |
| `text` | yes | The motion as voted, starting with "To", for example `"To approve the minutes of the August 19, 2026 regular meeting as corrected."` |
| `moved_by` | yes | Full name, `"[UNCLEAR]"`, or `null` (for example unanimous consent) |
| `seconded_by` | yes | Full name, `"[UNCLEAR: ...]"`, or `null` |
| `second_note` | no | Why there's no seconder: `"No second required (committee recommendation)"` |
| `on_behalf_of` | no | `"Architectural Review Committee"`. Prints "Moved by Helen Whitaker, on behalf of the Architectural Review Committee". |
| `amendments` | no | List of amendments. Each has `text`, `moved_by`, `seconded_by`, `second_note`, `vote`, `result`, `notes` and `source`. |
| `vote` | no | See below. |
| `threshold` | no | `"majority"` (default), `"two_thirds"`, `"unanimous"` or `"other"`. The checker uses it to test the result. |
| `result` | yes | `"carried"`, `"failed"`, `"withdrawn"`, `"tabled"`, `"postponed"`, `"referred"`, `"ruled_out_of_order"`, `"no_vote"` or `"[UNCLEAR]"` |
| `notes` | no | Printed in small italics under the motion. |
| `source` | no | Recording time of the motion. |

### `vote`

| Field | Notes |
|---|---|
| `method` | `"voice"`, `"show_of_hands"`, `"roll_call"`, `"ballot"`, `"unanimous_consent"`, `"electronic"` or `"[UNCLEAR]"` |
| `in_favor`, `opposed`, `abstained` | Numbers. Fill them only when the chair stated them or you can count them (a roll call). Otherwise leave them out. Don't guess from the number present. |
| `unanimous` | `true` only if the chair said so, or the count shows it. |
| `roll_call` | List of `{"name": "...", "vote": "yes"}`. Votes: `"yes"`, `"no"`, `"abstain"`, `"recused"`, `"absent"`, `"[UNCLEAR]"`. |
| `recused` | List of names. |
| `note` | Printed in small italics. |

How votes print:

| JSON | Printed |
|---|---|
| `{"method": "voice", "in_favor": 4, "opposed": 0}` | CARRIED — 4 in favor, 0 opposed (voice vote) |
| `{"method": "voice", "unanimous": true}` | CARRIED — Unanimous (voice vote) |
| `{"method": "roll_call", "in_favor": 4, "opposed": 1, "roll_call": [...]}` | CARRIED — 4 in favor, 1 opposed (roll call vote), then a "Roll call:" line with each name |
| `{"method": "voice"}` | CARRIED — Voice vote |

## `action_items`

| Field | Required | Notes |
|---|---|---|
| `task` | yes | Starts with a verb: `"Send the approval letter to the owners of 18 Thistle Court."` |
| `owner` | yes | A person, role or committee. `"[UNCLEAR]"` if nobody was named, plus a question. |
| `due` | yes | `YYYY-MM-DD` when the date is certain ("by Friday" after a Wednesday meeting is that Friday; "by the next meeting" is the next meeting's date). Otherwise words: `"Budget workshop"`, `"Not stated"`. |
| `item` | no | The agenda item number, for example `"9c"`. |
| `source` | no | Recording time. |

## `next_meeting`

| Field | Example |
|---|---|
| `description` | `"regular meeting"` (default `"meeting"`) |
| `date` | `"2026-10-21"` or `"[UNCLEAR]"` |
| `time` | `"19:00"` |
| `location` | `"by Zoom videoconference"` or `"at the clubhouse"` |
| `note` | An extra sentence, for example `"The Community Manager will send the link with the meeting packet."` |

Prints: "The next regular meeting of the Board will be held on Wednesday, October 21, 2026, at 7:00 p.m., by Zoom videoconference." Use `"next_meeting": null` if none was announced.

## `questions`

| Field | Required | Example |
|---|---|---|
| `question` | yes | Specific and answerable: `"Was Holloway Landscapes' bid $5,600 or $5,650 per month? ..."` |
| `where` | no | `"Item 9a"`, `"Item 6, Motion 2"` |
| `source` | no | `"00:18:24"` |

Questions are not printed in the minutes. They go in the Questions sheet of the workbook and in the file from `check_minutes.py --questions-out`, which you paste into the handoff email.

## `signatures`

| Field | Default | Notes |
|---|---|---|
| `secretary` | `meeting.recording_secretary` | The person who signs. |
| `submitted_label` | `"Respectfully submitted"` | The line above the signature. |
| `show_approval_line` | `true` | Drafts get "Approved by the Board of Directors on: ____"; approved minutes get the approval date. |
