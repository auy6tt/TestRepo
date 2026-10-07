# Publisher Rescue starter kit

Everything you need to sell and deliver one service from day one: **rescuing Microsoft Publisher files**.

You take an organisation's folder of old `.pub` files and give back:

1. **A PDF archive**: every file as a searchable PDF, a preview picture of each, an index spreadsheet and a contact sheet (a web page of thumbnails they can search).
2. **Rebuilt templates**: the 5 to 20 layouts they reuse (newsletter, weekly bulletin, certificates, posters), rebuilt as editable Word or PowerPoint files.

The kit has the scripts that do the heavy lifting, three polished starter templates, an intake checklist, a delivery note, a finished sample job for a made-up parish to show prospects, and a Claude Code skill that runs a whole job with you.

This kit expands the [Rescuing Microsoft Publisher files](../../PLAYBOOK.md#publisher-rescue) idea in the playbook.

---

## Contents

- [Why now](#why-now)
- [The offer](#the-offer)
- [Who buys, and where to find them](#who-buys-and-where-to-find-them)
- [Price guide](#price-guide)
- [What is in this kit](#what-is-in-this-kit)
- [Set up (once per sandbox)](#set-up-once-per-sandbox)
- [Step-by-step: one job from start to finish](#step-by-step-one-job-from-start-to-finish)
- [Job checklist](#job-checklist)
- [Rules](#rules)
- [How to run each script](#how-to-run-each-script)
- [Using the Claude Code skill](#using-the-claude-code-skill)
- [What .pub conversion can and cannot do](#what-pub-conversion-can-and-cannot-do)
- [What was tested](#what-was-tested)
- [Troubleshooting](#troubleshooting)

---

## Why now

Microsoft is retiring Publisher. It has been reported that **from October 2026, Microsoft 365 subscribers can no longer open or edit .pub files**. Before you quote this to a client, check the current wording on Microsoft's own support site (search for "Publisher retirement"), and tell clients to check it too. Dates and details can change, and your credibility depends on getting them right.

Churches, schools, parent-teacher groups, clubs, small charities and local councils have years of newsletters, bulletins, flyers and certificates in `.pub` files. Most of them have no budget for a designer and no time to retype everything. They need two things: a way to keep reading the old files, and a way to keep making the new ones.

## The offer

Sell **"your archive plus your top templates"**, not "a perfect copy of every file".

| Part | What the client gets | Why they care |
| --- | --- | --- |
| PDF archive | One searchable PDF per `.pub` file (PDF/A, the archive standard), in the same folders as before. A preview picture of each. `index.xlsx` listing every file with its date, page count and status. `contact-sheet.html`: thumbnails they can browse, search and print. | They can find and read every old newsletter, forever, without Publisher. |
| Rebuilt templates | Their most-used layouts as Word (`.docx`) or PowerPoint (`.pptx`) files, built with named styles so anyone can edit them. | Next week's bulletin still gets made. |
| Delivery note | What they received, files that need attention, how to use the templates, and confirmation that their files will be deleted. | Clear hand-over, fewer support emails. |

A short pitch you can adapt:

> Microsoft is retiring Publisher, and your old .pub files may stop opening. I convert your whole archive into searchable PDFs with an index, and rebuild the layouts you reuse (newsletter, service sheet, certificates) as easy Word templates. Send me one file and I'll show you the result free.

## Who buys, and where to find them

| Buyer | What they have in Publisher | Where to reach them |
| --- | --- | --- |
| Church and parish administrators | Weekly bulletins, service sheets, parish magazines, rotas | Church-admin and church-communications groups on Facebook and forums, denominational newsletters |
| Dioceses, circuits, synods | The same, across many parishes | The diocesan communications or IT office. One deal can cover dozens of parishes. |
| School offices, PTAs and PTOs | Newsletters, certificates, event flyers | School-office and PTA groups, school business manager networks |
| School districts and groups of schools | All of the above, at many sites | District IT or communications departments |
| Clubs, small charities, town and parish councils | Newsletters, posters, membership cards, agendas | Local community groups, council clerk networks, charity forums, Nextdoor |

**Search for people already asking:** "can't open .pub file", "Publisher retirement", "convert Publisher to Word".

**Test it in one day:** offer "send me one .pub file and I'll send back a PDF and an editable Word version, free" in three church-admin or school-office groups. Use the sample in `samples/` as proof of your work.

## Price guide

| Item | Price |
| --- | --- |
| Archived file (PDF + preview + index row) | $0.50 to $2 per file |
| Rebuilt template | $25 to $75 per template |
| Typical organisation | about $150 to $600 |

Example packages:

| Package | Includes | Price |
| --- | --- | --- |
| Small | up to 100 files and 3 templates | $150 to $250 |
| Standard | up to 300 files and 6 templates | $300 to $450 |
| Large | up to 600 files and 10 templates | $550 to $650 |

- Count first, then quote: `convert_archive.py --survey` counts files, exact duplicates and dates (see below).
- Don't charge for exact duplicates. Clients notice and appreciate it.
- Dioceses and school districts: quote per site, with a discount for volume.
- Take a deposit (for example 50%) before you start.

## What is in this kit

```text
kits/publisher-rescue/
├── README.md                  this guide
├── requirements.txt           Python packages
├── .gitignore                 keeps jobs/ (client files) out of git
├── scripts/
│   ├── setup.sh               installs LibreOffice modules, fonts and Python packages
│   ├── convert_archive.py     .pub folder -> PDFs, previews, index.xlsx, contact sheet
│   ├── build_templates.py     builds the templates, intake checklist and delivery note
│   ├── check_render.py        converts your edited templates to PDF and page pictures
│   ├── make_booklet.py        turns a 4-page A5 bulletin into a print-ready folded booklet
│   ├── make_sample_archive.py makes the fictional sample "client files"
│   ├── build_samples.py       rebuilds the whole sample job in samples/
│   ├── office_tools.py        shared code: runs LibreOffice safely, reads PDFs
│   ├── docx_tools.py          shared code: Word formatting helpers
│   ├── artwork.py             shared code: picture placeholders and sample illustrations
│   └── sample-data/
│       └── st-aidans-wrenford.json   the sample's text, colours and logo
├── templates/                 blank starter templates (with a PDF preview of each)
│   ├── newsletter-two-column-A4.docx / -Letter.docx
│   ├── service-bulletin-A5-booklet.docx / -HalfLetter-booklet.docx
│   ├── certificate-of-achievement-A4.pptx / -Letter.pptx
│   ├── client-intake-checklist.docx
│   └── delivery-note.docx
└── samples/
    └── st-aidans-wrenford/    a complete FICTIONAL job (show this to prospects)
        ├── originals/         the "client's files" (stand-ins, see below)
        ├── archive/           PDFs, previews, index.xlsx, contact-sheet.html
        ├── templates/         the rebuilt templates, filled in, with PDFs
        └── delivery-note.docx and delivery-note.pdf
```

The Claude Code skill is in `.claude/skills/publisher-rescue/SKILL.md` at the root of this repository.

### The templates

All templates use Cambria for headings and Calibri for text. Both come with Microsoft Office and are available in Google Docs, so clients do not need to buy fonts. Every piece of text has a named style, so a client changes all headlines at once by changing one style.

- **Two-column newsletter** (Word, A4 and Letter). Masthead with logo, issue line, headlines, kickers, bylines, captions, pull quote, a "dates for your diary" box, notices and a contact box. Text flows between columns and pages by itself, with no linked text boxes.
- **Service bulletin** (Word). Four half-size pages (A5, or half Letter): cover, two pages of order of service with dot leaders, and a back page for the week's diary, notices and contacts. Print it as a folded booklet on A4 or Letter with `make_booklet.py` or the "Booklet" print option.
- **Certificate of achievement** (PowerPoint, A4 and Letter landscape). The border sits on the slide layout so it cannot be knocked out of place. Duplicate the slide for each person.
- **Client intake checklist** and **delivery note** (Word). The tick boxes can be clicked in Word.

To make a client's own versions, see [build_templates.py](#build_templatespy-templates-checklist-and-delivery-note).

### The sample job (for your portfolio)

`samples/st-aidans-wrenford/` is a complete job for **St Aidan's Church, Wrenford, a fictional parish**. All names are invented, the phone numbers are UK numbers reserved for drama, and the web addresses use example.org.

- `originals/` stands in for the client's archive. Real `.pub` files cannot be created without Publisher, so the stand-ins are Word, LibreOffice Draw and Impress files styled like old Publisher files. LibreOffice converts them exactly the way it converts `.pub` files. One file, `Old PC backup/Parish magazine March 2007.pub`, is deliberately damaged to show how a failure is reported.
- `archive/` is the output of `convert_archive.py`. Open `contact-sheet.html` in a browser and `index.xlsx` in Excel.
- `templates/` holds the rebuilt newsletter (2 pages), the Mothering Sunday bulletin (with a print-ready booklet PDF) and three certificates, all filled in.
- `delivery-note.pdf` is what the client receives with it.

To show your own name on the sample, change `"from"` and `"from_email"` in `scripts/sample-data/st-aidans-wrenford.json` and run `python scripts/build_samples.py`.

## Set up (once per sandbox)

Cloud sandboxes start fresh, so run this at the start of each session:

```bash
bash kits/publisher-rescue/scripts/setup.sh
source ~/.venvs/publisher-rescue/bin/activate
cd kits/publisher-rescue
```

`setup.sh` installs:

- **LibreOffice Draw, Writer and Impress.** Draw contains the Publisher import filter (it uses a library called libmspub). In this sandbox, LibreOffice came without these parts and could not open any document until they were installed.
- **libmspub-tools** (`pub2raw`), for checking `.pub` files that will not open.
- **Fonts** with the same letter widths as Calibri and Cambria (Carlito and Caladea), so page layouts match what clients see in Office.
- **Python packages** from `requirements.txt` into a virtual environment (change its location with `VENV=/path bash scripts/setup.sh`).

The scripts should also work on your own computer if LibreOffice and Python 3.9 or newer are installed, but they were tested only on Ubuntu Linux.

## Step-by-step: one job from start to finish

Each job lives in its own folder, `jobs/<client>/`, inside this kit. `jobs/` is git-ignored, so client files never end up in your repository.

1. **Intake.** Go through `templates/client-intake-checklist.docx` with the client: how many files, which layouts they reuse, paper size, logo, fonts, privacy, deadline.
2. **Get the files.** Ask for a shared folder link (not email attachments). Put the files in `jobs/<client>/originals/`. If your Claude Code session has Google Drive connected, Claude can copy them from a folder the client shared with you. Never edit the originals.
3. **Survey and quote.**
   ```bash
   python scripts/convert_archive.py jobs/stmarys/originals --survey
   ```
   This counts `.pub` files, duplicates, empty files and dates, and prints a price range for the archive part. Add the templates, send the quote, take the deposit.
4. **Convert.**
   ```bash
   python scripts/convert_archive.py jobs/stmarys/originals jobs/stmarys/archive \
       --title "St Mary's School: Publisher archive"
   ```
   About 1 to 3 seconds per file. If it stops, run the same command again: finished files are kept.
5. **Check the results.** Open `archive/contact-sheet.html` and choose "Need attention". Read the "Problem or note" column in `index.xlsx`. Compare a handful of previews with the originals (ask the client for screenshots or PDFs from Publisher if they still have it). Write down fonts that were replaced.
6. **Let the client choose templates.** Send them the contact sheet. They tick "Rebuild as template" on the layouts they reuse and press "Copy my ticks" to email you the list.
7. **Rebuild the templates.** Start from the kit's templates in the client's colours and logo:
   ```bash
   python scripts/build_templates.py --paper a4 --out jobs/stmarys/templates \
       --org "St Mary's School PTA" --primary 0B6E4F --accent E0A100 \
       --logo jobs/stmarys/logo.png --only newsletter,bulletin,certificate
   ```
   Then adjust them in Word or PowerPoint (or with Claude) to match the client's old layouts: section names, boxes, order of items. For layouts the kit does not cover (posters, menus, forms), start from the closest template and keep using styles.
8. **Check your templates.**
   ```bash
   python scripts/check_render.py jobs/stmarys/templates --out jobs/stmarys/render-check
   ```
   Look at every page picture. Fix text that spills onto an extra page. For a bulletin, make the print-ready booklet with `make_booklet.py`.
9. **Write the delivery note.** Either fill in `templates/delivery-note.docx` by hand, or copy the `delivery_note` part of `scripts/sample-data/st-aidans-wrenford.json` into `jobs/stmarys/job.json`, edit it, and run:
   ```bash
   python scripts/build_templates.py --only delivery --paper a4 \
       --content jobs/stmarys/job.json --summary jobs/stmarys/archive/summary.json \
       --out jobs/stmarys --pdf
   ```
   The `--summary` option fills in the numbers and the list of files that need attention.
10. **Deliver.** Zip `archive/`, `templates/` and the delivery note, and share them through the client's own folder:
    ```bash
    cd jobs/stmarys && zip -r stmarys-publisher-rescue.zip archive templates delivery-note.pdf delivery-note.docx
    ```
11. **Delete.** When the client confirms they have everything (we suggest within 7 days), delete every copy and tell them:
    ```bash
    rm -rf jobs/stmarys
    ```
12. **Ask for a testimonial** and a referral to the next parish, school or club.

## Job checklist

Copy this into your notes for each job.

- [ ] Intake checklist completed; client confirmed they may share the files
- [ ] Files in `jobs/<client>/originals/` (not in git, not edited)
- [ ] Survey run; quote sent; deposit received
- [ ] Archive converted; contact sheet and index opened
- [ ] Every "Failed" and "please check" file looked at; client asked for replacements if needed
- [ ] Previews spot-checked against originals; font substitutions noted
- [ ] Client's template choices received
- [ ] Templates rebuilt with the client's name, colours and logo; styles kept
- [ ] `check_render.py` run; every page looked at; nothing spills onto an extra page
- [ ] Templates opened once in Word or PowerPoint (if you have it) before delivery
- [ ] Delivery note written, with font substitutions and problem files listed
- [ ] Package delivered through the client's shared folder; final invoice sent
- [ ] Client files deleted; deletion confirmed to the client in writing
- [ ] Testimonial and referral asked for

## Rules

1. **Sell "archive plus top templates", not pixel-perfect copies.** Say up front that PDFs are faithful copies for reading, searching and printing, and that some fonts and effects will differ. Never promise every file will convert.
2. **Use substitute fonts where licences are an issue.** If an old file used a font the client has no licence for (often a paid font a past volunteer installed), use a standard or free font instead, for example Calibri, Cambria, Georgia, or an open-licence font. Never send font files you do not have the right to share. List every substitution in the delivery note.
3. **Delete client files after delivery.** Agree a date in the intake (for example within 7 days of delivery), delete every copy (sandbox, downloads, cloud folders), and confirm in writing. Keep only the delivery note and invoice.
4. **Keep client files out of git.** Work only in `jobs/`, which is git-ignored. Never paste personal details from client files into public places.
5. **Treat archives as personal data.** Newsletters and bulletins contain names, addresses, prayer requests and photos of children. Tell the client where the files are processed, and turn off model training in Claude's privacy settings before you handle anyone else's files.
6. **Never change the originals.** The scripts work on copies; keep it that way if you add your own steps.
7. **Be accurate about Microsoft's dates.** Say "reported" and point clients to Microsoft's own page.

## How to run each script

Activate the environment first (`source ~/.venvs/publisher-rescue/bin/activate`) and run commands from `kits/publisher-rescue/`. Every script has `--help`.

### `setup.sh`: one-time setup

```bash
bash scripts/setup.sh                                # default environment: ~/.venvs/publisher-rescue
VENV=/somewhere/else bash scripts/setup.sh           # choose another location
```

### `convert_archive.py`: the batch converter

```bash
python scripts/convert_archive.py INPUT [OUTPUT] [options]
```

| Option | What it does |
| --- | --- |
| `--survey` | Count files, duplicates, empty files and dates, print a price range. Converts nothing. |
| `--ext pub` | File types to convert (default `pub`). Also `word`, `slides`, `drawing`, `all`, or a list such as `pub,docx,odg`. |
| `--title "..."` | Title shown on the index and contact sheet. |
| `--timeout 180` | Seconds to wait for one file before giving up. |
| `--no-pdfa` | Make ordinary PDFs instead of PDF/A-2b. |
| `--preview-width 600` | Width of the preview pictures in pixels. |
| `--limit 20` | Only do the first 20 files (a quick trial). |
| `--overwrite` | Convert again even if a PDF from an earlier run exists. |
| `--soffice PATH` | Where LibreOffice is, if it is not found. |

What it does, for each file, one at a time:

- skips junk: Office lock files (`~$...`), Mac extras (`._...`, `__MACOSX`) and hidden files;
- refuses `.pub` files that do not start like a Publisher 98 or later file;
- copies the file to a temporary folder and converts the copy with LibreOffice, forcing the Publisher import filter for `.pub` files (without it, LibreOffice may open a damaged file as pages of garbage text);
- stops LibreOffice if it takes longer than the timeout;
- checks the PDF: page count, whether it has searchable text, whether the text looks garbled, which fonts were used;
- saves a PNG of the first page;
- notes exact duplicates.

Output folder:

```text
pdf/                 PDFs, in the same folders as the originals
previews/            first-page PNG pictures
index.xlsx           one row per file: original path, date modified, status, pages,
                     PDF link, preview link, searchable text, opening words, fonts,
                     problem or note, size; plus a Summary sheet
contact-sheet.html   thumbnails grouped by folder, with search, a "Need attention"
                     filter and "Rebuild as template" tick boxes
conversion-log.txt   what happened to each file, including LibreOffice's messages
summary.json         the counts and problem list, for the delivery note
```

Status values: **Converted**, **Converted - please check** (for example no searchable text, or text that looks garbled), **Failed**, **Skipped** (empty file).

### `build_templates.py`: templates, checklist and delivery note

```bash
python scripts/build_templates.py                            # blank templates into templates/ (A4 and Letter)
python scripts/build_templates.py --paper letter --out DIR \
    --org "Riverside Rotary Club" --primary 123B6D --accent D4A017 --logo logo.png
python scripts/build_templates.py --content scripts/sample-data/st-aidans-wrenford.json \
    --paper a4 --out DIR --pdf                               # filled with real text
```

| Option | What it does |
| --- | --- |
| `--paper a4\|letter\|both` | Paper size (default both). Bulletins use A5 or half Letter pages. |
| `--out DIR` | Where to save (default: the kit's `templates/` folder). |
| `--org`, `--primary`, `--accent`, `--heading-font`, `--body-font`, `--logo` | Client branding. Colours are hex codes such as `1F3A5F`. |
| `--content FILE.json` | Fill the templates with real text. Use `scripts/sample-data/st-aidans-wrenford.json` as the pattern; pictures can be file paths. |
| `--summary summary.json` | Fill the delivery note's numbers and problem list from a conversion. |
| `--only newsletter,bulletin,certificate,intake,delivery` | Build only some of them. |
| `--pdf` | Also save a PDF of each file (to check the layout or to send). |

### `check_render.py`: check edited templates

```bash
python scripts/check_render.py templates/newsletter-two-column-A4.docx
python scripts/check_render.py jobs/stmarys/templates --out jobs/stmarys/render-check --expect-pages 4
```

Converts each Word, PowerPoint or LibreOffice file to PDF, saves every page as a PNG, and lists fonts. Carlito and Caladea mean Calibri and Cambria (same letter widths). A "stand-in" font such as DejaVu means a font was missing here, so line breaks may differ on the client's computer.

### `make_booklet.py`: print-ready folded booklet

```bash
python scripts/make_booklet.py templates/service-bulletin-A5-booklet.pdf
```

Puts two half-size pages on each side of an A4 or Letter sheet in booklet order (4 pages: front 4|1, back 2|3). Print double-sided, flip on the short edge, at actual size, then fold.

### `build_samples.py` and `make_sample_archive.py`: the portfolio sample

```bash
python scripts/build_samples.py
```

Deletes and rebuilds `samples/st-aidans-wrenford/` (about 30 seconds): makes the stand-in originals, converts them, builds the filled templates and PDFs, the booklet and the delivery note.

### `artwork.py`: preview the built-in pictures

```bash
python scripts/artwork.py /tmp/artwork-preview
```

## Using the Claude Code skill

The skill at `.claude/skills/publisher-rescue/SKILL.md` walks Claude through a whole job using this kit: setup check, job folder, survey and quote, conversion, quality checks, template rebuilding, render checks, delivery note, packaging and deletion. Start it with:

```text
/publisher-rescue stmarys
```

or just ask, for example: "I have a new Publisher rescue job for St Mary's School. The files are in jobs/stmarys/originals."

## What .pub conversion can and cannot do

LibreOffice reads `.pub` files through **libmspub**, an open-source library (version 0.1.4 in Ubuntu 24.04). LibreOffice labels the filter "Microsoft Publisher 98-2010". Inside, libmspub recognises two families of files: Publisher 97 to 2000, and Publisher 2002 and later. Files from recent versions (up to Microsoft 365) belong to the second family and normally open, but always check the previews.

**Usually converts well**

- Text, as real, searchable text, with sizes, bold and italic
- Page size and the number of pages
- Pictures, simple shapes, lines and coloured boxes
- Basic tables

**Often differs, so warn clients**

- **Fonts.** Fonts that are not installed are replaced, which changes line breaks. Text can run past the edge of a box or onto fewer lines.
- **WordArt, shadows, gradients, transparency, BorderArt** (decorative page borders) and other effects can be simplified or missing.
- **Linked text boxes** (stories continued on another page) can break in different places.
- **Embedded objects** such as Excel charts can be missing.
- **Mail-merge and catalogue-merge fields** can come out as plain text or blank.
- **Non-Western text in older files** can come out garbled. LibreOffice's own test file showed Russian text as "Ðóññêèé òåêñò"; the converter flags this as "Text may be garbled".

**Does not convert**

- Files from Publisher 95 or earlier, and damaged files. The converter reports them as "Failed" with the reason.

When a page matters and the PDF is not good enough: ask the client for a PDF saved from Publisher (if anyone still has it working), or rebuild that page as a template.

## What was tested

Tested on 7 October 2026 in an Ubuntu 24.04 cloud sandbox with LibreOffice 24.2.7, libmspub 0.1.4, Python 3.11 and the packages in `requirements.txt`.

- **`.pub` import is verified.** A real Publisher file from LibreOffice's own test suite (`fdo59355-1.pub`) converted to a searchable 2-page A4 PDF/A through `convert_archive.py`. Its Russian text came out garbled (a known libmspub limit), which the converter flags.
- Files with a `.pub` name that are not Publisher files, a damaged Publisher file and an empty file were all reported cleanly. Without the forced Publisher filter, LibreOffice turned one of them into 12 pages of garbage text and hung on another, which is why the script forces it.
- The full pipeline (PDF/A, previews, index, contact sheet, duplicates, resuming, timeouts, odd file names) was tested on `.pub`, `.docx`, `.odt`, `.odg`, `.odp` and `.pptx` files.
- Every template was checked against the Office Open XML schemas, converted to PDF with LibreOffice and inspected page by page. Microsoft Word and PowerPoint were not available, so open each template once in Office before your first delivery.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Every file fails with "LibreOffice could not open this file" | LibreOffice Draw is missing. Run `scripts/setup.sh`. |
| LibreOffice not found | Install it with `setup.sh`, or pass `--soffice /path/to/soffice`. |
| One file keeps timing out | Try `--timeout 600`. If it still fails, ask the client for a PDF from Publisher. |
| Text looks different from the original | Fonts were replaced. Check the "Fonts in PDF" column, install fonts if the client has the right to use them, and note substitutions in the delivery note. |
| "Text may be garbled" | Older non-English files. Compare with a printout; retype the important pages if needed. |
| A rebuilt template spills onto an extra page | Shorten text or reduce a picture, then run `check_render.py` again. |
| The run stopped halfway | Run the same command again. Finished PDFs are kept. |
| Files disappeared after the session ended | Cloud sandboxes are temporary and `jobs/` is not saved in git. Deliver before you end the session, or work on your own computer. |
