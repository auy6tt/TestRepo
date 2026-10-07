# Test checklist: Lakeside Community Health Check forms

*Fictional sample, made to show the service.*

**Study:** Lakeside Community Health Check  **Files tested:** lakeside_data_dictionary.csv and lakeside_health_check.xlsx, delivery 1.0  **Tested by:** ____________  **Date:** ____________

Please test in a **test (development) project**, never in the live one, and only with **made-up records** (for example "TEST 1", "TEST 2"). Tick each item. For anything that looks wrong, note the record ID, form, question and what you expected, and send me the list. Two rounds of fixes are included.

## A. Set up the test project

- [ ] REDCap: create the project, turn on longitudinal data collection and create the 4 events (delivery note, section 2)
- [ ] Upload lakeside_data_dictionary.csv and click "Commit changes"
- [ ] Designate the forms to the events and make health_event repeat in Visits 1 to 3
- [ ] KoboToolbox: upload lakeside_health_check.xlsx, preview it, deploy it to a test project

## B. Every form

- [ ] All 15 screening questions, the contact sheet, the 9 follow-up questions and the 5 health event questions are there, in the same order as version 1.2
- [ ] The wording is exactly as approved (texts I added are listed in the delivery note, section 5)
- [ ] Every answer option is there, in the right order
- [ ] Section headings and help text are in the right places
- [ ] Each form saves without errors

## C. Skip logic (questions that appear only sometimes)

Test each rule both ways: give the answer that should show the question, then one that should hide it.

| Form or section | Question | Shown when | Appears when it should | Stays hidden when it should |
|---|---|---|---|---|
| Screening | consent_stop | consent is "No" (0) | [ ] | [ ] |
| Screening | age_stop | age is not blank AND age < 18 | [ ] | [ ] |
| Screening | bp_med | conditions: "High blood pressure" is ticked | [ ] | [ ] |
| Screening | cig_per_day | smoke_status is "Yes, every day" (1) OR "Yes, some days" (2) | [ ] | [ ] |
| Screening | bp_high_msg | bp_high is 1 | [ ] | [ ] |
| Screening | fu_agree | bp_high is 1 | [ ] | [ ] |
| Contact details | contact_phone | fu_agree is "Yes" (1) | [ ] | [ ] |
| Contact details | contact_time | fu_agree is "Yes" (1) | [ ] | [ ] |
| Contact details | contact_sms | fu_agree is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | fu_missed_reason | fu_attended is "No" (0) | [ ] | [ ] |
| Follow-up visit | fu_missed_other | fu_missed_reason is "Other" (5) | [ ] | [ ] |
| Follow-up visit | fu_sbp, fu_dbp, fu_weight | fu_attended is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | fu_bp_med | fu_attended is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | fu_med_days | fu_bp_med is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | symptom grid (fu_headache to fu_ankles) | fu_attended is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | fu_health_event | fu_attended is "Yes" (1) | [ ] | [ ] |
| Follow-up visit | fu_he_msg | fu_health_event is "Yes" (1) | [ ] | [ ] |
| Health event | he_type_other | he_type is "Other" (4) | [ ] | [ ] |
| Health event | he_nights | he_type is "Overnight hospital stay" (1) | [ ] | [ ] |

KoboToolbox only: the screening section appears only when the visit is "Screening", the follow-up section only for visits 1 to 3, sections A to D only when consent is "Yes", and the health event repeat only when F9 is "Yes".

## D. Checks on answers

- [ ] Dates before 2026 or in the future are refused (date of birth: before 1900 or in the future)
- [ ] Household 0 or 21, active days 8, height 99.9 or 230.1, weight 29.9 or 250.1, blood pressure outside 70-250 / 40-150: each shows a warning
- [ ] Height and weight need one decimal place (165.0)
- [ ] Text typed into a number box is refused
- [ ] Leaving a required question blank shows a warning when you save
- [ ] Question 5: "None of these" cannot be ticked with a condition
- [ ] KoboToolbox: participant ID must look like LH-0042; diastolic must be lower than systolic

## E. Calculations

- [ ] The test values in the delivery note (section 4) give the expected age, BMI, high-reading flag, days since screening and change in systolic pressure
- [ ] Calculated fields update when you change an answer and save again

## F. Visits and repeating forms

- [ ] Screening shows the screening and contact details forms; each visit shows the follow-up and health event forms
- [ ] Health event can be added more than once at a visit
- [ ] Days since screening and change since screening work at each visit

## G. Identifiers and exports

- [ ] dob and contact_phone are marked as identifiers (left out of de-identified exports)
- [ ] Export the test records (CSV, raw data) and check the column names match the codebook
- [ ] Optional: run the cleaning script on that test export and read the report

## H. Sign-off

| Result | Tick |
|---|---|
| Approved: ready to move to the live project | [ ] |
| Changes needed (list attached) | [ ] |

Signed: ______________________  Role: ______________________  Date: ____________

> After real data collection starts, changes need more care (in REDCap they go through draft mode and can affect data already collected). Please finish testing before going live.
