---
name: redcap-xlsform
description: Converts a research questionnaire or case report form (Word, PDF or text) into a validated REDCap data dictionary CSV and/or a KoboToolbox/ODK XLSForm, then makes the codebook, test checklist, delivery note and a tested data-cleaning script, using the scripts in kits/redcap-xlsform. Use when asked to build, convert, check or fix a REDCap data dictionary, XLSForm, CRF, survey form, branching logic, calculated field or codebook, or to write a cleaning script for a REDCap export.
argument-hint: "[questionnaire file] [redcap | xlsform | both]"
---

# REDCap and XLSForm form building

Input from the user: $ARGUMENTS
(If empty, ask for the questionnaire file and which platform: REDCap, XLSForm or both.)

The kit is in `kits/redcap-xlsform/` (paths below are relative to the repository root).
Its README explains the service; `reference.md` next to this file has the syntax rules.

## Rules that always apply

1. **Structure only.** Never ask for, open or process real participant data: no real exports,
   no screenshots with data, no access to live projects. If the user shares data by mistake,
   do not read it; tell them to delete it. Test only with `make_fake_export.py` data.
2. **Approved wording is fixed.** Copy question text, answer options, instructions and units
   word for word from the approved version. Do not correct, shorten or "improve" it. If the
   screen needs an adaptation (e.g. "mark the line" becomes a slider note), make it in a field
   note or hint and list it for the client's approval.
3. **Published scales.** If the questionnaire contains a published scale, check its terms.
   Some are free to use (e.g. PHQ-9, GAD-7); others (e.g. EQ-5D, SF-36v2/SF-12v2, MMAS-8)
   need a licence that covers electronic use, so stop and confirm the client holds it. Record
   the answer in the delivery note, copy every scale exactly, and never put licensed items in
   samples or portfolio material.
4. **Never invent study rules.** Cut-offs, eligibility, visit windows and scoring come from the
   questionnaire or the client. If unclear, write it down as a question for the client.
5. The client imports and tests in their own test project. Do not ask for logins.
6. Do not put AI model names or IDs in any deliverable.

## Setup (once per session)

```bash
test -x /tmp/redcap-venv/bin/python || bash kits/setup.sh redcap-xlsform
```

`bash kits/setup.sh redcap-xlsform` is the setup route (needs Python 3.10 or newer), and
`bash kits/setup.sh --list` shows this kit's Python: `/tmp/redcap-venv/bin/python`. Run every
command below with it, never with a bare `python` or `python3`. If `kits/setup.sh` is missing
or fails, run `python3 -m venv /tmp/redcap-venv && /tmp/redcap-venv/bin/pip install -q -r kits/redcap-xlsform/requirements.txt`.
To confirm the kit works: `/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/selftest.py`
(every check must PASS).

Run the commands from the repository root. Make a work folder for the job there, outside the
kit, e.g. `work/<project>/` with `input/ redcap/ xlsform/ codebook/ test_data/ delivery/`
(git ignores `work/`). Client questionnaires are confidential: keep them there and never
commit them.

## Workflow

### 1. Read the questionnaire

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/extract_text.py work/<project>/input/<file> -o work/<project>/input/questionnaire.txt
```

Also look at the layout (convert to PDF and view pages: `soffice --headless --convert-to pdf`,
then `pdftoppm -png -r 70`), because tick boxes, grids and "go to question 7" arrows carry meaning.
Make a question inventory: number, exact text, answer type, options, skip instruction, notes.
Count the questions and check the count against the document before building.

### 2. Plan the build (write it to `work/<project>/build_plan.md`)

- Instruments (one per paper form or logical section) and, for multi-visit studies, events
  (unique names like `visit_1_arm_1`), which instruments go in which event, and which repeat.
- Variable names: lowercase, letters/numbers/underscores, start with a letter, 26 characters
  or fewer, a short prefix per form (`scr_`, `fu_`), the same name for the same question.
- Codes: whole numbers, the same coding everywhere (1 = Yes, 0 = No; 98 = Not sure;
  99 = Prefer not to say). Keep the order of options from the document.
- Calculations, identifiers (name, date of birth, contact details, record numbers: flag them;
  put contact details on their own form if asked), required questions, date format.
- Open questions for the client.

### 3. Build the REDCap data dictionary

Write it with a short Python script using the `csv` module (never by hand: commas and quotes
in labels break CSV). Start from the 18 headers in
`kits/redcap-xlsform/templates/data_dictionary_template.csv`. The first field is the record ID.
Follow `reference.md` for field types, validation, branching logic, calculations, matrices and
action tags. Write `instrument_event_mapping.csv` (arm_num, unique_event_name, form) and
`repeating_instruments.csv` (event_name, form_name, custom_form_label) for longitudinal studies.

### 4. Check it and fix until it passes

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/validate_redcap.py work/<project>/redcap/<name>_data_dictionary.csv \
  --events work/<project>/redcap/instrument_event_mapping.csv \
  --repeating work/<project>/redcap/repeating_instruments.csv \
  --report work/<project>/redcap/validation_report.txt
```

Exit code 0 means no errors. Fix every error. Fix each warning or write down why it is intended
(it goes in the delivery note). Re-run until clean.

### 5. Build the XLSForm (if requested)

Write `survey.csv`, `choices.csv` and `settings.csv` in `work/<project>/xlsform/source/`
(use `label::English (en)` style columns, same variable names and codes as REDCap, a
`version` in settings), then:

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/build_xlsform.py work/<project>/xlsform/source -o work/<project>/xlsform/<name>.xlsx
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/check_xlsform.py work/<project>/xlsform/<name>.xlsx \
  --xml work/<project>/xlsform/<name>.xml --report work/<project>/xlsform/xlsform_check_report.txt
```

To edit a client's existing XLSForm, split it first:
`/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/build_xlsform.py --split work/<project>/input/<form>.xlsx -o work/<project>/xlsform/source`.
REDCap-to-XLSForm equivalents are in `reference.md`. ODK forms cannot see earlier submissions,
so cross-visit calculations move to analysis (say so in the delivery note).

### 6. Check the wording against the approved document

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/check_wording.py --source work/<project>/input/<file>.docx \
  --dictionary <dictionary.csv> --xlsform <form.xlsx> --report work/<project>/delivery/wording_check.txt
```

Every "differs" or "not found" item must be either fixed or listed in the delivery note with a reason.

### 7. Make the codebook

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/make_codebook.py --dictionary <dictionary.csv> --events <mapping.csv> \
  --repeating <repeating.csv> --title "<study title>" --out work/<project>/codebook/<name>_codebook \
  --logic-table work/<project>/delivery/skip_logic_tests.md
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/make_codebook.py --xlsform <form.xlsx> --out work/<project>/codebook/<name>_kobo_codebook
```

### 8. Test the cleaning script on fake data

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/make_fake_export.py --dictionary <dictionary.csv> --events <mapping.csv> \
  --repeating <repeating.csv> --records 25 --errors 8 --seed 1 --out work/<project>/test_data/fake_export.csv
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/clean_export.py --dictionary <dictionary.csv> --export work/<project>/test_data/fake_export.csv \
  --events <mapping.csv> --rules work/<project>/test_data/cleaning_rules.csv \
  --answer-key work/<project>/test_data/fake_export_answer_key.csv --outdir work/<project>/test_data/cleaning_output
```

The answer-key line must say every deliberate mistake was found. Use `--event-logic` and
`--repeat-logic` (see `--help`) so fake visits follow the study design. Put study-specific
checks in `cleaning_rules.csv` (columns `rule,logic`, REDCap syntax, flagged when TRUE) only
when they come from the protocol or the client. Copy `clean_export.py`, the two helper modules
it imports (`redcap_dictionary.py`, `redcap_logic.py`) and the rules file into the delivery.

### 9. Fill in the client documents

Copy `kits/redcap-xlsform/templates/client_test_checklist.md` and `delivery_note.md` into
`work/<project>/delivery/`, fill every [placeholder] (paste the skip-logic table into section C;
list wording differences, decisions and open questions), then:

```bash
/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/md_to_docx.py work/<project>/delivery/*.md --outdir work/<project>/delivery
```

Look at `kits/redcap-xlsform/samples/08_delivery/` for a finished example. To put the user's
name on that portfolio sample, replace `[your name]` in the "Prepared by" row of
`kits/redcap-xlsform/samples/08_delivery/delivery_note.md`, then run
`/tmp/redcap-venv/bin/python kits/redcap-xlsform/scripts/md_to_docx.py kits/redcap-xlsform/samples/08_delivery/delivery_note.md`.

### 10. Final check before telling the user it is ready

- [ ] validate_redcap.py: 0 errors; warnings fixed or explained
- [ ] check_xlsform.py: 0 errors, ODK Validate ran (needs Java)
- [ ] Every skip instruction in the document has logic; every calculation checked by hand
      with two sets of test values (put them in the delivery note)
- [ ] Wording check reviewed; identifiers flagged; codes consistent across forms
- [ ] Codebook made from the final files; answer key fully found
- [ ] No participant data anywhere; delivery note lists everything the data dictionary cannot set
      (events, arms, repeating setup, surveys, user rights, missing-data codes)

Then report to the user: files made (paths), check results (errors/warnings/notes),
wording differences, open questions for the client, and anything they must do by hand.

## When something fails

- Validator errors are explained in plain English with a "Fix:" line; fix the CSV-writing
  script, not the CSV by hand, so fixes are not lost on the next run.
- `check_xlsform.py` shows the pyxform/ODK message plus a plain-English line. If Java is
  missing, ODK Validate is skipped; say so in the report.
- If a REDCap feature cannot be expressed in the data dictionary, add it to the delivery note
  as a manual setup step for the client.
