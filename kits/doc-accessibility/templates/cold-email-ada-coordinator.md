# Cold email to an ADA coordinator

For towns, counties, school districts, special districts and public colleges. Versions for health providers and EU businesses are at the end.

## Before you send

- **Find the right person.** Public bodies with 50 or more employees must name an ADA coordinator, and most list one on their website. Search the site for "ADA coordinator", "ADA notice" or "grievance procedure". School districts often call this person the Section 504 coordinator. In a small town it may be the clerk or the person who runs the website.
- **Look at their site for two minutes.** Note one real detail, such as "your agendas page links to about 40 PDFs". Don't crawl the whole site before they agree.
- **Link your sample.** Use the sample report in `samples/report/` and say clearly that it is for a fictional town.
- **Keep it human.** Send it from your own name. One email and one follow-up. No scare tactics.

## Subject lines (pick one)

- Documents on [website] and the ADA Title II web rule
- A list of every PDF on [website]
- Quick question about [Town]'s PDF backlog

## Email (under 150 words)

> Hi [First name],
>
> I help small public bodies get the documents on their websites ready for the ADA Title II web rule, which uses WCAG 2.1 AA. Most of the work is in PDFs: agendas, minutes, forms and reports.
>
> I noticed [one real detail, for example "your Agendas and Minutes page links to about 40 PDFs"].
>
> I offer a fixed-price document snapshot of [website]: a spreadsheet of every PDF, Word, Excel and PowerPoint file, a check of each one (tagged or not, scanned or real text, title, language, forms) and a suggested action: delete, archive, turn into a web page, or fix. It costs $[price], takes about [5] working days, and the spreadsheet is yours to keep.
>
> Here is a sample for a fictional town: [link]
>
> Would a 15-minute call next week help?
>
> [Your name]
> [Phone] · [Email]
>
> P.S. You get test results and a log for every file, not a compliance badge. Decisions about exceptions stay with you and your lawyer.

## Follow-up (5 to 7 working days later)

> Hi [First name],
>
> Following up on my note about the documents on [website]. If a full snapshot isn't right for now, I can send a free list of the PDFs linked from your home page and main menu, with a one-line check of each. Just reply "list" and you'll have it within two working days.
>
> [Your name]

If they reply "list", run the crawler with `--depth 1` and a slow `--delay`, then send the short list. That is your foot in the door.

## Version for health providers (Section 504 coordinator)

Replace the first paragraph with:

> I help health providers that receive funding from the US Department of Health and Human Services get the documents on their websites ready for the department's Section 504 rule, which uses WCAG 2.1 AA. Most of the work is in PDFs: patient forms, notices, brochures and reports.

## Version for EU businesses (European Accessibility Act)

Replace the first paragraph with:

> I help businesses covered by the European Accessibility Act make the documents they offer online accessible. The Act has applied since 28 June 2025, and its standard (EN 301 549) points to WCAG 2.1 AA. Most of the work is in PDFs: terms, product sheets, statements and forms.

## Don't

- Don't write "you are not compliant", "you will be sued", "ADA certified" or "guaranteed compliance".
- Don't quote deadlines without checking the current dates first. They have changed before.
- Don't send their own files back to them before they have asked for your help.
