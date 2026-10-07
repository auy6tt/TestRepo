# Drafting guide for digest items

Read this before turning `changes.json` into `items.yaml`. A full worked example is `kits/weekly-digest/samples/battery-storage-ohio-week41/items.reviewed.yaml`; the field reference is `kits/weekly-digest/templates/items.example.yaml`.

## Inputs

- `changes.json` (the same content as `changes.md`): changed sources with added and removed lines, new links, new records and `documents` fetched from new links (an excerpt plus `text_file`, the full text).
- `sources.yaml`: `digest.scope` and `digest.audience` say what is in and out.
- Last week's `items.yaml`: avoid repeating items, keep the same sections, and follow up on items that had a pending date.

## For each changed source

1. Read the diff, the new records and the fetched documents. Open `text_file` when the excerpt stops before the part you need.
2. Decide:
   - In scope and new: draft an item.
   - Out of scope, already reported, or noise (a changed date stamp, formatting, a page counter): add it to `skipped_changes` with a short reason.
3. One item per event or decision. If two sources describe the same event, write one item and cite the primary document (the agenda or notice, not the listing page).

## Writing an item

- **title:** what happened, plainly, in under 100 characters. Name the place and the key number. No hype ("major", "huge", "shocking").
- **short_title:** under 60 characters, for the "Coming up" list and the calendar.
- **summary:** one to three short sentences in your own words: who, what, where, how big, what stage. Use the exact status words in the source (proposed, adopted, continued, filed, recommended). Quote at most a short phrase, in quotation marks.
- **why_it_matters:** facts about the effect and the next step: dates, thresholds, what happens next. No advice ("you should..."), no predictions written as facts.
- **source_url:** the official document itself (the PDF or the case page) when you have it, otherwise the official page that lists it. For a "current agenda" file that is replaced each month, put the meeting date in `source_name`.
- **source_ref:** page, item or section. Changed PDF lines in `changes.json` start with `[p. N]`.
- **date:** the date on the document, or when it was posted or filed.
- **deadline:** the next date that matters (hearing, vote, comment deadline, bid due), with the time if the source gives one: `YYYY-MM-DDTHH:MM` in the issue's time zone. Put other dates in `more_dates`. Never guess a time.
- **details:** two to four key facts: case or bid number, size, amount, applicant company.
- **category:** reuse last week's section names.
- **status:** `needs_review`. Never `approved`.
- **review_notes:** start with `CHECK:` and list what the reviewer must confirm: every date, time, number and status word, and anything you inferred or found hard to read (for example a scanned PDF with no text).

## Never

- Invent or "round" facts, dates or numbers that are not in the source.
- Include names, home addresses, phone numbers or emails of private individuals: residents, homeowners, public commenters, landowners who are people, sole traders. Companies and public bodies are fine; name public officials only in their official role and only when it matters.
- Copy text from paid services, newsletters or law-firm alerts.
- Tell readers what to do, or whether a law applies to them.

## Issue fields

Copy the `issue:` block from last week and update `edition`, `number`, `date`, `coverage`, `intro` and `sources_checked` (changed + unchanged + first-check sources from `changes.json`, plus any you checked by hand; or pass `--changes` to the build). Write the `intro` last: two or three sentences, most important item first, and nothing that is not in the items.

## Notes by offer

- **Packaging EPR:** describe rules and deadlines state by state and link to the agency page. Never say whether a brand is covered or owes fees.
- **Public bids:** copy bid numbers, due dates and times, and site-visit dates exactly. Put past prices from bid tabulations in `details` (for example "Last similar award: $612,400 (2024, Bid 24-071)"). Use business names only.
- **Meeting watch:** cite page numbers. Keep "on the agenda" apart from "decided". Leave residents' names out of public comment summaries.
- **Aid tenders:** give the deadline with the issuing office's time zone, the funder, the country and who can apply. Summarise the terms of reference and link to the notice; never copy aggregator listings.
- **Commercial premises:** commercial projects only: business name if public, the premises address, permit type, value and the contractor company. Never homeowners or residential permits.

## Example item

```yaml
- id: W41-03
  status: needs_review
  category: Rezonings and applications
  jurisdiction: Wrenfield Township, Tarrow County
  title: 48-acre rezoning sought for an 80 MW battery project on Kessler Road
  short_title: Kessler Road battery project rezoning (RZ-26-014)
  summary: >-
    Northbank Storage Partners LLC asks to rezone about 48.2 acres on the north side of
    Kessler Road from A-1 Agricultural to I-1 Light Industrial for a battery energy storage
    facility of about 80 MW / 320 MWh, as stated in the application (case RZ-26-014).
  why_it_matters: >-
    The regional planning commission holds the first public hearing and makes a
    recommendation on October 22. The township zoning commission then holds its own hearing.
  source_name: Kestrel Regional Planning Commission, agenda for October 22, 2026 (PDF)
  source_url: https://www.kestrelrpc.example/agendas/current-agenda.pdf
  source_ref: page 1, item 3a; case summary on page 2
  date: 2026-10-05
  deadline: 2026-10-22T18:00
  deadline_label: Planning commission hearing and recommendation
  details:
    Case: RZ-26-014
    Applicant: Northbank Storage Partners LLC
  tags: [rezoning, wrenfield-township]
  review_notes: >-
    CHECK: 48.2 acres and 80 MW / 320 MWh on page 2; meeting time 6:00 p.m. on page 1;
    the agenda file is replaced monthly, so the source name gives the meeting date.
```
