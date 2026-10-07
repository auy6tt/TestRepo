# Delivery note: Lakeside Community Health Check forms

*Fictional sample delivery, made to show the service. There is no real study, client or data.*

| | |
|---|---|
| Client | Lakeside Community Health Check study team (fictional) |
| Prepared by | [your name] |
| Date | 7 October 2026 |
| Questionnaire version used | Version 1.2, 14 August 2026 |
| Delivery version | 1.0 |

## 1. What is included

| File | What it is | What to do with it |
|---|---|---|
| lakeside_data_dictionary.csv | REDCap data dictionary: 61 fields in 4 forms | Upload in Project Setup > Data Dictionary (test project first) |
| instrument_event_mapping.csv | Which forms belong to which visit | Use it when you designate forms to events |
| repeating_instruments.csv | Which form repeats at which visit | Use it when you set up repeating forms |
| events.csv | The 4 events with their day offsets | Use it when you create the events |
| lakeside_health_check.xlsx | XLSForm for KoboToolbox or ODK (one form for all visits) | Upload as a new project, preview, test |
| lakeside_health_check.xml | The same form as XForm XML | Only needed for ODK tools that ask for XML |
| lakeside_codebook.docx / .html | Codebook for the REDCap version | Keep with the study documents; share with your statistician |
| lakeside_kobo_codebook.docx / .html | Codebook for the KoboToolbox version | As above |
| test_checklist.docx | What to test before going live, with every skip rule listed | Work through it in the test project |
| clean_export.py, redcap_dictionary.py, redcap_logic.py, cleaning_rules.csv | Cleaning script for your REDCap exports | Keep the files together; instructions in section 7 |
| validation_report.txt, xlsform_check_report.txt, wording_check.txt | Results of my checks | For your records |

## 2. How to set it up in REDCap

1. Create a new project (or a development copy).
2. In Project Setup, turn on "Use longitudinal data collection with defined events".
3. Define the events in arm 1: Screening (day 0), Visit 1 (day 14, window 7 days either side), Visit 2 (day 90, 14 days either side), Visit 3 (day 180, 14 days either side). Check that REDCap names them screening_arm_1, visit_1_arm_1, visit_2_arm_1 and visit_3_arm_1: two calculations use these names.
4. Upload the data dictionary: Project Setup > Data Dictionary > choose lakeside_data_dictionary.csv > Upload > Commit changes.
5. Designate the forms: Screening gets screening and contact_details; each visit gets follow_up_visit and health_event.
6. Project Setup > Enable optional modules > Repeating instruments and events: make health_event repeat in Visit 1, Visit 2 and Visit 3. Custom label: `[he_date]: [he_type:label]`.
7. User rights: give "No access" to the contact_details form to anyone who does not phone participants, and give analysts de-identified export rights only.
8. Work through the test checklist with made-up records.

## 3. How to set it up in KoboToolbox or ODK

1. KoboToolbox: New project > Upload an XLSForm > lakeside_health_check.xlsx > Preview > Deploy (test project first). ODK Central: create a form from the .xlsx and test the draft.
2. Staff choose the visit first; the form then shows the screening questions or the follow-up questions. Health events are a repeat group: one entry per event.
3. Participant IDs are typed in the format LH-0000 (for example LH-0042), so screening and follow-up submissions can be matched.
4. Work through the test checklist with made-up records.

## 4. What I checked

| Check | Result |
|---|---|
| REDCap dictionary check (headers, names, choices, validation, logic, events, identifiers) | PASSED: 0 errors, 0 warnings, 1 note (free-text fields carry a "no names" reminder) |
| XLSForm check (pyxform 4.5 and ODK Validate) | PASSED: 0 errors, 0 warnings |
| Wording check against questionnaire version 1.2 | 103 of 127 texts word for word; the 24 others are listed in section 5 |
| Cleaning script tested on fake data with 9 deliberate mistakes | All 9 found |

Calculations to test with made-up values:

| Inputs | Expected result |
|---|---|
| Date of birth 15/03/1970, screening 10/02/2026 | age = 55 |
| Date of birth 11/02/2008, screening 10/02/2026 | age = 17, and the under-18 STOP message appears |
| Height 170.0 cm, weight 72.4 kg | bmi = 25.1 |
| Height 182.5 cm, weight 95.0 kg | bmi = 28.5 |
| Blood pressure 150/85, then 128/92, then 139/89 | bp_high = 1, then 1, then 0 |
| Screening 10/02/2026, Visit 1 on 24/02/2026 | fu_days = 14 |
| Systolic 150 at screening, 138 at Visit 1 | fu_bp_change = -12 |

## 5. Decisions and wording to confirm

All question texts and answer options are word for word from version 1.2. These texts are not, and need your approval:

| Where | Text | Why |
|---|---|---|
| age, bmi, bp_high, fu_days, fu_bp_change | Labels such as "Age at screening (years)" and "Days since screening" | Labels for the calculations you asked for; staff see them, participants do not |
| bmi, age, fu_days, fu_bp_change, bp_high | Field notes such as "Calculated from height and weight" | Explain the calculations to staff |
| energy | "Move the slider to your answer (0 to 100)." | The paper says "mark the line"; a screen needs a slider. Please confirm this adaptation |
| active_days | "0 to 7 days" | Hint for the allowed range |
| fu_date, fu_bp_med | Section headings "Visit details" and "Medicines and symptoms" | Split the follow-up form into short sections |
| fu_missed_reason | "Main reason the visit did not take place" | The paper says "If no: main reason ..."; the "If no" is handled by skip logic |
| record_id | "Assigned by REDCap" | Capital letter only |
| XLSForm only | "Which visit is this?", visit names, "Screening visit", the form introduction and the LH-0000 hint | Needed because one Kobo form covers all visits |

Other decisions:

- Codes are the same in REDCap and KoboToolbox: 1 = Yes, 0 = No, 98 = Not sure, 99 = Prefer not to say.
- Dates are shown day/month/year in REDCap; every export stores them as year-month-day.
- Question 5: "None of these" cannot be ticked together with a condition.
- Question 13 and F8 are shown as grids (one row per symptom).
- High blood pressure reading = systolic 140 or more, or diastolic 90 or more, as in your notes.
- Contact details are on their own form (REDCap) or their own section (KoboToolbox) and are flagged as identifiers, with date of birth.
- The KoboToolbox version cannot show "days since screening" or "change since screening", because a Kobo form does not see earlier submissions. Work them out at analysis from the matched submissions.

Questions for you:

- REDCap record IDs: keep REDCap's automatic numbers, or use the LH-0000 format as in KoboToolbox?
- Visit windows: are 7 days either side for Visit 1 and 14 days for Visits 2 and 3 right? (The cleaning rules check the Visit 1 window.)
- Who on the team should see the contact details form?

## 6. Ethics and data protection

- I worked only on the structure of the forms. I did not receive or see any participant data.
- Question wording follows version 1.2. Every difference is listed in section 5 for your approval.
- Licensed scales: none. All questions were written by the study team.
- Identifiers flagged: dob (date of birth) and contact_phone.

## 7. Running the cleaning script (optional)

You need Python 3.9 or newer; no extra packages. Keep clean_export.py, redcap_dictionary.py and redcap_logic.py in one folder. Export your data from REDCap as "CSV / Microsoft Excel (raw data)", then run:

```text
python clean_export.py --dictionary lakeside_data_dictionary.csv --export your_export.csv --events instrument_event_mapping.csv --rules cleaning_rules.csv --drop-identifiers
```

It writes a labelled copy of the data (without identifier columns), a list of issues and a short report next to your export. It never changes your REDCap data. The rules file checks that diastolic is lower than systolic, the Visit 1 window, implausible BMI values and health events dated after the visit; add your own in the same format.

## 8. Changes and support

Two rounds of changes within 14 days are included. After that, changes are billed by the hour. Changes to approved wording need your written confirmation (and possibly your ethics committee's).

Approved by: ______________________  Date: ____________
