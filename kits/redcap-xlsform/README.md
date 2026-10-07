# REDCap and XLSForm form-building kit

A starter kit for one paid service: **turning a study team's approved questionnaire into forms they can import and use**, with the checks and documents that make the job look professional from day one.

- **For REDCap:** a data dictionary CSV ready to upload, with validation, skip logic (branching logic), calculated fields, and set-up notes for repeat visits and repeating forms.
- **For KoboToolbox or ODK:** an XLSForm (.xlsx) that passes the official converter and ODK Validate.
- **For every job:** a codebook (Word and web page), a test checklist for the client, a delivery note, and a data-cleaning script for their exports, tested on fake data.

Everything here was run and checked in this repository. The sample study in `samples/` is entirely fictional and is your first portfolio piece.

## Contents

- [The offer](#the-offer)
- [Who buys and where to find them](#who-buys-and-where-to-find-them)
- [Price guide](#price-guide)
- [Step-by-step process](#step-by-step-process)
- [Quality checklist](#quality-checklist-before-you-deliver)
- [Ethics and data rules](#ethics-and-data-rules)
- [Set up and run the scripts](#set-up-and-run-the-scripts)
- [The sample (your portfolio piece)](#the-sample-your-portfolio-piece)
- [What the kit cannot do](#what-the-kit-cannot-do)

## The offer

> I turn your approved questionnaire into a REDCap data dictionary or a KoboToolbox form, with skip logic, validation and calculations, plus a codebook, a test checklist and a cleaning script. I never touch participant data, and your approved wording stays word for word.

What the client gets:

| Deliverable | File | Made with |
|---|---|---|
| REDCap data dictionary | `.csv` (+ event mapping and repeating set-up for multi-visit studies) | the skill, checked by `validate_redcap.py` |
| XLSForm for KoboToolbox / ODK | `.xlsx` (+ XForm `.xml`) | `build_xlsform.py`, checked by `check_xlsform.py` |
| Wording check | `.txt` report | `check_wording.py` |
| Codebook | `.docx` and `.html` | `make_codebook.py` |
| Test checklist and delivery note | `.docx` | templates + `md_to_docx.py` |
| Cleaning script for their exports | `clean_export.py` + rules file | tested with `make_fake_export.py` |

## Who buys and where to find them

| Buyer | Where to find them | How to approach |
|---|---|---|
| Clinical research coordinators and study teams | ACRP (Association of Clinical Research Professionals) and SoCRA (Society of Clinical Research Associates): local chapters, conferences, online communities and LinkedIn groups | Join, answer REDCap questions, mention your service in your profile; message coordinators who post about form building |
| Community hospitals and smaller universities without a REDCap build team | Hospital research offices, clinical trials units, nursing and public health departments (their web pages list contacts) | Short email with your sample and an offer to convert one form free |
| NGOs and monitoring and evaluation teams | KoboToolbox community forum (community.kobotoolbox.org) and ODK forum (forum.getodk.org) | Help first. Read each forum's rules: most do not allow adverts in support threads. Put your offer in your profile and post only where job or marketplace posts are allowed |
| Researchers who already pay their university $60-150 an hour for this | University REDCap support pages show who offers build services and what they charge | Position yourself as faster and fixed-price, especially for teams without access to that service |

A first message you can adapt (keep it personal and short):

```text
Subject: REDCap / KoboToolbox forms for your study

Hi [name],
I build REDCap data dictionaries and KoboToolbox forms from approved questionnaires:
skip logic, validation, calculated fields and repeat visits, plus a codebook and a
test checklist. I only work on the blank form, never on participant data, and your
approved wording stays word for word.

Here is a fictional multi-visit study I built as a sample: [link]
If you have a questionnaire waiting to be built, I'm happy to convert one short form
free so you can judge the quality.

[Your name]
```

To get your first testimonial quickly, offer one free conversion of a short form (up to about 25 questions) to 20 carefully chosen contacts, as the playbook suggests.

## Price guide

Universities bill researchers **$60-150 an hour** for this work. Freelance fixed prices are typically **$200-500 for a simple form set** and **$800-2,000 for a multi-visit study** (estimates from the playbook research). Quote fixed prices; they are easier for research budgets.

| Job | Typical scope | Fixed price (estimate) |
|---|---|---|
| One form, one platform | Up to about 40 questions, simple skip logic, validation | $200-350 |
| Simple form set | 2-5 forms, calculations, codebook, test checklist | $350-500 |
| Same forms on a second platform | REDCap and KoboToolbox versions | add 40-60% |
| Multi-visit study | Events, repeating forms, calculations across visits, set-up notes | $800-2,000 |
| Cleaning script with study-specific rules | Tested on fake data, report and labelled export | $150-400 |
| Changes after sign-off | New questions, new wording versions | hourly, e.g. $40-75 as a beginner |

Take 30-50% upfront or use platform escrow. Include two rounds of changes within 14 days. Changes to approved wording are a new job, because the client may need ethics approval for them. Plan for about half a day for a simple form set and one to three days for a multi-visit study, including checks and documents.

## Step-by-step process

1. **Intake.** Send `templates/intake_form.docx`. Ask for the approved questionnaire (version and date), the platform, visits, repeating items, identifiers and any licensed scales. Never ask for data.
2. **Quote.** Fixed price, deliverables, two rounds of changes, timeline, deposit. Tell the client you use AI-assisted tools (with no participant data involved) and honour a "no AI" request.
3. **Set up a work folder** for the client, for example `work/<client>/input/` at the top of the repository (git ignores the `work/` folder), and put the questionnaire there. Keep client files out of public repositories.
4. **Build with the skill.** In your coding-assistant session, type `/redcap-xlsform work/<client>/input/questionnaire.docx both`, or just ask: "Build a REDCap data dictionary and an XLSForm from work/acme/input/questionnaire.docx". The skill (`.claude/skills/redcap-xlsform/`) plans the build, writes the files and runs every check below.
5. **Check and fix** until the validators pass: `validate_redcap.py`, `check_xlsform.py`, then `check_wording.py` against the approved document.
6. **Codebook, fake data and cleaning script:** `make_codebook.py`, `make_fake_export.py`, `clean_export.py --answer-key` (every deliberate mistake must be found).
7. **Client documents.** Fill in the test checklist and delivery note (see `samples/08_delivery/`), convert them with `md_to_docx.py`.
8. **Deliver** the files as a zip. Offer a 30-minute call while the client imports into a test project.
9. **Client tests** with made-up records and sends a list of changes. Fix, re-run the checks, re-deliver with a new version number.
10. **Sign-off, final invoice, testimonial.** Ask for a short testimonial on delivery day.

## Quality checklist (before you deliver)

- [ ] `validate_redcap.py`: 0 errors; every warning fixed or explained in the delivery note
- [ ] `check_xlsform.py`: 0 errors, with ODK Validate run (needs Java)
- [ ] `check_wording.py`: every text that is not word for word is fixed or listed for the client's approval
- [ ] Every skip instruction in the questionnaire has logic; every question has the right type and answer options in the original order
- [ ] Every calculation checked by hand with two sets of test values, written in the delivery note
- [ ] Identifiers flagged (names, dates of birth, contact details, record numbers); contact details on their own form if asked
- [ ] Codes consistent across forms and platforms (1 = Yes, 0 = No everywhere)
- [ ] Codebook made from the final files
- [ ] Cleaning script tested on fake data: the answer key is fully found
- [ ] Delivery note lists what the client must set up by hand (events, repeating forms, user rights)
- [ ] No participant data anywhere in your files; samples labelled as fictional

## Ethics and data rules

1. **Structure only, never participant data.** Do not ask for, accept or open real exports, screenshots with data, or logins to live projects. If a client sends data by mistake, do not open it, delete it and tell them. Test only with fake data from `make_fake_export.py`.
2. **Do not change ethics-approved wording.** Build from the approved version only. Adaptations for the screen (for example "mark the line" becoming a slider) are listed in the delivery note for the client to approve; their ethics committee may need to see them. `check_wording.py` proves the rest is word for word.
3. **Check each published scale's terms.** Some published questionnaires are free to use (the PHQ-9 and GAD-7, for example), but others (for example the EQ-5D, SF-36v2 and MMAS-8) need a licence that covers electronic use. Ask for the licence or written confirmation before building a licensed scale, copy every scale exactly, and never put licensed items in your samples.
4. **The client tests in their own REDCap or Kobo project.** You deliver files; they import them into a test project, test with made-up records, and move to production after sign-off. Regulated trials need the client's own validation process; your test checklist supports it but does not replace it.
5. **Protect client files.** Turn off model training in your AI tool's privacy settings before client work, keep each client's files in a private folder, and delete them when the job is done if the client asks.

## Set up and run the scripts

You need Python 3.10 or newer (`validate_redcap.py`, `clean_export.py` and `make_fake_export.py` also run on Python 3.9, since they use only the standard library). The other scripts need three packages; ODK Validate also needs Java (already in the cloud sandbox).

The easy way, from the repository root: `bash kits/setup.sh redcap-xlsform`. It makes the Python environment below (`bash kits/setup.sh --list` shows where). Or make it by hand:

```bash
python3 -m venv /tmp/redcap-venv
/tmp/redcap-venv/bin/pip install -r kits/redcap-xlsform/requirements.txt
cd kits/redcap-xlsform
/tmp/redcap-venv/bin/python scripts/selftest.py      # runs every script on the samples: 16 checks
```

In the commands below, `python` means `/tmp/redcap-venv/bin/python`, run from `kits/redcap-xlsform/`. Every script has `--help`, which shows the options and changes nothing. The examples write their results to an `out/` folder (ignored by git); the fake-data example rebuilds the sample files themselves.

| Script | What it does |
|---|---|
| `validate_redcap.py` | Checks a REDCap data dictionary: 18 headers in order, variable and form names, field types, choices, validation types and min/max, branching logic and calculations (syntax and references), checkbox and matrix rules, action tags, events, identifiers. Plain-English report; exit code 0 = no errors |
| `check_xlsform.py` | Checks an XLSForm with its own quick checks, pyxform and ODK Validate; explains errors in plain English; can save the XForm XML |
| `make_codebook.py` | Codebook (.docx and .html) from a dictionary and/or an XLSForm, with skip logic in plain English; `--logic-table` writes the skip-logic table for the test checklist |
| `clean_export.py` | Template cleaning script for a REDCap raw export: labels, value and range checks, required-but-blank (respecting skip logic), hidden-but-filled, calculation mismatches, custom rules. Writes labelled CSV, issues CSV and a report |
| `make_fake_export.py` | Fake REDCap export that follows the dictionary, with deliberate mistakes and an answer key |
| `check_wording.py` | Compares every label and option with the approved questionnaire (.docx or .txt) |
| `build_xlsform.py` | Builds an XLSForm .xlsx from CSV sheets, or splits an .xlsx into CSVs |
| `extract_text.py` | Gets the text out of a questionnaire (.docx, .doc, .odt, .rtf, .pdf) |
| `md_to_docx.py` | Turns the Markdown templates into Word documents |
| `selftest.py` | Runs everything on the samples and reports PASS/FAIL |
| `redcap_dictionary.py`, `redcap_logic.py`, `xlsform_reader.py` | Helper modules used by the scripts above (you do not run them; `--help` only says what they do) |

### Check a REDCap data dictionary

```bash
python scripts/validate_redcap.py samples/02_redcap/lakeside_data_dictionary.csv \
  --events samples/02_redcap/instrument_event_mapping.csv \
  --repeating samples/02_redcap/repeating_instruments.csv --report out/validation_report.txt
```

Add `--strict` to fail on warnings too. See what errors look like: `samples/07_checker_demo/broken_dictionary_report.txt`.

### Build and check an XLSForm

```bash
python scripts/build_xlsform.py samples/03_xlsform/source -o out/my_form.xlsx
python scripts/check_xlsform.py out/my_form.xlsx --xml out/my_form.xml --report out/xlsform_check.txt
```

To fix a client's existing form, split it into CSVs first. Keep the client's files in `work/<client>/` at the top of the repository (git ignores that folder), not in the kit folder: `python scripts/build_xlsform.py --split ../../work/<client>/input/their_form.xlsx -o ../../work/<client>/xlsform/source`.

### Check the wording against the approved questionnaire

```bash
python scripts/check_wording.py --source samples/01_client_input/lakeside_questionnaire_v1.2.docx \
  --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
  --xlsform samples/03_xlsform/lakeside_health_check.xlsx --report out/wording_check.txt
```

### Make a codebook

```bash
python scripts/make_codebook.py --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
  --events samples/02_redcap/instrument_event_mapping.csv \
  --repeating samples/02_redcap/repeating_instruments.csv \
  --title "Lakeside Community Health Check (fictional sample)" --out out/lakeside_codebook --logic-table out/skip_logic_tests.md
python scripts/make_codebook.py --xlsform samples/03_xlsform/lakeside_health_check.xlsx --out out/lakeside_kobo_codebook
```

Options: `--page letter` for US paper, `--formats html` for the web page only.

### Make fake data and test the cleaning script

```bash
python scripts/make_fake_export.py --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
  --events samples/02_redcap/instrument_event_mapping.csv \
  --repeating samples/02_redcap/repeating_instruments.csv --event-days samples/02_redcap/events.csv \
  --event-logic "visit_*=[screening_arm_1][fu_agree] = '1'" \
  --repeat-logic "health_event=[fu_health_event] = '1'" \
  --records 24 --errors 8 --seed 7 --today 2026-10-07 --start 2026-02-01 \
  --set "2:screening_arm_1:scr_dbp=148" --out samples/05_test_data/fake_export.csv

python scripts/clean_export.py --dictionary samples/02_redcap/lakeside_data_dictionary.csv \
  --export samples/05_test_data/fake_export.csv --events samples/02_redcap/instrument_event_mapping.csv \
  --rules samples/05_test_data/cleaning_rules.csv --today 2026-10-07 --outdir samples/06_cleaning_output \
  --answer-key samples/05_test_data/fake_export_answer_key.csv
```

The last line of the output must read "Answer key: 9 of 9 deliberate mistakes found." Rules files have two columns, `rule` and `logic`; the logic uses REDCap syntax and a row is flagged when it is true. For clients: `--drop-identifiers` leaves identifier columns out of the labelled file.

### Turn templates into Word documents

```bash
python scripts/md_to_docx.py templates/intake_form.md templates/client_test_checklist.md templates/delivery_note.md --outdir out
```

Without `--outdir`, each Word file is written next to its Markdown file, so the command above would overwrite the Word templates in `templates/`. For a client, fill in copies in `work/<client>/delivery/` and use `--outdir ../../work/<client>/delivery`.

## The sample (your portfolio piece)

A fictional "Lakeside Community Health Check": a 15-question screening questionnaire, a contact sheet, a follow-up form used at 3 visits (2 weeks, 3 months, 6 months) and a repeating health event form. All questions were written for this kit; no published or licensed scale is used.

| Folder | What it shows |
|---|---|
| `samples/01_client_input/` | The "client" questionnaire as a study team would send it (.docx) |
| `samples/02_redcap/` | Data dictionary (61 fields, 4 forms, 4 events, calculations across visits, matrices, a repeating form), event mapping, repeating set-up, event list, validation report |
| `samples/03_xlsform/` | The same study as one KoboToolbox/ODK form (visit chooser, groups, a repeat), its CSV source, XForm XML and check report |
| `samples/04_codebook/` | Codebooks for both versions (.docx and .html) |
| `samples/05_test_data/` | Fake export (24 fake records) with an answer key of 9 deliberate mistakes, and the study's cleaning rules |
| `samples/06_cleaning_output/` | Labelled export, issues list and cleaning report (all 9 mistakes found) |
| `samples/07_checker_demo/` | A deliberately broken dictionary and XLSForm, with the reports that catch the mistakes |
| `samples/08_delivery/` | The filled-in delivery note and test checklist (.md and .docx) and the wording check |

How to use it with prospects: share the delivery note and the HTML codebook first (they show the finished package), and the broken-file reports to show your checks. Always say the study is fictional. You can rebuild any sample output with the commands above; the self-test confirms the samples are still consistent.

**Put your own name on the sample.** Open `samples/08_delivery/delivery_note.md` and replace `[your name]` in the "Prepared by" row with your name or business name. Then rebuild its Word file (from `kits/redcap-xlsform/`):

```bash
python scripts/md_to_docx.py samples/08_delivery/delivery_note.md
```

This writes `samples/08_delivery/delivery_note.docx` next to the Markdown file. Keep the "fictional sample" line at the top.

## What the kit cannot do

- It cannot log into REDCap, KoboToolbox or ODK. The client imports and tests; the checklist tells them how.
- The REDCap check covers the common upload and logic errors, but servers differ (version, enabled validation types, external modules). A clean report is not a substitute for testing.
- The data dictionary cannot create events, arms, repeating set-up, surveys, user rights or missing-data codes; the delivery note lists these as manual steps.
- The cleaning script evaluates REDCap logic itself. A few smart variables and instance references cannot be evaluated; the report lists any field it could not check.
- KoboToolbox uses its own copy of pyxform, which can be a version ahead or behind; preview the form in Kobo before deploying.
