---
name: security-questionnaire
description: Answer a client's security questionnaire (SIG Lite, CAIQ-style or a custom vendor due-diligence spreadsheet) using only the client's own policies and written answers, and build or update the client's reusable answer library. Use when asked to fill, answer, review or finalise a security questionnaire, vendor security assessment or due-diligence spreadsheet; to draft an answer library from policy documents; to list gaps to send a client; or to add a client's answers to their library.
---

# Security questionnaire service

You help a freelancer answer security questionnaires for small B2B software companies, using only the client's documents. The kit is in `kits/security-questionnaire/` (read its `README.md` for the full process, prices and templates). Run commands from the repository root.

## Rules you must follow

1. **Answers are the client's statements to its customer.** Use only the client's documents and their dated written answers. Never invent or "assume" a control, date, number, tool, frequency or certification, and never fill a gap with what companies "usually" do.
2. **Every answer cites its source**: document and section, or "Written answers from [name], [date]" with the question number. If no source supports it, the answer is **NEEDS CLIENT INPUT**.
3. **The client's technical owner reviews and signs off** every answer before it reaches the buyer. Only library rows with Status **Approved** are used to fill questionnaires; you may draft, but only the client approves.
4. **Never pose as an auditor.** Don't write that anything is certified, audited, attested or "compliant with" a standard unless the client has the certificate or report. Don't describe your work as an assessment.
5. **Confidential.** Client files live only in `kits/security-questionnaire/clients/<client>/` (git-ignored; this repository is public). If the user's files are anywhere else in the repository, copy them there first (`clients/` at the repository root is git-ignored too). Every file you write for the client goes in that folder. Never commit, upload, publish or paste client content anywhere else, never put it in an artifact or public page, and offer to delete the folder when the engagement ends.
6. **Honest gaps beat overclaims.** "No" and "Not yet" are valid answers. When in doubt, ask.

## Setup (once per session)

```sh
test -x ~/.venvs/security-questionnaire/bin/python || bash kits/setup.sh security-questionnaire
```

`bash kits/setup.sh security-questionnaire` is the usual setup route. The kit's Python is `~/.venvs/security-questionnaire/bin/python` (the security-questionnaire line of `bash kits/setup.sh --list`). Run every script below with it, never with a bare `python` or `python3` (they don't have the kit's packages). If `kits/setup.sh` is missing or fails, create the environment directly: `python3 -m venv ~/.venvs/security-questionnaire && ~/.venvs/security-questionnaire/bin/pip install -r kits/security-questionnaire/requirements.txt`. Paths start from the repository root.

## Workflow

### 1. Intake

Confirm (or ask for) everything in `kits/security-questionnaire/templates/client_intake_checklist.md`: NDA signed, deadline, the technical owner, whether answers may name internal policies, and what must never appear in an answer. Put documents in `kits/security-questionnaire/clients/<client>/docs/`.

### 2. Draft the library

```sh
~/.venvs/security-questionnaire/bin/python kits/security-questionnaire/scripts/build_library.py --docs kits/security-questionnaire/clients/<client>/docs --out kits/security-questionnaire/clients/<client>/answer_library.xlsx --client "<Client>" --owner "<Name, Title>"
```

Report the document list and any warnings (scanned PDFs, skipped .doc files: ask for text versions). If the client already has a library, pass it as `--questions` instead of the default question bank.

### 3. Write answers from the sources

For every row with Status **Draft**:

- Read the cited section in the document itself, plus the Evidence sheet's other candidates. The match is lexical, so also read each document in full once: the best source may not be the top candidate.
- Decide whether the source really answers the canonical question. Reject look-alikes, for example: text about the client's *vendors* (their SOC 2 reports, their DPAs) is not evidence about the client; "customer managed keys" in AWS terms means keys the client manages, not keys its customers manage; staff single sign-on is not SSO for customers; backup retention is not log retention. Rejected rows become NEEDS CLIENT INPUT with a note saying why.
- Write **Approved Answer** in the client's voice ("Quarterhour ..."), present tense, 1 to 3 sentences, using only facts in the source. Keep its scope and qualifiers ("for production systems", "where supported", "at least annually"). Never upgrade "should" to "must", "planned" to "in place", or "some" to "all". Start with "Yes." or "No." when the canonical question is yes/no.
- **Short Answer**: Yes, No, Partial (in place only for some systems or people) or N/A (explain why in the answer). For open questions, use the answer to the yes/no version.
- Fill **Source Document**, **Source Section** and **Source Excerpt** (the supporting sentence, copied word for word), and **Confidence**: High if stated directly, Medium if pieced together from several places or interpreted, Low if partly supported.
- Leave **Status** as Draft. Only the client's approval makes it Approved.

Edit the library with openpyxl, run with `~/.venvs/security-questionnaire/bin/python` (the library is the kit's own file). Keep the column headers, IDs and drop-down values; never reuse an ID. Afterwards run:

```sh
~/.venvs/security-questionnaire/bin/python kits/security-questionnaire/scripts/build_library.py --check kits/security-questionnaire/clients/<client>/answer_library.xlsx --gaps kits/security-questionnaire/clients/<client>/questions_for_client.md --client "<Client>"
```

Fix every ERROR. Read every "could overstate" warning against the source.

### 4. Gaps and client answers

Send `questions_for_client.md` (or summarise it). When the client replies, save the reply as a dated document in their folder (for example `kits/security-questionnaire/clients/<client>/client_input/written-answers-2026-09-30.md`), then update each row: answer, short answer, source "Written answers from <name>, <date>", section "Q<n>", excerpt. When the client approves rows, set Status Approved, Owner and Last Reviewed, and add a line to the Change Log sheet.

### 5. Fill the buyer's questionnaire

```sh
~/.venvs/security-questionnaire/bin/python kits/security-questionnaire/scripts/fill_questionnaire.py kits/security-questionnaire/clients/<client>/<buyer-file>.xlsx --library kits/security-questionnaire/clients/<client>/answer_library.xlsx --dry-run
~/.venvs/security-questionnaire/bin/python kits/security-questionnaire/scripts/fill_questionnaire.py kits/security-questionnaire/clients/<client>/<buyer-file>.xlsx --library kits/security-questionnaire/clients/<client>/answer_library.xlsx
```

Check the dry run's detected sheet, header row and columns before writing. If anything is wrong, set it (`--sheet`, `--header-row`, `--question-col`, `--answer-col`, `--short-col`, `--comment-col`, `--source-col none`) or save the settings with `--config`. Ask before using `--source-mode review-only` or `append` if the client hasn't said whether internal policy names may appear. The original file is never changed; the output is `kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT.xlsx` with the sheet "Review - remove before sending". If the user wants their name on the review sheet, add `--prepared-by "<their name or business>"`.

### 6. Review pass (you, then the human)

Go through the review sheet in order: NEEDS CLIENT INPUT, then CHECK, then every OK row.

- **Wrong match**: find the right entry yourself (you understand meaning; the script compares words). Put its ID in "Use library ID" (or NONE), add the buyer's wording to that entry's Alternate Phrasings in the library, and rerun on the **original** file with `--use-review kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT.xlsx --out kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT2.xlsx`.
- **Partly answered** (two questions in one, asks for a date or an attachment): complete it only from approved library entries or sources; otherwise list it for the client. Pen-test dates, report copies and insurance limits always come from the client.
- **Reversed wording** ("Are shared accounts used?"): make sure the Yes/No matches the answer text.
- Note anything for the client in "Reviewer notes"; mark "Resolved" Y only when an item is truly settled.
- To change a cell in the buyer's file by hand, never re-save it with openpyxl (that can drop drop-downs, shapes and other features). Use the kit's writer with the kit's Python. It changes only the cells you name; save to a new file in the client folder:

```sh
~/.venvs/security-questionnaire/bin/python - <<'PYEOF'
import sys; sys.path.insert(0, "kits/security-questionnaire/scripts")
from xlsx_patch import XlsxPackage
pkg = XlsxPackage("kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT2.xlsx")
pkg.set_cells("Questionnaire", {"E12": "No. ...", "F12": "Source: ..."})
pkg.save("kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT3.xlsx")
PYEOF
```

Summarise for the human: counts (OK / CHECK / NEEDS CLIENT INPUT), the questions the client must answer, and anything you corrected. Then draft the email from part A of `kits/security-questionnaire/templates/cover_note.md`.

### 7. Finalise

After the client has answered the gaps (library updated, questionnaire refilled) and the technical owner has signed off:

```sh
~/.venvs/security-questionnaire/bin/python kits/security-questionnaire/scripts/fill_questionnaire.py --finalize kits/security-questionnaire/clients/<client>/<buyer-file>_DRAFT2.xlsx --out kits/security-questionnaire/clients/<client>/<buyer-file>_FINAL.xlsx
```

It refuses while "NEEDS CLIENT INPUT" text remains or any NEEDS/CHECK row isn't Resolved = Y. Use `--force` only if the client explicitly accepts the open items. Deliver with part B of the cover note and the updated library.

## Before anything is delivered

- [ ] Every answer read by a person; every source opened and checked
- [ ] No claim stronger than its source; no invented certifications, dates, tools or numbers
- [ ] Yes/No consistent with the answer text and the question's direction
- [ ] Nothing the client asked to keep out (hostnames, staff names, internal policy names if they said no)
- [ ] No placeholder text left; review sheet removed (`--finalize`)
- [ ] Technical owner's sign-off saved; library updated (Approved, owner, date, Change Log, new alternate phrasings)

## Reference

- Matching: score 0 to 1 = 70% TF-IDF keyword match + 30% rapidfuzz fuzzy match; OK at 0.50 or more, CHECK from 0.25, lower means NEEDS CLIENT INPUT. Wrong matches usually score under 0.45, which is why CHECK exists. Synonym groups (MFA, SSO, etc.) are in `kits/security-questionnaire/scripts/sqkit.py`.
- Library columns and allowed values: the Readme sheet in `kits/security-questionnaire/templates/answer_library.xlsx`.
- A worked example (fictional company and buyer): `kits/security-questionnaire/samples/README.md`.
