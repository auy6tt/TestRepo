---
name: pdf-binder
description: Builds indexed, bookmarked PDF binders with the kit in kits/pdf-binder. Use for chemical safety data sheet (SDS) binders and chemical inventories for OSHA HazCom updates, and for construction submittal packages and operation and maintenance (O&M), handover or closeout binders. Merges PDFs with a cover, clickable contents, section dividers, bookmarks, page numbers and an index spreadsheet; reads SDS PDFs into inventory.xlsx (product, supplier, revision date, signal word, H-codes, pictograms) and flags old, missing or unclear sheets; keeps a submittal log; verifies the finished binder.
argument-hint: "[sds | submittal | handover | samples | setup]"
---

# PDF binder kit

KIT = `${CLAUDE_PROJECT_DIR}/kits/pdf-binder`. The full guide (offers, buyers, prices, every option) is `KIT/README.md`. Templates are in `KIT/templates/`. Samples are in `KIT/samples/`.

## Rules (never break these)

- Never write, edit, retype, summarise into a new sheet, or "correct" a safety data sheet or any manufacturer document. Merge them exactly as supplied. If one looks wrong, tell the user to ask the manufacturer for a corrected version.
- Never classify chemicals, judge hazards or give safety advice. H-codes and signal words in the inventory are copied from the sheets. Hazard questions go to the SDS, the manufacturer or the employer's safety adviser. A qualified person trains staff.
- The client (employer) confirms the on-site chemical list. Never present an unconfirmed list as final.
- Never certify that a submittal complies. A spec checklist only shows where each requirement appears; the subcontractor's project manager confirms, signs and stamps. Never add mark-ups to a datasheet unless the PM gave exact instructions.
- OSHA dates: tell the user to check osha.gov. The employer compliance date for single-substance chemicals is reported as 20 November 2026, with later dates for mixtures. Never use it to scare anyone.
- Client files are confidential. Keep each client in its own folder under `KIT/jobs/` (git ignores it; this repository is public). This container is temporary, so remind the user to download what they deliver. Never copy client documents into `KIT/samples/`.

## Setup (once per session)

```bash
cd "${CLAUDE_PROJECT_DIR}"
test -x kits/pdf-binder/.venv/bin/python || bash kits/setup.sh pdf-binder
cd kits/pdf-binder
.venv/bin/python tests/test_kit.py        # must end with "All tests passed."
```

The kit's Python is `KIT/.venv/bin/python` (the pdf-binder line of `bash kits/setup.sh --list`). `bash kits/setup.sh pdf-binder` is the usual setup route. If it is missing or fails, run `python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt` inside KIT. Run every script from KIT as `.venv/bin/python scripts/<name>.py`, never with a bare `python` or `python3` (they don't have the kit's packages). Each script has `--help`.

## Workflow A: SDS binder

1. Intake: go through `templates/intake-checklist-sds-binder.md` with the user. Collect shelf photos, purchase records and the old binder.
2. Make a job folder in KIT's `jobs/` folder (ignored by git), e.g. `JOB=jobs/<client>` with `sds/`, `output/`, a copy of `templates/sds-site-list-template.xlsx` as `site-list.xlsx`, and a copy of `templates/binder-cover-sds.toml` as `cover.toml`.
3. Draft the on-site list from the photos and records (one row per product, name as on the label, manufacturer, location). Mark it as a draft for the client to confirm.
4. The user downloads the current SDS PDFs (most websites are blocked in the sandbox) into `$JOB/sds/`. Never generate or retype a sheet.
5. Read the sheets:
   ```bash
   .venv/bin/python scripts/extract_sds.py --sds-folder $JOB/sds --site-list $JOB/site-list.xlsx \
       --out $JOB/output/inventory.xlsx --group-by location --client "<Client name>"
   ```
6. Review every row whose Status is not OK (read the Inventory sheet with openpyxl, `data_only=True`):
   - REVIEW: open the PDF named in "SDS file" (the Read tool shows PDF pages, including scans) and compare with the amber/red cells and the Review notes. Record what the sheet actually says in `$JOB/manual-entries.csv` (format: `templates/sds-manual-entries-template.csv`; fields product, manufacturer, date, signal word, codes, pictograms, version; add `reviewed,yes` when the whole sheet is checked). Rerun step 5 with `--manual $JOB/manual-entries.csv`. Don't hand-edit inventory.xlsx; reruns would overwrite it.
   - CHECK FOR NEWER SDS, REPLACE: OLD FORMAT, MISSING SDS: list them for the user to request current sheets from the manufacturer or supplier.
   - NOT ON SITE LIST: ask the user to check with the client.
   Report what you found in plain words. Don't guess values you can't read.
7. The client confirms the list (the "Chemical List" sheet). Note who and when for the cover.
8. Check the "Binder Index" sheet (titles, sections, include yes/no). Fill in `$JOB/cover.toml`. Build without page stamps, so every sheet stays as published:
   ```bash
   .venv/bin/python scripts/build_binder.py --pdf-folder $JOB/sds --index $JOB/output/inventory.xlsx \
       --sheet "Binder Index" --cover $JOB/cover.toml --out $JOB/output/<Client>_SDS-Binder.pdf
   ```
9. Verify (below). Deliver the binder PDF, inventory.xlsx and the binder's `-index.xlsx`. Optional extra: adapt `templates/hazcom-written-program-outline.md` from the client's answers, keeping it marked as a draft for the employer to adapt.

## Workflow B: submittal package or O&M / handover binder

1. Intake: `templates/intake-checklist-submittal-handover.md`. Get the project's submittal and closeout rules, the required order and tab names, the GC's cover or transmittal form, and every document.
2. Job folder in KIT's `jobs/` folder (ignored by git), e.g. `JOB=jobs/<client>`: `docs/` (all PDFs), `index.xlsx` (copy of `templates/binder-index-template.xlsx`), `cover.toml` (copy of `templates/binder-cover-submittal.toml` or `binder-cover-handover.toml`), `output/`.
3. Fill the index in the required order: section, title, file, order, notes; `pages` (e.g. `3-5`) to take only some pages of a catalogue; blank `file` = PENDING placeholder page; rows starting with EXAMPLE are ignored.
4. Build:
   ```bash
   .venv/bin/python scripts/build_binder.py --pdf-folder $JOB/docs --index $JOB/index.xlsx \
       --cover $JOB/cover.toml --out $JOB/output/<name>.pdf --page-numbers
   ```
   Small submittal: add `--no-dividers --tabs none`. "Tab A, B, C": `--tabs letters --section-word Tab`. A missing or unreadable file stops the build with a list of problems; `--missing placeholder` builds anyway with PENDING pages.
5. Verify (below). Add or update the row in the submittal log (`templates/submittal-log.xlsx`; one row per submittal and per resubmittal; don't type over the formula columns "Days in review" and "Late?").
6. Tell the user the package goes to the subcontractor's PM to review and sign before it is sent to the GC.

## Verify before saying a binder is done

```bash
.venv/bin/python scripts/verify_binder.py <binder>.pdf
```

It must end with `RESULT: all N checks passed.` Then look at the result yourself: render the cover, the contents and one divider to images (pypdfium2 is installed with pdfplumber) and view them, and read the build warnings. Report the page count, sections, pending documents and any warnings to the user.

## Samples

`.venv/bin/python scripts/make_samples.py --business "<user's business name>"` rebuilds all three portfolio samples (fake, watermarked inputs) and verifies them. `.venv/bin/python scripts/make_templates.py` restores clean spreadsheet and CSV templates.

## Quick fixes

- "is not in <folder>. Did you mean ...": fix the file name in the index.
- "password-protected": ask for an unlocked copy (files that only restrict editing open fine).
- Pictograms "Not named in text" is normal: most sheets show them as images.
- "?" on generated pages: the built-in font covers Western European text only; bookmarks keep the original.
