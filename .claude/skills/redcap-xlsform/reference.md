# Reference: REDCap data dictionaries and XLSForms

Quick rules for building forms that import cleanly. Check the client's platform version when in doubt.

## REDCap data dictionary: the 18 columns (in this order)

| Col | Header | Notes |
|---|---|---|
| A | Variable / Field Name | lowercase letters, numbers, `_`; starts with a letter; unique; 26 characters or fewer; never starts with `redcap_` |
| B | Form Name | instrument name, lowercase with `_`; all rows of a form together |
| C | Section Header | heading shown above the field; on the first row of a matrix it is the matrix question |
| D | Field Type | text, notes, dropdown, radio, checkbox, yesno, truefalse, calc, slider, descriptive, file (sql needs an admin) |
| E | Field Label | the exact question text; simple HTML allowed (`<b>`, `<i>`, `<br>`) |
| F | Choices, Calculations, OR Slider Labels | `1, Yes \| 0, No`; or the calculation; or `left \| middle \| right` slider labels |
| G | Field Note | small help text under the field (units, format, "no names here") |
| H | Text Validation Type OR Show Slider Number | e.g. `integer`, `number`, `number_1dp`, `date_dmy`, `email`; `number` on a slider shows its value |
| I, J | Text Validation Min / Max | numbers, or dates written `YYYY-MM-DD`, or `today` / `now` |
| K | Identifier? | `y` for anything that identifies a person |
| L | Branching Logic (Show field only if...) | see below |
| M | Required Field? | `y` or empty |
| N | Custom Alignment | `LV`, `LH`, `RV`, `RH` or empty |
| O | Question Number (surveys only) | e.g. `5`, `13a`; keeps traceability to the paper form |
| P | Matrix Group Name | same name on consecutive radio (or checkbox) rows with identical choices |
| Q | Matrix Ranking? | `y` only for radio matrices |
| R | Field Annotation | action tags and notes, e.g. `@NONEOFTHEABOVE='6'` |

## Choosing field types

| Questionnaire item | REDCap |
|---|---|
| Short answer, number, date | `text` + validation (`integer`, `number`, `number_1dp`, `date_dmy`/`date_mdy`/`date_ymd`, `datetime_dmy`, `time`, `email`) |
| Long free text | `notes` (add a field note: "no names or contact details") |
| Tick one (few options) | `radio` (add `LH` alignment for short horizontal lists) |
| Tick one (long list) | `dropdown` |
| Tick all that apply | `checkbox`; exclusive "None of these" via `@NONEOFTHEABOVE='code'` |
| Yes / No | `yesno` (stored 1 = Yes, 0 = No; no choices needed) |
| Grid of items with the same answers | consecutive `radio` rows with one Matrix Group Name |
| Visual analogue line | `slider` (0-100; labels in column F; `number` in H to show the value) |
| Instructions, stop messages | `descriptive` (stores nothing; can have branching logic) |
| Score, BMI, age | `calc` with the formula in column F |
| Text that is calculated | `text` with `@CALCTEXT(...)` in the annotation |

Validation types REDCap ships with include: `integer`, `number`, `number_1dp` ... `number_4dp`,
`number_comma_decimal`, `date_dmy`, `date_mdy`, `date_ymd`, `datetime_dmy`, `datetime_mdy`,
`datetime_ymd`, `datetime_seconds_*`, `time`, `time_hh_mm_ss`, `time_mm_ss`, `email`, `phone`
(North American format), `zipcode`, `alpha_only`. Some are switched off on some servers.
`number_1dp` needs exactly one decimal place (165.0), so say so in the field note.

## Branching logic

```text
[sex] = '2'                                  radio, dropdown, yesno: compare with the code
[sex] <> '2'                                 not equal (also !=)
[conditions(1)] = '1'                        checkbox option 1 is ticked (use '0' for not ticked)
[age] >= 18 and [age] <= 65                  numbers
[smoke_status] = '1' or [smoke_status] = '2'
([a] = '1' or [b] = '1') and [c] = '1'       brackets group conditions
[weight] <> ''                               answered (not blank)
[age] <> '' and [age] < 18                   blank values fail < and >; check for blank first
datediff([dob], [visit_date], "y") < 18      dates: use datediff, never subtract dates
[screening_arm_1][fu_agree] = '1'            a field from another event (longitudinal)
[event-name] = 'visit_1_arm_1'               smart variable: current event
```

Use straight quotes only (never curly quotes pasted from Word), `and`/`or` in words, single `=`.
A field should only depend on questions above it.

## Calculations

```text
round([weight_kg] / (([height_cm] / 100) ^ 2), 1)                 BMI, 1 decimal
rounddown(datediff([dob], [scr_date], "y"), 0)                    age in whole years
datediff([screening_arm_1][scr_date], [fu_date], "d")             days between events
sum([q1], [q2], [q3])                                             blanks are ignored
if([q1] = '' or [q2] = '', '', [q1] + [q2])                       blank unless all answered
if([scr_sbp] >= 140 or [scr_dbp] >= 90, 1, 0)                     yes/no flag (document the codes)
```

Other functions: `roundup`, `rounddown`, `min`, `max`, `mean`, `median`, `stdev`, `abs`, `sqrt`,
`if`, `datediff` (units `y`, `M`, `d`, `h`, `m`, `s`), `isnumber`, `isblankormissingcode`.
Put the codes of a calculated flag in its field note. Scoring rules for published scales come
from the scale's manual (and need the client's licence).

## Useful action tags (column R)

`@NONEOFTHEABOVE='99'`, `@HIDECHOICE='3'`, `@READONLY`, `@HIDDEN`, `@HIDDEN-SURVEY`,
`@DEFAULT='1'`, `@TODAY`, `@NOW`, `@CHARLIMIT=500`, `@WORDLIMIT=100`, `@CALCTEXT(...)`,
`@CALCDATE([date], 14, 'd')`, `@MAXCHECKED=2`, `@PLACEHOLDER='...'`. Do not make a field both
`@HIDDEN` and required.

## Longitudinal and repeating set-up

- Events are created in Project Setup (not in the dictionary). Unique event names are built from
  the event name and arm: "Visit 1" in arm 1 becomes `visit_1_arm_1`. Ask the client to confirm
  them after creating the events, because logic uses them.
- `instrument_event_mapping.csv`: columns `arm_num,unique_event_name,form`, one row per form per event.
- `repeating_instruments.csv` (API format): `event_name,form_name,custom_form_label`. The client
  ticks the same in Project Setup > Repeating instruments and events.
- Things the dictionary cannot set (list them in the delivery note): events and arms, form
  designation, repeating set-up, surveys and survey settings, user rights, data access groups,
  missing data codes, alerts, randomization, form display logic.

## REDCap export facts (for the cleaning script)

- Raw export: codes, not labels. Dates are `YYYY-MM-DD` whatever the display format.
- Checkboxes become one column per option: `conditions___1` (1 = ticked, 0 = not).
- Each form adds `<form>_complete`: 0 Incomplete, 1 Unverified, 2 Complete.
- Longitudinal exports add `redcap_event_name`; repeating forms add `redcap_repeat_instrument`
  and `redcap_repeat_instance` and get their own rows.

## REDCap to XLSForm equivalents

| REDCap | XLSForm (survey sheet) |
|---|---|
| text + integer / number | `integer` / `decimal`, with `constraint` `. >= 0 and . <= 7` and a `constraint_message` |
| text + date_dmy | `date` (the display format follows the phone or browser) |
| notes | `text` with appearance `multiline` |
| radio | `select_one listname` |
| dropdown | `select_one listname` with appearance `minimal` |
| checkbox | `select_multiple listname`; "None of these": constraint `not(selected(., '6') and count-selected(.) > 1)` |
| yesno | `select_one yesno` (choices `1 Yes`, `0 No` to keep REDCap codes) |
| calc | `calculate` (shows nothing; add a `note` with `${bmi}` to display it) |
| descriptive | `note` |
| slider | `range` with parameters `start=0 end=100 step=1` |
| section header | `begin_group` / `end_group` (appearance `field-list` for one screen) |
| matrix | a group with appearance `table-list` |
| field note | `hint` |
| required y | `required` = `yes` (optionally `required_message`) |
| branching `[x] = '1'` | `relevant` = `${x} = '1'` |
| `[chk(2)] = '1'` | `selected(${chk}, '2')` |
| `<>` | `!=` |
| `datediff([dob], [d], "y")` | `int((decimal-date-time(${d}) - decimal-date-time(${dob})) div 365.2425)` |
| `round(x, 1)` | `round(x, 1)`; division is `div`, not `/` |
| repeating instrument | `begin_repeat` / `end_repeat` |
| events (visits) | a visit question with groups shown by `relevant`, separate forms, or ODK Entities |
| identifier flag | no equivalent: list identifiers in the codebook and delivery note |

XLSForm rules: names unique across the form; `select_multiple` choice names without spaces;
`${name}` references; `.` means the current answer; lowercase `and`/`or`; straight quotes; a
`version` in settings that changes with every update; one `label::Language (code)` column per
language and `default_language` matching one of them. KoboToolbox exports add group names to
column names unless the export option is changed.
