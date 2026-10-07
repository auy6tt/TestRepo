# Extraction rules: from transcript to minutes JSON

Detailed rules for Step 4 of the board-minutes skill. The field reference is in `kits/board-minutes/SCHEMA.md`.

## Sources, in order of trust

1. What the user tells you (board list, quorum rule, corrections, the secretary's answers).
2. Documents from the client: agenda, board packet, earlier minutes.
3. The transcript, for what was said and decided. It's a machine transcript: names, numbers and short words ("aye", "nay", "second") can be wrong or attributed to the wrong person.

When sources disagree, don't pick one. Use `[UNCLEAR: A or B]` and ask. The exception is spelling: names of people, the association and vendors always come from the documents.

## Header and attendance

- `meeting.title`: from the agenda or notice, for example "Regular Meeting of the Board of Directors" or "Special Meeting of the Board of Directors".
- `called_to_order` and `adjourned`: the times the chair announced ("It's 7:02", "adjourned at 7:36"). Don't work them out from recording timestamps, because recordings start early and get paused. If the chair never says a time, use `[UNCLEAR]` and ask.
- Directors present: everyone the roll call or the transcript shows taking part, with `role` from the board list. Late arrivals get `arrived` (the time announced, or `[UNCLEAR]`); people who leave get `left`.
- Directors absent: board members on the list who weren't there. Add `"note": "excused"` only if someone said so.
- Others present: the manager, attorney, guest presenters, with their roles. Residents are counted in `members_present` ("Nine homeowners") only if someone stated the number.
- Quorum: `met` from what the chair said. `present_count` is the number present when the quorum was established, not counting later arrivals.

## Agenda items

- One JSON item per agenda item, numbered as on the agenda. Sub-items such as "8a" get `"level": 2` under a `"kind": "heading"` item for "8. Old Business".
- If the meeting took items out of order, list them in the order they happened and keep their agenda numbers.
- Items on the agenda but not taken up: include them with a one-line summary ("This item was deferred to the next meeting.") only if the transcript says so. Otherwise ask.
- Business that was on no agenda: add it where it happened, numbered as an added item, and mention it in your report.

## Summaries

- Report decisions and the main facts behind them: amounts, bids, dates, reasons stated. Leave out side talk, technical problems, jokes and repetition.
- Usually one to four sentences per item. Reports with many figures read best as bullets (`"- "` at the start of a line). End a lead-in line with a colon.
- Attribute views only when it matters for the record ("Directors Castillo and Whitaker preferred to wait for the third bid"); otherwise "Directors discussed ...".
- Neutral words: "noted", "reported", "asked", "discussed". Never "heated", "excellent", "unfortunately", and never characterize anyone.
- No direct quotes, unless the board asked for a statement to be recorded word for word.
- Copy numbers exactly as stated ($48,212.67). Don't round, total or convert unless you say so.

## Motions

- `text` is the motion as finally voted, starting with "To": "To approve the minutes of the August 19, 2026 regular meeting as corrected." If the chair restated the motion before the vote, use the restated wording. If the wording isn't clear, use the closest clear wording and add a question.
- `moved_by` and `seconded_by` are full names. "So moved" and "Second" count. If two people second at once and the chair names neither, use `[UNCLEAR: A or B]`. If the chair names the seconder, use that name.
- No second needed (a motion from a committee, or the board's practice): `"seconded_by": null` and a `second_note`. A motion that died for lack of a second: `"result": "no_vote"`, `"seconded_by": null`, `"second_note": "Died for lack of a second"`, and no vote.
- Approval "without objection" or "by unanimous consent": `"vote": {"method": "unanimous_consent"}`, `"moved_by": null`, `"seconded_by": null`, `"result": "carried"`. A simple agenda approval can instead be a one-line summary.
- Amendments: put the final wording in `text` and list the amendments under `amendments`, each with its own mover, seconder, vote and result. "Friendly" amendments accepted without a vote: mention them in `notes`.
- Motions to postpone, table or refer are motions in their own right: record what the board voted on, with `"result": "carried"` when the board voted in favor of postponing.
- A motion withdrawn before the vote: `"result": "withdrawn"` and no vote.
- Use `on_behalf_of` when a director moves a committee's recommendation.

## Votes

- `method`: how the vote was taken (voice, show of hands, roll call, ballot, electronic). Use `[UNCLEAR]` if you can't tell.
- Counts (`in_favor`, `opposed`, `abstained`) only when the chair announced them ("four to one") or you can count each person's vote (roll call). Never work them out from the number of people present.
- "Carries unanimously" or "that's unanimous": `"unanimous": true`. With a stated count, give both.
- Roll calls: list every name in `roll_call` with yes, no, abstain, recused or absent, and fill the counts to match.
- Abstentions and recusals: record who and, if stated, why (in the item's summary, as the sample does).
- `result` from what the chair declared. If the chair declared nothing and the votes are unclear, use `[UNCLEAR]` and ask.

## Action items

- An action item is a task someone agreed to do or was asked to do, with a clear owner: "I'll send it by Friday", "Priya, please get two quotes".
- `owner`: the person, role or committee. If the chair asks "can somebody look into it?" and nobody is named, use `[UNCLEAR]` and ask.
- `due`: turn relative dates into `YYYY-MM-DD` only when the meaning is certain: "tomorrow", "by Friday", "by the end of the month", "for the next meeting" (use the next meeting's date). Otherwise use words ("Budget workshop", "Not stated") or `[UNCLEAR]`. List every conversion in your report.
- One task per action item, starting with a verb.

## Executive session

- Record only: start and end times as announced, the general topics as the chair stated them (`topics`), and the `outcome` stated in open session ("no action was taken in executive session").
- Votes taken in open session afterwards (for example referring an account to the attorney) are normal motions under the next item. Use the wording used in open session (an account number, not a name).
- If the recording kept running into executive session, leave everything said there out of the minutes, the questions and your report summary. Add a question telling the secretary the recording captured part of the closed session.

## Open forum

- Summarise each topic in one or two sentences without names: "A homeowner raised speeding on Wrenfield Drive". Include the board's response and any task.
- Name residents only if the user says the client wants names.

## Questions for the secretary

- One question per unclear point, specific enough to answer in a sentence: who, which figure, which wording.
- Give the options you heard and the recording time (`source`). Say where it is in the minutes (`where`, for example "Item 6, Motion 2").
- Also ask about things the minutes need but the meeting didn't say: a missing adjournment time, an unnamed seconder, a late arrival time.

## Before you build

- Every person named in the JSON is on the board list, the agenda, or in the transcript.
- Every `[UNCLEAR]` has a question, and every question points to something real.
- Nothing from closed session is in any field.
- `document.status` is `"draft"`.
