# Delivery note: [study name] forms

| | |
|---|---|
| Client | [name, organisation] |
| Prepared by | [your name] |
| Date | [date] |
| Questionnaire version used | [e.g. version 1.2, 14 August 2026] |
| Delivery version | [1.0] |

## 1. What is included

| File | What it is | What to do with it |
|---|---|---|
| [name]_data_dictionary.csv | REDCap data dictionary | Upload in Project Setup > Data Dictionary (test project first) |
| instrument_event_mapping.csv | Which forms belong to which visit (longitudinal only) | Use it when you designate forms to events |
| [name].xlsx | XLSForm for KoboToolbox / ODK | Upload as a new project, preview, test |
| [name]_codebook.docx / .html | Codebook: every variable, code and rule | Keep with the study documents; share with your statistician |
| test_checklist.docx | What to test before going live | Work through it in the test project |
| clean_export.py and cleaning_rules.csv | Cleaning script for your exports | Run it on your own computer (instructions below) |
| validation reports (.txt) | Results of my automatic checks | For your records |

## 2. How to set it up in REDCap

1. Create a new project (or use a development copy).
2. [Longitudinal only] In Project Setup, turn on "Use longitudinal data collection". Create these events: [list with day offsets].
3. Upload the data dictionary: Project Setup > Data Dictionary > choose the CSV > Upload > Commit changes.
4. [Longitudinal only] Designate the forms for each event as in instrument_event_mapping.csv.
5. [Repeating only] Project Setup > Enable optional modules > Repeating instruments and events: tick [forms] in [events].
6. Work through the test checklist with made-up records.

## 3. How to set it up in KoboToolbox or ODK

1. KoboToolbox: New project > Upload an XLSForm > choose [name].xlsx > Preview > Deploy. ODK Central: new form > upload > test with the draft.
2. Work through the test checklist with made-up records.

## 4. What I checked

| Check | Result |
|---|---|
| REDCap dictionary check (headers, names, choices, validation, logic, identifiers) | [PASSED: 0 errors, 0 warnings] |
| XLSForm check (pyxform and ODK Validate) | [PASSED] |
| Wording check against the approved questionnaire | [x of y texts word for word; the rest listed in section 5] |
| Cleaning script tested on fake data with deliberate mistakes | [all found] |

## 5. Decisions and wording to confirm

Texts that are not word for word from the approved questionnaire (from the wording check):

| Where | Text | Why |
|---|---|---|
| [variable] | [text] | [e.g. label for a calculated field; instruction adapted for the screen] |

Other decisions:

- [e.g. "Prefer not to say" is coded 99 everywhere]
- [e.g. dates are shown as day-month-year; REDCap stores them as year-month-day]
- [differences between the REDCap and KoboToolbox versions, if both]

Questions for you:

- [anything still open]

## 6. Ethics and data protection

- I worked only on the structure of the forms. I did not receive or see any participant data.
- Question wording follows the approved version listed above. Every difference is in section 5 for your approval.
- Licensed scales: [none in this questionnaire / you confirmed you hold the licence for: ...].
- Fields that identify a person are flagged as identifiers: [list].

## 7. Running the cleaning script (optional)

You need Python 3.9 or newer; no extra packages. Export your data from REDCap as "CSV / Microsoft Excel (raw data)", then run:

```text
python clean_export.py --dictionary [name]_data_dictionary.csv --export your_export.csv --events instrument_event_mapping.csv --rules cleaning_rules.csv
```

It writes a labelled copy of the data, a list of issues and a short report next to your export. It never changes your REDCap data.

## 8. Changes and support

[Two rounds of changes within 14 days are included.] After that, changes are [price]. Changes to approved wording need your written confirmation (and possibly your ethics committee's).

Approved by: ______________________  Date: ____________
