---
name: publisher-rescue
description: Run a paid Microsoft Publisher (.pub) rescue job with the kit in kits/publisher-rescue. Surveys a client's .pub archive and prices it, batch-converts it to searchable PDF/A files with preview pictures, index.xlsx and a contact sheet, rebuilds the client's most-used layouts (newsletter, service bulletin, certificate and similar) as editable Word or PowerPoint templates, checks the renders, writes the delivery note, packages the delivery and deletes the client's files afterwards. Use when the user mentions Publisher or .pub files, converting or archiving old newsletters, bulletins, flyers or certificates, or rebuilding Publisher templates for a church, school, PTA, club, charity or council.
argument-hint: "[client-name or folder with the client's files]"
---

# Publisher rescue job

You are running one client job with the kit in `kits/publisher-rescue/` (in the project root). The business side (offer, prices, buyers, rules, limits) is in `kits/publisher-rescue/README.md`; read the "Rules" and "What .pub conversion can and cannot do" sections before you talk to the user about results.

Client or folder given: `$ARGUMENTS` (if empty, ask the user for the client's name and where the files are).

## Rules that always apply

- Never modify, rename or move the client's original files. Work in `kits/publisher-rescue/jobs/<client-slug>/`, which is git-ignored.
- Never `git add`, commit or push anything from `jobs/`, and never paste personal details from client files anywhere public.
- Promise "archive plus top templates", never pixel-perfect copies.
- Use a standard or free substitute when the client has no licence for a font, and record every substitution for the delivery note.
- Delete the job folder after delivery, but only when the user confirms the client has everything.
- Say "reported" about Microsoft's Publisher retirement dates and point to Microsoft's own support pages.

## 1. Check the tools

The kit's Python is `~/.venvs/publisher-rescue/bin/python` (`bash kits/setup.sh --list` shows it). Run every script below with that full path. A bare `python` or `python3` is the system Python, which has none of the kit's packages, and activating the environment does not carry over between commands.

```bash
cd kits/publisher-rescue
~/.venvs/publisher-rescue/bin/python -c "import docx, pptx, openpyxl, pymupdf, PIL; print('Python packages: OK')"
soffice --version
ls /usr/lib/libreoffice/program/libwpftdrawlo.so   # LibreOffice Draw: holds the Publisher filter
```

If any of these fails, run `bash kits/setup.sh publisher-rescue` from the project root. This is the usual setup route: it installs LibreOffice Draw, the fonts and the kit's Python. Then check again. (`bash kits/publisher-rescue/scripts/setup.sh` installs the same things for this kit only.)

## 2. Set up the job folder

```bash
JOB=jobs/<client-slug>          # lowercase, hyphens, e.g. jobs/st-marys-pta
mkdir -p "$JOB/originals" "$JOB/archive" "$JOB/templates"
```

All commands in this skill run from `kits/publisher-rescue/`. Shell variables and the working directory may not carry over between commands, so start each command with `cd kits/publisher-rescue && JOB=jobs/<client-slug> && ...` from the project root, or write the paths out in full.

Ask the user how the files will arrive (upload, a shared cloud folder through a connected drive, a zip). Put them in `$JOB/originals/` exactly as received. Unzip archives there. If the user has an intake checklist filled in (`templates/client-intake-checklist.docx`), read it for paper size, colours, logo, fonts and deadline.

## 3. Survey and quote

```bash
~/.venvs/publisher-rescue/bin/python scripts/convert_archive.py "$JOB/originals" --survey
```

Report: number of `.pub` files, duplicates, empty files, files that do not look like Publisher files, date range, and the price range printed. Add templates at \$25 to \$75 each (README "Price guide"). Draft a short quote message for the user to send. Do not start converting a large archive until the user says the quote is accepted, unless they asked you to go ahead.

## 4. Convert

```bash
~/.venvs/publisher-rescue/bin/python scripts/convert_archive.py "$JOB/originals" "$JOB/archive" --title "<Client>: Publisher archive"
```

- Add `--ext all` only if the client also wants Word, PowerPoint or drawing files archived (priced separately).
- For more than about 200 files, run it in the background and check progress; it prints one line per file. If it stops, run the same command again: finished PDFs are kept.
- A trial run on a few files: add `--limit 10`.

## 5. Check the results

1. Read `$JOB/archive/summary.json` for counts, `failed_files` and `check_files`.
2. For each failed `.pub` file, run `pub2raw "<file>" | head -20`. "ERROR: Unsupported file format" or a crash means libmspub cannot read it: the client needs another copy or a PDF saved from Publisher.
3. Look at preview pictures (read the PNGs in `$JOB/archive/previews/`): every file marked "please check", and a sample of about one in ten of the rest. Look for missing pictures, text running off the page, odd fonts, blank pages.
4. Read the "Fonts in PDF" and "Problem or note" columns of `index.xlsx`:

   ```bash
   ~/.venvs/publisher-rescue/bin/python -c "
   from openpyxl import load_workbook
   for row in load_workbook('$JOB/archive/index.xlsx')['Index'].iter_rows(min_row=2, values_only=True):
       print(row[1], '|', row[10], '|', row[11])"
   ```

   Any font in "Fonts in PDF" that is not the original font and not a same-width substitute is a stand-in. Same-width substitutes: Carlito (Calibri), Caladea (Cambria), Liberation Sans, Serif and Mono (Arial, Times New Roman, Courier New), Nimbus Sans, Roman and Mono PS (Helvetica, Times, Courier). Stand-ins include DejaVu, Noto, FreeSans, FreeSerif and the URW fonts Z003, C059, P052, URW Bookman and URW Gothic. Some look nothing like the original: Comic Sans MS, for example, comes out in Z003, a script font. The converter writes "Font replaced" in "Problem or note" for the stand-ins it knows, and `summary.json` lists them under `stand_in_fonts`. List every stand-in in `delivery_note.fonts`: which file, which font, and how it looks now.
5. Tell the user what you found in plain words, with file names, and what you suggest.

## 6. Rebuild the templates

1. Get the client's choices: the ticked list from `contact-sheet.html` ("Copy my ticks"), or ask the user which layouts they reuse.
2. Look at the PDF previews of those originals so the rebuild keeps their structure: masthead, sections, boxes, order of items.
3. Start from the kit's templates in the client's branding:

   ```bash
   ~/.venvs/publisher-rescue/bin/python scripts/build_templates.py --paper a4 --out "$JOB/templates" \
       --org "<Client name>" --primary <hex> --accent <hex> --logo "$JOB/logo.png" \
       --only newsletter,bulletin,certificate
   ```

   Use `--paper letter` for US and Canadian clients. Leave out the logo if there is none.
4. To fill templates with the client's real text, copy `scripts/sample-data/st-aidans-wrenford.json` to `$JOB/content.json`, replace the content, and add `--content "$JOB/content.json"`. Pictures can be file paths relative to that JSON file.
5. For layouts the kit does not cover (posters, menus, forms, membership cards), write a small python-docx or python-pptx script in `$JOB/` that follows `build_templates.py`: named paragraph styles instead of direct formatting, the `docx_tools.py` helpers for borders, shading and columns, and fonts the client owns (Calibri and Cambria by default).
6. Keep the client's own wording, but never copy text or pictures the client does not own the rights to.

## 7. Check every template

```bash
~/.venvs/publisher-rescue/bin/python scripts/check_render.py "$JOB/templates" --out "$JOB/render-check"
```

Read the page pictures it saves. Fix anything that spills onto an extra page, overlaps or looks cramped, then check again. A "CHECK: some text used a stand-in font" line means a font is missing here: use a font the client has, or note it for the delivery note. A service bulletin must have exactly 4 pages. Check it on its own, because `--expect-pages` applies to every file you give it:

```bash
~/.venvs/publisher-rescue/bin/python scripts/check_render.py "$JOB/templates/<bulletin>.docx" --out "$JOB/render-check" --expect-pages 4
```

Then make the print-ready booklet from its PDF:

```bash
~/.venvs/publisher-rescue/bin/python scripts/make_booklet.py "$JOB/render-check/<bulletin>.pdf" -o "$JOB/templates/<bulletin>-print-booklet.pdf"
```

## 8. Delivery note and package

1. Create `$JOB/job.json` with a `delivery_note` section shaped like the one in `scripts/sample-data/st-aidans-wrenford.json`, wrapped as `{"delivery_note": {...}}`: client, contact, the user's name and email, date, reference, the templates delivered, font substitutions, `delete_by` date and support days. Ask the user for anything you do not know; never invent their details.
2. Build it:

   ```bash
   ~/.venvs/publisher-rescue/bin/python scripts/build_templates.py --only delivery --paper a4 --content "$JOB/job.json" \
       --summary "$JOB/archive/summary.json" --out "$JOB" --pdf
   ```

3. Package:

   ```bash
   cd "$JOB" && zip -r "<client-slug>-publisher-rescue.zip" archive templates delivery-note.pdf delivery-note.docx
   ```

4. Tell the user where the zip is and remind them to deliver it through the client's own shared folder, not git. Draft a short hand-over email that points to the contact sheet, the index and the templates.

## 9. Delete the client's files

Only after the user confirms the client has everything:

```bash
rm -rf "jobs/<client-slug>"      # from kits/publisher-rescue/
```

Confirm the folder is gone, then draft a one-line message to the client confirming deletion and the date.

## Other tasks

- **Put the user's name on the portfolio sample:** change `"from"` and `"from_email"` in the `"delivery_note"` section of `scripts/sample-data/st-aidans-wrenford.json`, then run `~/.venvs/publisher-rescue/bin/python scripts/build_samples.py` from `kits/publisher-rescue/`. It deletes and rebuilds `samples/st-aidans-wrenford/` (about 30 seconds).
- Every script prints its options with `--help` and does nothing else.

## What to report back to the user at each stage

- Counts (files, converted, needs checking, failed, pages) and the price range.
- Files that need attention, each with the reason and a suggestion.
- Font substitutions.
- Where the outputs are, and what still needs the user's decision.
