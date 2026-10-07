# Test checklist for your new forms

**Study:** [study name]  **Files tested:** [file names and delivery version]  **Tested by:** [name]  **Date:** [date]

Please test in a **test (development) project**, never in the live one, and only with **made-up records** (for example "TEST 1", "TEST 2"). Tick each item. For anything that looks wrong, note the record ID, form, question and what you expected, and send me the list. Two rounds of fixes are included.

## A. Set up the test project

- [ ] REDCap: create a new project, then Project Setup > Data Dictionary > upload the CSV, read the summary page and click "Commit changes"
- [ ] Longitudinal studies: turn on "Use longitudinal data collection", create the events and tick the forms for each event as listed in the delivery note
- [ ] Repeating forms: Project Setup > "Repeating instruments and events" > tick the forms listed in the delivery note
- [ ] KoboToolbox: New project > Upload an XLSForm, then Preview, then Deploy (to a test project)
- [ ] ODK Central: create a test project, upload the form as a draft and test with the draft QR code

## B. Every form

- [ ] Every question from the approved questionnaire is there, in the same order
- [ ] The wording is exactly as approved (the delivery note lists every text I added or adapted)
- [ ] Every answer option is there, in the right order
- [ ] Section headings and help text are in the right places
- [ ] The form saves without errors

## C. Skip logic (questions that appear only sometimes)

The codebook lists every rule in plain English under "Shown when". Test each rule both ways.

| Question | Shown when | Appears when it should | Stays hidden when it should |
|---|---|---|---|
| [variable] | [rule from the codebook] | [ ] | [ ] |
| [variable] | [rule from the codebook] | [ ] | [ ] |
| [variable] | [rule from the codebook] | [ ] | [ ] |

## D. Checks on answers

- [ ] A number below the minimum, or above the maximum, shows a warning
- [ ] Text typed into a number box is refused
- [ ] Impossible dates (for example 31/02) and dates outside the allowed range show a warning
- [ ] Leaving a required question blank shows a warning when you save (REDCap still lets you save; that is normal)
- [ ] "None of these" cannot be ticked together with another answer, where the questionnaire says so

## E. Calculations

- [ ] Each calculated field gives the expected result for the test values in the delivery note
- [ ] Calculated fields update when you change an answer and save again

## F. Visits and repeating forms (if used)

- [ ] Each visit shows the right forms
- [ ] Repeating forms can be added more than once at each visit
- [ ] Calculations that use another visit (for example "days since screening") work

## G. Identifiers and exports

- [ ] Questions that identify a person are marked as identifiers (REDCap removes them from de-identified exports)
- [ ] Export the test records (CSV, raw data) and check the column names match the codebook
- [ ] Optional: run the cleaning script on that test export and look at the report

## H. Sign-off

| Result | Tick |
|---|---|
| Approved: ready to move to the live project | [ ] |
| Changes needed (list attached) | [ ] |

Signed: ______________________  Role: ______________________  Date: ____________

> After real data collection starts, changes need more care (in REDCap they go through draft mode and can affect data already collected). Please finish testing before going live.
