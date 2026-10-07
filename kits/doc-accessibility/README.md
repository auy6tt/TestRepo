# Document accessibility starter kit

Everything you need to sell and deliver one service from day one: **finding, checking and fixing the PDF, Word, PowerPoint and Excel files on an organization's website so people using screen readers can use them.**

- **Step 1, the entry offer ($300 to $1,500):** crawl the client's website, list every document, check each one, and send a short report with a spreadsheet that says what to delete, archive, turn into a web page or fix.
- **Step 2, the follow-on work ($5 to $25 per page):** fix the files, test them, and hand over a log of what you did.

The kit has the scripts, the templates, a portfolio sample for a fictional town, and a Claude Code skill (`/doc-accessibility`) that runs the process for you.

## Contents

1. [The offer](#the-offer)
2. [Who buys, and where to find them](#who-buys-and-where-to-find-them)
3. [Price guide](#price-guide)
4. [Why buyers need this now](#why-buyers-need-this-now)
5. [Rules](#rules)
6. [Step by step](#step-by-step)
7. [Checklists](#checklists)
8. [Setup](#setup)
9. [How to run each script](#how-to-run-each-script)
10. [The portfolio sample](#the-portfolio-sample)
11. [Using it with Claude Code](#using-it-with-claude-code)
12. [Limits](#limits)
13. [Files in this kit](#files-in-this-kit)

## The offer

**Document accessibility snapshot (step 1).** A fixed price, delivered in about a week:

- a spreadsheet (`inventory.xlsx`) listing every PDF, Word, PowerPoint and Excel file linked from the website, with where it was found
- for each file: page count, tagged or untagged, real text or scanned image, title and language set or not, fillable form fields, duplicates, the year it seems to be from, and a suggested action: **Delete, Archive, Convert to web page, Fix, or Keep (check only)**
- a short report ("Document accessibility snapshot") with the key numbers, the files to fix first, and an estimate for fixing
- broken document links and links with unclear text such as "click here"

**Fixing (step 2).** Priced per page after the client decides what to keep:

- rebuild each file with real structure (headings, lists, table headers, alt text, title, language), usually in Word, and export a tagged PDF
- OCR scanned files, then tag them (or retype short ones)
- turn short or simple documents into web pages
- test every file: automated checks (veraPDF, PAC) plus a person with a screen reader
- deliver the fixed files, the test results and a per-file log

What you never sell: "ADA compliance", a certificate or a guarantee. See [Rules](#rules).

## Who buys, and where to find them

| Buyer | Why they need it | Where to find them |
|---|---|---|
| Small US public bodies: towns, villages, counties, school districts, special districts (water, fire, library, park, transit), community colleges, housing authorities | The ADA Title II web rule covers their documents. Agendas, minutes, forms and reports pile up as untagged PDFs. | Their website's "ADA coordinator" or "ADA notice" page; state municipal leagues and county associations (member directories); state lists of special districts; state school board associations; public bid boards (search "PDF remediation", "document accessibility", "ADA Title II") |
| US health providers that receive funding from the US Department of Health and Human Services: community health centers, hospitals, clinics, behavioral health providers that take Medicaid | The department's Section 504 rule uses WCAG 2.1 AA. Patient forms and notices are mostly PDFs. | State primary care associations, the HRSA health center finder, the provider's "Section 504 coordinator" or "nondiscrimination notice" page |
| EU businesses under the European Accessibility Act: online shops, banks, transport companies, e-book publishers | Documents they offer online (terms, product sheets, statements, forms) are in scope. | Their "accessibility statement" page, e-commerce communities, chambers of commerce |
| Accessibility vendors and web agencies that build public-sector websites | They need overflow help with PDFs. | LinkedIn ("digital accessibility", "PDF remediation"), agency websites; offer white-label work at a fixed per-page rate |

On LinkedIn, search job titles such as "ADA coordinator", "accessibility coordinator", "web content manager", "city clerk" and "communications director" together with "city of", "county" or "school district".

Start with `templates/cold-email-ada-coordinator.md`. Send a handful of personal emails a day rather than a big blast.

## Price guide

| What | Price (estimate) | Notes |
|---|---|---|
| Snapshot, up to 100 documents | $300 | About one day of work including the report |
| Snapshot, 100 to 500 documents | $500 to $900 | |
| Snapshot, 500 to 1,500 documents | $900 to $1,500 | Above that, quote per section of the site |
| Fixing simple pages (letters, notices, agendas, minutes) | $5 to $8 per page | Cheapest when the client sends the Word file |
| Fixing moderate pages (headings, lists, simple tables, a few images) | $8 to $15 per page | |
| Fixing complex pages (big tables, charts, maps, forms, poor scans) | $15 to $25 per page | Forms are often quoted per form instead |
| Converting a document to a web page | The same per-page rates | Often the best choice for short documents |
| Monthly upkeep (new agendas, minutes and notices) | A fixed monthly fee for up to a set number of pages | Turns one job into steady income |

These prices are estimates. Check what your market pays before you quote.

Add 25 to 50 percent for rush jobs (under three working days) and set a minimum per batch (for example $150). Give a fixed quote after the snapshot, never an open-ended hourly rate.

## Why buyers need this now

State these facts in client documents with the note **"verify current dates"**:

- **US public bodies.** The US Justice Department's rule under Title II of the Americans with Disabilities Act requires state and local governments' web content, including documents posted online, to meet **WCAG 2.1 Level AA**. Deadlines are reported as **26 April 2027** for entities serving 50,000 or more people and **26 April 2028** for smaller ones (special district governments were grouped with the smaller ones in the 2024 rule). The dates have moved once already, so verify the current ones before you quote them.
- **US health providers.** Providers that receive funding from the US Department of Health and Human Services are covered by its Section 504 rule, which also uses WCAG 2.1 AA. Deadlines depend on the organization's size; verify them.
- **EU businesses.** The European Accessibility Act has applied since 28 June 2025. Its standard (EN 301 549) points to WCAG 2.1 AA. Microenterprises that provide services are exempt.

The Title II rule has a few exceptions, for example for archived content and some older documents. **The client's ADA coordinator or lawyer decides whether an exception applies, never you.** The inventory only marks "archive candidates" to help them decide.

## Rules

1. **Never promise "ADA compliant", "WCAG compliant" or certification.** Not in emails, reports, invoices or your profile. You deliver test results and a log. Write "checked on [date] with [tools]".
2. **A person checks every fixed file.** Automated tools catch only part of the problems. Someone checks reading order, alt text, tables and forms with the NVDA screen reader and the free PAC checker (or Acrobat Pro) on Windows, using `templates/human-check-checklist.md`.
3. **Exceptions are the client's call.** Their ADA coordinator or lawyer decides on archived content and other exceptions.
4. **Verify dates** before you quote any deadline.
5. **Crawl politely and with permission.** Get the client's written OK before a full crawl. Before that, keep any look at a prospect's site light: a few pages, slow rate. The crawler follows robots.txt and waits between requests; put your contact email in its user agent.
6. **Don't change the meaning.** Keep wording, numbers and signatures as they are. Ask before fixing typos in legal or official documents. Keep the originals.
7. **The client approves alt text** for complex charts, maps and diagrams. You draft it.
8. **Don't remove security settings** from a client's file without asking. The fix script skips protected files.
9. **Protect client files.** Keep them out of public repositories: put them in `clients/` at the repository root (git ignores it) or in a private repo, one folder per client. Turn off model training in Claude's privacy settings, and delete client files when the job is done.

## Step by step

**Win the job**

1. Find 20 prospects (see [Who buys](#who-buys-and-where-to-find-them)) and send the cold email with a link to the sample report. Follow up once.
2. On the call, agree the scope in writing: the website address, any other hosts that hold documents (agenda systems, file storage), sections to skip, the price, the delivery date and permission to crawl.

**Step 1: the snapshot**

3. Allow the client's domains in this environment's network settings (see the note in [Setup](#setup)).
4. Crawl: `crawl_documents.py` with `--download` and `--sitemap`.
5. Triage: `triage_pdfs.py` with `--crawl`. This writes `inventory.xlsx`.
6. Open `inventory.xlsx`. Read the suggested actions, open a few files to sanity-check them, and change the "Suggested action" or "Priority" column where you disagree.
7. Make the report: `make_report.py --pdf`. Read it, edit anything that doesn't fit, and fill in your contact details.
8. Send the report PDF and `inventory.xlsx`. Offer a short call and quote step 2 from the estimate.

**Step 2: fixing**

9. The client marks each file keep, fix, convert, archive or delete (with their ADA coordinator) and sends the original Word files where they have them.
10. Run `fix_basics.py --inventory inventory.xlsx --ocr` for quick wins: titles, language, title bar and OCR on scans. This is not the fix itself.
11. Fix each file properly:
    - **Have the Word file?** Fix its structure in Word (or ask Claude to fix the .docx), then `docx_to_tagged_pdf.py --compare old.pdf --validate`.
    - **Only a PDF?** Recreate it as a structured Word file (Claude can draft it from the PDF's text; you check it against the original), then convert as above. Or tag it in Acrobat Pro.
    - **Scanned?** OCR first, check the text against the scan, then rebuild or tag.
    - **Form?** Rebuild the fields with proper names in Acrobat Pro, or offer an accessible web form instead.
    - **Short and simple?** Make it a web page.
12. Run `validate_pdfs.py` (veraPDF) on the fixed files.
13. Do the human check on Windows with NVDA and PAC (`templates/human-check-checklist.md`).
14. Fill the log: `make_remediation_log.py` fills the automated columns; you fill the human-check columns.
15. Deliver the fixed files, the log, the PAC reports and the veraPDF results. Invoice, ask for a testimonial, and offer monthly upkeep.

## Checklists

**Before you crawl**

- [ ] Written OK from the client, and the list of hosts and sections to include or skip
- [ ] Client domains allowed in Network access (cloud sessions)
- [ ] Your contact email in `--user-agent`
- [ ] An empty folder for this client in `clients/` at the repository root (git ignores it), never in `samples/` or any other folder git tracks

**Before you send the snapshot**

- [ ] Crawl summary read: page limit not hit by surprise, robots.txt notes understood
- [ ] "Not checked" sheet read: broken links, blocked files, off-site files
- [ ] Five or more files opened by hand to confirm the automated results
- [ ] Suggested actions reviewed and edited where needed, then `make_report.py` run again
- [ ] Report read from start to end; no "compliant", "certified" or "guarantee"; deadlines marked "verify current dates"
- [ ] Your contact details and the client's name are right

**Before you deliver fixed files**

- [ ] Every file opened and compared with the original (nothing missing, numbers and names unchanged)
- [ ] veraPDF and PAC results saved
- [ ] Human check done and recorded for every file, by a person
- [ ] OCR text checked against the scan
- [ ] Alt text for complex images approved by the client
- [ ] Remediation log complete; anything not fixed is listed with the reason

## Setup

**One command (Linux and Claude Code cloud sessions):**

```sh
bash kits/setup.sh doc-accessibility
PY=~/.venvs/doc-accessibility/bin/python
```

It installs the system tools (LibreOffice Writer, Tesseract, Ghostscript and others, with apt), then runs this kit's own `scripts/setup.sh --verapdf`. That creates a Python virtual environment at `~/.venvs/doc-accessibility` with the packages in `requirements.txt` and downloads the veraPDF validator (needs Java and Maven, both present in cloud sessions). You can also run `bash kits/doc-accessibility/scripts/setup.sh --verapdf` on its own. `bash kits/setup.sh --list` shows where each kit's Python is. Cloud sessions start from a clean machine, so run it again in each new session, or add it to your environment's setup script.

Good to know:

- Some machines have LibreOffice without its Writer part. Word-to-PDF conversion then fails with "source file could not be loaded". The setup script installs `libreoffice-writer` to fix this.
- On a Mac: `brew install --cask libreoffice` and `brew install tesseract ghostscript`, then `python3 -m venv ~/.venvs/doc-accessibility && ~/.venvs/doc-accessibility/bin/pip install -r kits/doc-accessibility/requirements.txt`. Install veraPDF from verapdf.org and set `VERAPDF_DIR` to its folder.
- The human check needs Windows (NVDA, PAC, Acrobat Reader). Use a Windows computer or a Windows virtual machine.

**Network access for real client sites.** This cloud environment's network policy blocks most websites, so the crawler cannot reach a client's site until you allow it. To audit a real site from here: at claude.ai/code, click the cloud icon showing your environment's name (above the message box), hover over the environment and click the settings icon. Under Network access, choose "Custom" (newer app versions may call it "Limited") and add the client's domains to the allowed domains. Keep the "Also include default list of common package managers" box ticked (newer versions: "Allow package managers"). Add every host the documents live on, such as a separate agenda or file-storage host. Steps: https://code.claude.com/docs/en/cloud-environments#network-access. The sample site in this kit runs on your own machine, so it needs no network access.

## How to run each script

Run these from the repository root. Put each client's files in their own folder under `clients/` at the repository root, for example `C=clients/town-of-example`. The repository's `.gitignore` keeps `clients/` out of git, so client files are never pushed to this public repository.

```sh
PY=~/.venvs/doc-accessibility/bin/python
K=kits/doc-accessibility/scripts
C=clients/town-of-example
```

**1. Crawl the site** (`crawl_documents.py`)

```sh
$PY $K/crawl_documents.py https://www.example-town.gov/ --out $C/crawl --download $C/downloads \
    --sitemap --depth 3 --delay 1 --user-agent "DocInventory/1.0 (+mailto:you@example.com)"
```

Follows links up to `--depth` clicks from the start page, reads robots.txt (including `*` and `$` patterns and Crawl-delay), waits at least `--delay` seconds between requests, and stops at `--max-pages` (default 500). It finds documents by file extension, by asking the server about links like `/DocumentCenter/View/123` that many town website platforms use, and in `<iframe>`, `<embed>` and `<object>` tags. Other useful options: `--also-download-from files.example-host.com` (documents the client keeps on another host), `--exclude "calendar|/events/"` (skip endless calendar pages), `--include-subdomains`.

Writes `documents.csv` (one row per document), `document_links.csv` (every link, its text, and a note when the text is unclear), `pages.csv`, `crawl_summary.md` and `crawl_summary.json`.

**2. Triage the documents** (`triage_pdfs.py`)

```sh
$PY $K/triage_pdfs.py $C/downloads --crawl $C/crawl/documents.csv --out $C/inventory --client "Town of Example"
$PY $K/triage_pdfs.py some-file.pdf      # quick check of one file, prints only
```

For PDFs: pages, tags (StructTreeRoot and MarkInfo) with headings, images without alt text and table headers inside the tags, real text or scanned image (and OCR layers), title and whether the title bar shows it, language, form fields and whether they have names, bookmarks, security settings, duplicates and dates. Word, PowerPoint and Excel files get basic checks (title, language, heading styles, alt text, table header rows, slide titles, sheet names). Writes `inventory.xlsx` (Summary, Inventory, Not checked, How to read), `inventory.csv` and `summary.md`. Options: `--archive-before 2023` (files dated earlier are suggested for Archive; default is three years ago), `--short-pages 1`, `--rate-low 5 --rate-high 25`.

**3. Make the snapshot report** (`make_report.py`)

```sh
$PY $K/make_report.py --inventory $C/inventory/inventory.xlsx --crawl-summary $C/crawl/crawl_summary.json \
    --client "Town of Example" --prepared-by "Your Name" --contact "you@example.com, 555-0100" \
    --sector us-public --out $C/report/document-snapshot.docx --pdf
```

Fills `templates/snapshot-report-template.docx` from the Inventory sheet (so your edits count) and exports a tagged PDF. `--sector` is `us-public`, `us-health` or `eu` and picks the "Why this matters" text.

**4. Safe automatic fixes** (`fix_basics.py`)

```sh
$PY $K/fix_basics.py $C/downloads --crawl $C/crawl/documents.csv --suggest-titles $C/titles.csv   # review titles first
$PY $K/fix_basics.py $C/downloads --out $C/basic-fixes --titles $C/titles.csv \
    --inventory $C/inventory/inventory.xlsx --lang en-US --ocr
```

Sets the title (document info and XMP), the language and the "show title in title bar" setting, and runs OCR on scanned files with ocrmypdf when `--ocr` is given and Tesseract is installed. Never changes tags, reading order or alt text, never touches protected files, never overwrites originals, and skips files marked Delete or Archive in the inventory. Writes fixed copies and `fix-log.csv`, which says what is still to do for each file.

**5. Word to tagged PDF** (`docx_to_tagged_pdf.py`)

```sh
$PY $K/docx_to_tagged_pdf.py $C/word/agenda.docx --out $C/fixed --compare $C/downloads/agenda.pdf --validate
```

Checks the Word file first (title, language, heading styles, alt text, table header rows), converts it with LibreOffice with tagged PDF and PDF/UA turned on, then runs the triage checks on the new PDF. `--compare` shows the old and new file side by side and writes `comparison.md`; `--validate` adds veraPDF results.

**6. veraPDF checks** (`validate_pdfs.py`)

```sh
$PY $K/validate_pdfs.py $C/fixed --out $C/fixed
```

Runs veraPDF's PDF/UA-1 machine checks and writes `validation.csv` and `validation.md` with plain-English labels. Passing does not make a file accessible; it means the machine-testable part passed.

**7. Remediation log** (`make_remediation_log.py`)

```sh
$PY $K/make_remediation_log.py --before $C/downloads --after $C/fixed --out $C/remediation-log.xlsx \
    --work "Rebuilt in Word, exported tagged PDF" --validate
$PY $K/make_remediation_log.py --before $C/downloads --after $C/basic-fixes --fix-log $C/basic-fixes/fix-log.csv \
    --out $C/remediation-log.xlsx --append
```

Fills the automated columns of `templates/remediation-log-template.xlsx` (before and after checks, work done, veraPDF). The human-check columns say "To do" until a person does them.

**Other scripts**

- `setup.sh`: installs everything (see [Setup](#setup)).
- `run_sample_demo.py`: runs the whole process on the fictional sample site. `--serve-only` just serves the sample site at http://127.0.0.1:8765/ so you can try the crawler by hand.
- `build_samples.py`: rebuilds the fictional town website and its documents (it deletes and remakes `samples/town-site/` and `samples/source-files/`).
- `build_templates.py --force`: rebuilds the two Office templates from the default text. This overwrites your edits, so without `--force` it stops and changes nothing.
- `office_helpers.py`: shared code for making accessible Word files.

All the other scripts print their options with `--help` and then stop without changing anything.

## The portfolio sample

`samples/` is a complete run of the service on a **fictional** town, Fernwick. Fernwick is not a real place; all names and numbers are made up. Show it to prospects as "a sample for a fictional town".

| Folder | What it shows |
|---|---|
| `samples/town-site/` | The fictional town website: 9 public pages (one reachable only through the sitemap), a staff-only section blocked by robots.txt, and 14 documents: untagged PDFs, an exact duplicate, a 2019 file, a fillable form, an image-only scan, a file served from a link with no file extension, a tagged PDF with problems, one properly tagged PDF made from Word, and Word, Excel and PowerPoint files. Pages also link to a missing file, a staff-only file and an off-site file. |
| `samples/source-files/` | The Word files behind the tagged PDFs, including the rebuilt council agenda |
| `samples/crawl/` | Crawl output: documents, links, pages and the crawl summary |
| `samples/downloads/` | The documents the crawler downloaded |
| `samples/inventory/` | `inventory.xlsx`, `inventory.csv` and `summary.md` |
| `samples/report/` | The filled snapshot report, as Word and as a tagged PDF |
| `samples/fixes/before-after/` | The council agenda before (untagged) and after (rebuilt from Word): `comparison.md`, veraPDF results (7 rules failed before, all machine checks passed after) |
| `samples/fixes/basic-fixes/` | Copies with titles, language and OCR added by `fix_basics.py`, and `fix-log.csv` |
| `samples/fixes/remediation-log-sample.xlsx` | The log with the automated columns filled; the human-check columns are honestly marked "To do" |

To run it all again: `$PY kits/doc-accessibility/scripts/run_sample_demo.py --rebuild` (under a minute).

**Put your own name on the sample report.** The sample report says "Your Name, Document Accessibility Services". Run the demo again with your name and contact details; it rebuilds `samples/report/fernwick-document-snapshot.docx` and `.pdf`:

```sh
$PY kits/doc-accessibility/scripts/run_sample_demo.py --prepared-by "Your Name, Your Business" --contact "you@example.com"
```

The report shows the website as `https://www.fernwick.example/`, a made-up address, although the demo crawls a copy of the site on your own machine.

## Using it with Claude Code

The skill at `.claude/skills/doc-accessibility/SKILL.md` teaches Claude this process. Type `/doc-accessibility` or just ask, for example:

- "Run a document snapshot for https://www.example-town.gov for the Town of Example."
- "Here is inventory.xlsx. Mark the 2019 minutes as Archive and remake the report."
- "Rebuild this agenda PDF as a structured Word file, convert it to a tagged PDF and compare it with the original."
- "Draft alt text for the charts in this report for the client to approve."
- "Write the cold email for the ADA coordinator of [town], mentioning their agendas page."

## Limits

- **Automated checks are not enough.** They cannot judge reading order, alt text quality, table logic or colour contrast. That is why a person checks every fixed file.
- **The crawler does not run JavaScript.** Document lists loaded by scripts, files behind logins and files inside search tools can be missed. Ask the client about document libraries and agenda systems, and add those hosts.
- **LibreOffice is the free route for Word files only.** Complex PDFs without a Word source may need Acrobat Pro (paid) for tagging, especially forms.
- **This kit checks documents, not web pages.** Checking the HTML pages themselves is a separate service.
- **Word page counts** come from the file's saved statistics and can be out of date. Open the file to check before quoting.

## Files in this kit

```
kits/doc-accessibility/
├── README.md                         this guide
├── requirements.txt                  Python packages
├── scripts/
│   ├── setup.sh                      installs everything
│   ├── crawl_documents.py            step 1: crawl and download
│   ├── triage_pdfs.py                step 1: checks and inventory.xlsx
│   ├── make_report.py                step 1: the snapshot report
│   ├── fix_basics.py                 step 2: title, language, OCR
│   ├── docx_to_tagged_pdf.py         step 2: Word to tagged PDF, before and after
│   ├── validate_pdfs.py              step 2: veraPDF checks
│   ├── make_remediation_log.py       step 2: the per-file log
│   ├── run_sample_demo.py            runs everything on the sample site
│   ├── build_samples.py              makes the sample site
│   ├── build_templates.py            makes the Office templates
│   └── office_helpers.py             shared Word helpers
├── templates/
│   ├── snapshot-report-template.docx
│   ├── remediation-log-template.xlsx
│   ├── cold-email-ada-coordinator.md
│   └── human-check-checklist.md
└── samples/                          the fictional town portfolio sample
```
