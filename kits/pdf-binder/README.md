# PDF binder kit

Two paid services that share one set of scripts:

| | **A. Safety data sheet (SDS) binders** | **B. Submittal and handover packages** |
|---|---|---|
| **Who buys** | Small US employers that use chemicals: auto repair and body shops, cleaning companies, salons, small manufacturers, school facilities teams | Specialist subcontractors (mechanical, electrical, fire, audio-visual, finishes) and small general contractors |
| **What they get** | A current chemical inventory, the latest SDS for every product, old and missing sheets flagged, and an indexed, bookmarked binder PDF | Product datasheets, manuals and warranties merged into an indexed, bookmarked binder in the general contractor's order, with a cover sheet and a submittal log |
| **Price guide** | $300–1,500 per site | $300–1,500 per submittal package; $500–3,000 per handover binder |
| **You never** | Write, change or "correct" a safety data sheet, classify chemicals or give safety advice | Alter a manufacturer's document or certify compliance |

The scripts do the slow, fiddly part (merging, page numbers, contents, bookmarks, reading dates and codes out of PDFs). You do the part clients pay for: collecting the right documents, checking what the scripts flag, and delivering a clean, correct binder on time.

## What's in the kit

```text
kits/pdf-binder/
├── README.md                  this guide
├── requirements.txt           Python packages
├── scripts/
│   ├── build_binder.py        merge PDFs into one binder: cover, contents, dividers, bookmarks, index.xlsx
│   ├── extract_sds.py         read SDS PDFs into inventory.xlsx; flag old, missing and unclear sheets
│   ├── verify_binder.py       check a finished binder: pages, bookmarks, contents numbers, links
│   ├── make_templates.py      recreate the spreadsheet templates
│   ├── make_samples.py        recreate the portfolio samples (with your business name)
│   └── kitlib.py              shared helpers (not run directly)
├── templates/
│   ├── intake-checklist-sds-binder.md
│   ├── intake-checklist-submittal-handover.md
│   ├── hazcom-written-program-outline.md   draft written programme for the employer to adapt
│   ├── sds-site-list-template.xlsx         on-site chemical list the client confirms
│   ├── sds-manual-entries-template.csv     details you read off a sheet yourself (kept across re-runs)
│   ├── binder-index-template.xlsx / .csv   the list of documents for build_binder.py
│   ├── binder-cover-sds.toml / -submittal.toml / -handover.toml
│   └── submittal-log.xlsx
├── samples/                   fake, clearly watermarked portfolio samples (see below)
└── tests/test_kit.py          quick self-test
```

## Set up (once per session)

You need Python 3.11 or newer. In the Claude Code cloud sandbox:

```bash
cd kits/pdf-binder
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tests/test_kit.py          # should end with "All tests passed."
```

Every command below runs from `kits/pdf-binder` with `.venv/bin/python`. (On Windows the path is `.venv\Scripts\python`.) Or just ask Claude: *"Use the pdf-binder skill to set up the kit."*

## The samples (your portfolio)

Everything in `samples/` is invented: products, companies, people and the project. Every input page carries a large SAMPLE watermark and a red SAMPLE banner.

| Folder | What it shows |
|---|---|
| `samples/sds-binder/` | 9 fake safety data sheets for a fictional auto shop, each testing something (clean, two-column layout, codes printed only as wording, old date, messy letter-spaced text, an old MSDS form, a scanned image with no text, a sheet not on the client's list) plus one product with no sheet. The scanned sheet's details are entered by hand in `manual-entries.csv`. Output: `inventory.xlsx` and a 24-page binder. |
| `samples/om-handover/` | Datasheets, manuals (with their own bookmarks), warranties, an A4 page, a rotated landscape page and an 11 x 17 drawing for a fictional clinic's HVAC. Output: a 44-page O&M binder with page numbers stamped, and a filled-in submittal log. |
| `samples/submittal-package/` | A small product-data submittal with a reviewer-stamp cover and only selected pages of a manual. |

Put your own name on them before you show anyone:

```bash
.venv/bin/python scripts/make_samples.py --business "Jane Doe Document Services"
```

This rebuilds all three, runs the checks, and takes under a minute. Show prospects the binder PDFs and spreadsheets in each `output/` folder. Never pass a sample off as real client work.

---

## Offer A: safety data sheet binders

### Why now

OSHA revised its Hazard Communication Standard in 2024, and employers need current safety data sheets, a current chemical list and updated training. **Check the current compliance dates on osha.gov before you quote one.** The employer date for single-substance chemicals is reported as 20 November 2026, with later dates for mixtures. State it accurately and never use it to scare people.

### Who buys and where to find them

- **Auto repair and body shops, cleaning companies, salons:** Google Maps searches like "auto repair near [town]", local chambers of commerce, business associations.
- **Small manufacturers:** industrial parks, local manufacturing associations, LinkedIn (operations or plant managers).
- **School facilities teams:** district facilities or maintenance departments; small districts and private schools are easier to reach.
- **People already searching:** "SDS binder", "OSHA HazCom update", "safety data sheet management".

A first message that works: offer a 48-hour binder refresh from photos of their shelves, attach the sample binder, and give a fixed price.

### Price guide

Starting points. Adjust to your market and the state of their records.

| Job | Suggested price |
|---|---|
| One site, up to about 25 products, records in decent shape | $300–450 |
| 25–75 products | $500–900 |
| 75–150 products, or messy records and many missing sheets | $900–1,500 |
| Extra site | Quote separately |
| Rush (48 hours) | Add 25% |
| Draft written programme (from the outline in templates/) | Add $100–250 |
| Yearly refresh | Offer at a lower price than the first job |

### What you deliver

1. **Binder PDF:** cover, clickable contents, a divider per area, each safety data sheet exactly as published, bookmarks, and a PENDING page for each sheet still on order.
2. **inventory.xlsx:** every product with manufacturer, SDS date, age, signal word, hazard codes, location, status and notes, plus a printable *Chemical List* sheet for the employer to sign.
3. **Binder index spreadsheet:** where each sheet starts and ends.
4. Optional: the draft written programme (`templates/hazcom-written-program-outline.md`).

### Step by step

1. **Intake.** Go through `templates/intake-checklist-sds-binder.md` with the client. Get shelf photos, purchase records and their old binder.
2. **Make a job folder.** Keep each client separate, ideally in a private repo, because this container is temporary:
   ```text
   ~/jobs/riverside-auto/
   ├── site-list.xlsx     (copy of templates/sds-site-list-template.xlsx)
   ├── sds/               (one PDF per product)
   ├── cover.toml         (copy of templates/binder-cover-sds.toml)
   ├── manual-entries.csv (details you read off sheets yourself; see step 6)
   └── output/
   ```
3. **Build the on-site list.** One row per product, name as on the label, with manufacturer and location. Claude can read the shelf photos and draft it; you check it.
4. **Get the current sheets.** Download each SDS from the manufacturer's or supplier's website on your own computer (most websites are blocked in the cloud sandbox), save as PDF and upload them to `sds/`. Never type up or edit a sheet.
5. **Read the sheets:**
   ```bash
   JOB=~/jobs/riverside-auto
   .venv/bin/python scripts/extract_sds.py --sds-folder $JOB/sds --site-list $JOB/site-list.xlsx \
       --out $JOB/output/inventory.xlsx --group-by location --client "Riverside Auto Care"
   ```
6. **Work through the flags** in the Inventory sheet (see "Statuses" below). Amber cells were unclear; red cells weren't found; hover over a cell's red corner to see why. Open the PDF and read the sheet. Then record what you read in `manual-entries.csv` (copy `templates/sds-manual-entries-template.csv`): one line per detail (file, field, value, note), plus a line with the field `reviewed` and the value `yes` when the whole sheet is checked. Rerun step 5 with `--manual $JOB/manual-entries.csv`. Hand-entered cells turn green, and they survive every rerun. You only ever change the spreadsheet, never the PDF.
7. **Chase missing and old sheets.** Ask the manufacturer or supplier; note the date. Rerun step 5 when new sheets arrive.
8. **Client confirms the list.** Send the *Chemical List* sheet. Record who confirmed it and when. The client decides what's on the list, not you.
9. **Check the Binder Index sheet** (titles, sections, `include` yes/no), fill in `cover.toml`, then build:
   ```bash
   .venv/bin/python scripts/build_binder.py --pdf-folder $JOB/sds --index $JOB/output/inventory.xlsx \
       --sheet "Binder Index" --cover $JOB/cover.toml --out $JOB/output/Riverside-Auto_SDS-Binder.pdf
   .venv/bin/python scripts/verify_binder.py $JOB/output/Riverside-Auto_SDS-Binder.pdf
   ```
   Leave `--page-numbers` off for SDS binders so every sheet stays exactly as published.
10. **Look at it.** Open the PDF: cover, contents, a few bookmarks, every PENDING page. Then deliver the PDF and spreadsheets.

### Statuses in inventory.xlsx

| Status | Meaning | What you do |
|---|---|---|
| OK | Sheet found, details read clearly, not too old | Spot-check a few |
| CHECK FOR NEWER SDS | Older than the age limit (default 3 years) or dated before 19 July 2024, when OSHA's 2024 update took effect | Look for a newer version; OSHA sets no expiry date, this is only a prompt |
| REVIEW | Something was unclear (a label, a date that could be read two ways, codes found only as wording, a scanned sheet with no text, a possible name match) | Open the PDF and check the highlighted cells |
| MISSING SDS | On the site list but no sheet found | Get the current sheet |
| REPLACE: OLD FORMAT | An old MSDS form, not the 16-section SDS | Get the current SDS |
| NOT ON SITE LIST | A sheet was supplied but the product isn't on the client's list | Ask the client; it's left out of the binder (`include` = no) |

The status, age and flag columns are formulas: they update each time the file is opened and when you change the limits on the Settings sheet.

### Rules for Offer A

- Never write, edit, retype or "correct" a safety data sheet. If one looks wrong, the client asks the manufacturer.
- Never classify a chemical, judge its hazards or give safety advice. The codes in the spreadsheet are copied from the sheets.
- The employer confirms the on-site list and is responsible for compliance.
- A qualified person trains staff. You don't.
- Quote the OSHA date accurately and point people to osha.gov.

---

## Offer B: submittal and handover packages

### Who buys and where to find them

- **Subcontractor project managers and project coordinators** on LinkedIn (mechanical, electrical, fire protection, audio-visual, finishes).
- **Trade associations:** for example NSCA (audio-visual and systems integrators, US) and FIS (finishes and interiors, UK).
- **Job posts** for "submittal coordinator", "closeout documents" or "O&M manuals".
- **Local subcontractors** listed on general contractors' and plan rooms' public subcontractor lists.

A first message that works: show the sample O&M binder and offer a first binder at a flat price with a three-day turnaround.

### Price guide

| Job | Suggested price |
|---|---|
| Submittal package: a few products, under about 50 pages | $300–500 |
| Submittal package: several sections, with a spec checklist for the PM | $600–1,500 |
| Handover binder: one trade, under about 200 pages | $500–1,000 |
| Handover binder: several sections, 200–800 pages | $1,000–2,000 |
| Large multi-volume closeout | $2,000–3,000 |
| Resubmittal after comments | Quote separately or include one round |

### What you deliver

- **Submittal package PDF:** cover with project details and two empty boxes for the reviewers' stamps, contents, bookmarks, the documents in order, page numbers if required, and a draft spec checklist if agreed.
- **Handover (O&M) binder PDF:** cover, contents, a divider per section in the general contractor's order, manuals with their own bookmarks kept, warranties, drawings, PENDING pages for documents still to come, page numbers.
- **Index spreadsheet** and an updated **submittal log**.

### Step by step

1. **Intake.** Use `templates/intake-checklist-submittal-handover.md`. Get the project's submittal and closeout rules, the required order, the cover or transmittal form, and every document.
2. **Job folder:** `docs/` (all PDFs), `index.xlsx` (copy of `templates/binder-index-template.xlsx`), `cover.toml` (copy of `binder-cover-submittal.toml` or `binder-cover-handover.toml`), `output/`.
3. **Fill in the index** in the required order. Use the `pages` column to include only some pages of a long catalogue, and leave `file` blank for anything still to come.
4. **Build and check:**
   ```bash
   JOB=~/jobs/harborview-hvac
   .venv/bin/python scripts/build_binder.py --pdf-folder $JOB/docs --index $JOB/index.xlsx \
       --cover $JOB/cover.toml --out $JOB/output/Harborview_Div23_OM.pdf --page-numbers
   .venv/bin/python scripts/verify_binder.py $JOB/output/Harborview_Div23_OM.pdf
   ```
   For a small submittal, add `--no-dividers --tabs none`. If the general contractor wants "Tab A, Tab B", use `--tabs letters --section-word Tab`.
5. **Update the submittal log** (`templates/submittal-log.xlsx`): one row per submittal and resubmittal.
6. **Send it to the PM to review and sign** before it goes to the general contractor.

### Rules for Offer B

- Never alter a manufacturer's document. Mark-ups showing the selected model are done by the PM or exactly as the PM instructs.
- Never certify compliance. A spec checklist only shows where each requirement appears; the PM confirms it.
- Drawings and specifications are confidential to the project. Don't reuse them in samples.

---

## Script reference

### build_binder.py

```bash
.venv/bin/python scripts/build_binder.py --pdf-folder DOCS --index INDEX.csv|.xlsx --out BINDER.pdf [options]
```

| Option | What it does |
|---|---|
| `--cover cover.toml` | Cover details (copy a file from `templates/`) |
| `--sheet "Binder Index"` | Which sheet to read in an .xlsx index (default: "Binder Index", "Index", or the first sheet with the right columns) |
| `--page-numbers` | Stamp "Page X of Y" in the bottom margin of every document page (with a thin white outline so it reads on any background). Off by default. |
| `--stamp-prefix "Project 2041 O&M"` | Text before the stamped page number |
| `--stamp-position` | `bottom-right` (default), `bottom-center`, `bottom-left` or `top-right` |
| `--no-dividers`, `--no-toc` | Leave out divider pages or the contents |
| `--tabs numbers\|letters\|none`, `--section-word Tab` | How sections are numbered and named |
| `--missing error\|placeholder\|skip` | What to do if a listed file is missing or unreadable (default: stop and list every problem) |
| `--no-source-bookmarks` | Don't copy each document's own bookmarks |
| `--watermark DRAFT` | Faint text across the generated pages |
| `--page-size a4` | A4 generated pages (default US letter) |
| `--cover-only` | Draw just the cover, to proof it with the client |
| `--title`, `--subtitle`, `--type` | Override the cover file |

Output: the binder PDF and `<binder name>-index.xlsx` (Index and Summary sheets, including a SHA-256 fingerprint of each source file so you can prove which version you used). Page numbers in the contents are the PDF's own page numbers, so "page 12" in the contents is page 12 in any PDF viewer.

**Index columns** (CSV or XLSX, header names not case sensitive):

| Column | Required | Notes |
|---|---|---|
| section | no | Tab or area. Sections appear in the order they first appear. Blank = "Documents". |
| title | yes | Shown in the contents and bookmarks |
| file | yes (column) | PDF name inside `--pdf-folder`, sub-folders allowed. Blank = PENDING placeholder page. ".pdf" can be left off; a close misspelling gets a "Did you mean" hint. |
| order | no | 1, 2, 10 or 1.1, 1.2. Blank column = keep row order. |
| notes | no | Small print under the title in the contents |
| pages | no | e.g. `3-5` or `1,4-6`; blank = all pages |
| include | no | `no` leaves the row out |

Rows starting with `EXAMPLE` are ignored, so template examples never end up in a binder.

**Cover file** (TOML): `type` (sds, submittal, handover, general), `title`, `subtitle`, `organization` (your business), `footer_text`, `accent_color`, `logo`, `watermark`, optional `notice`, then a `[details]` table of `"Label" = "Value"` lines in the order you want. `"today"` prints today's date; `""` prints a blank line to sign. Each type has a suitable standard notice at the bottom (for example, the submittal cover says the preparer does not certify compliance).

### extract_sds.py

```bash
.venv/bin/python scripts/extract_sds.py --sds-folder SDS --out inventory.xlsx [options]
```

| Option | What it does |
|---|---|
| `--site-list site-list.xlsx` | The client's on-site list. Matches products to sheets (by the `SDS file` column, or by name), flags MISSING SDS and NOT ON SITE LIST, and adds locations. |
| `--manual manual-entries.csv` | Details you read off a sheet yourself (columns: sds file, field, value, note). Fields: product, manufacturer, date, signal word, codes, pictograms, version, and `reviewed` = yes to clear the sheet's review flags. Applied on every run. |
| `--group-by location` | One binder section per location (default: one section) |
| `--max-age-years 3` | Age that triggers CHECK FOR NEWER SDS |
| `--update-cutoff 2024-07-19` | Sheets dated before this are flagged too; `none` turns it off |
| `--date-order MDY\|DMY` | How to read dates like 03/05/2024 when the sheet doesn't make it clear (default MDY). If both readings are possible and the answer changes a flag, the row goes to REVIEW. |
| `--client "Name"` | Printed on the spreadsheet |
| `--as-of 2026-11-01` | Work out ages as of another date |
| `--recursive` | Include PDFs in sub-folders |

What it reads, and how carefully:

- **Product name, manufacturer/supplier, revision or issue date** from Section 1 and the page headers, using many label spellings ("Trade name", "Supplier", "Date Prepared", "Revised"...). Dates under "Supersedes" or "Date of first issue" are ignored. A print date alone is flagged.
- **Signal word** from its label, or a stand-alone DANGER/WARNING line in Section 2.
- **Hazard codes H200–H420** from Section 2 only, so ingredient codes in Section 3 and the full-text list in Section 16 don't leak in. Combined codes (H302+H332), spaced codes (H 319) and suffixes (H360FD) are handled. If a sheet prints only the statement wording (common on US sheets), the codes are matched from the standard wording and marked *From wording (verify)*.
- **Pictograms** only when the sheet names them in text (GHS02, "Flame"...). Most sheets show them as pictures, so "Not named in text" is normal.
- It copes with two-column layouts, letter-spaced headings, hyphenated lines and diagonal "UNCONTROLLED COPY" stamps, and tries three text readers per file. Scanned sheets with no text, password-protected or damaged files, old MSDS forms, files holding more than one SDS and non-English sheets are all flagged for a person to handle.

For a scanned sheet, open the PDF (Claude can read the page images), put the details in `manual-entries.csv`, and keep the PDF as it is. The SDS sample does exactly this for its scanned sheet.

### verify_binder.py

```bash
.venv/bin/python scripts/verify_binder.py BINDER.pdf [--index BINDER-index.xlsx] [--pdf-folder DOCS]
```

Checks the page count, that sections and documents follow on with no gaps, that every bookmark and every clickable contents entry opens the right page, that every page number printed in the contents is right, that dividers and PENDING pages are where they should be, and that each document's first and last page match its source file. It also notes any source file that has changed since the build. Ends with `RESULT: all N checks passed.` Run it before every delivery.

### make_templates.py and make_samples.py

`make_templates.py` restores clean copies of the spreadsheet templates. `make_samples.py` rebuilds the samples (`--business` puts your name on the covers, `--only sds|om|submittal` does one set).

---

## Before you deliver

- [ ] `verify_binder.py` says all checks passed
- [ ] You opened the PDF and looked at the cover, contents, every divider, and every PENDING page
- [ ] Cover details are right (names, dates, revision); no placeholder text left
- [ ] SDS jobs: every REVIEW row is resolved or explained to the client; the client has confirmed the list
- [ ] Submittal jobs: the PM has reviewed the package
- [ ] File names follow the client's or general contractor's rules
- [ ] Deliverables saved outside this temporary container (download them or commit them to the client's private repo)

## Troubleshooting

| Problem | Fix |
|---|---|
| "file ... is not in ..." | Check the spelling in the index; the message suggests the closest file name |
| "password-protected" | Ask for an unlocked copy. Files that only restrict editing open fine. |
| "could not be read as a PDF" | Download the file again; or use `--missing placeholder` to build now and swap it in later |
| Contents run to several pages | Normal for big binders. Shorter titles and notes keep it compact; a section heading always stays with its first entry. |
| A character shows as "?" on the cover or contents | The built-in font covers Western European text only; bookmarks keep the original characters |
| Spreadsheet shows old ages | Ages use today's date when the file is opened in Excel, LibreOffice or Google Sheets |
| "Close it in Excel" / "close it in your PDF viewer" | The file is open in another program; close it and rerun |
| Missing package errors | Run `.venv/bin/pip install -r requirements.txt` again |

## Privacy

Client files are confidential. Keep each client in its own private folder or repo, use their documents only for their job, and never put real client documents in `samples/`. Before handling anyone else's files, check your Claude privacy settings (the playbook recommends turning off model training).
