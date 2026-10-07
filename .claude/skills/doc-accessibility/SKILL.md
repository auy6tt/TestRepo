---
name: doc-accessibility
description: Runs the document accessibility service in kits/doc-accessibility. Crawls a client's website for PDF, Word, PowerPoint and Excel files, triages each one (tagged or untagged, real text or scanned, title, language, forms) into inventory.xlsx and a client-facing "Document accessibility snapshot" report, applies safe fixes (title, language, OCR), rebuilds files as structured Word and exports tagged PDFs with LibreOffice, validates with veraPDF and fills the remediation log. Use when the user mentions document or PDF accessibility, PDF remediation, tagged PDFs, the ADA Title II web rule, Section 504, the European Accessibility Act, a document inventory or snapshot for a town, county, school district, health provider or business, or asks for a cold email to an ADA coordinator.
---

# Document accessibility service

Kit: `${CLAUDE_PROJECT_DIR}/kits/doc-accessibility`. Its README has the offer, prices, process and rules. Templates are in `templates/`, scripts in `scripts/`, a full worked example in `samples/` (fictional town).

## Rules (always)

- Never write or imply "ADA compliant", "WCAG compliant", "certified" or "guaranteed", in any file, email or message. Deliver test results and a log, and write "checked on [date] with [tools]".
- Automated checks are not enough. Every fixed file needs a person to check reading order, alt text, tables and forms with NVDA plus PAC or Acrobat on Windows (`templates/human-check-checklist.md`). Never fill the human-check columns of the log for checks nobody did.
- Exceptions (archived content and others) are decided by the client's ADA coordinator or lawyer. Call files "archive candidates", nothing stronger.
- Deadlines: ADA Title II requires WCAG 2.1 AA; reported dates are 26 April 2027 (entities serving 50,000+) and 26 April 2028 (smaller ones). Always add "verify current dates".
- Crawl only sites the user says the client has agreed to. Keep the default delay (1 second or more), respect robots.txt, and put the user's contact in `--user-agent`. For prospects, at most a light `--depth 1` look.
- Keep client files out of this kit and out of public repos: use a client folder the user names (suggest `~/clients/<client-name>/`).
- Do not change the meaning, numbers or names in client documents. Draft alt text for complex images and ask the client to approve it.

## Setup (once per session)

```sh
PY=${DOC_A11Y_VENV:-$HOME/.venvs/doc-accessibility}/bin/python
K=${CLAUDE_PROJECT_DIR}/kits/doc-accessibility/scripts
test -x "$PY" || bash "$K/setup.sh" --verapdf
```

If the crawler cannot reach the client's site (connection refused, 403 from the proxy), tell the user that this environment's network policy blocks the domain and that they can allow it under Network access in the environment settings (cloud environment menu in the session title bar > Edit > Allowed domains). Name the exact hosts. Do not try to work around it.

## Step 1: snapshot (inventory and report)

Ask for, or confirm: start URL, client name, sector (`us-public`, `us-health` or `eu`), any extra document hosts, sections to skip, the user's name and contact, and the client folder `C`.

```sh
$PY $K/crawl_documents.py <start-url> --out $C/crawl --download $C/downloads --sitemap \
    --user-agent "DocInventory/1.0 (+mailto:<user email>)" [--also-download-from <host>] [--exclude "calendar"]
$PY $K/triage_pdfs.py $C/downloads --crawl $C/crawl/documents.csv --out $C/inventory --client "<client>"
```

Then review before reporting:

1. Read `$C/crawl/crawl_summary.md` (page limit hit? robots.txt notes? broken links?).
2. Read `$C/inventory/summary.md`. Open a few files to confirm the results (for example `$PY $K/triage_pdfs.py <file>`).
3. If a suggested action looks wrong, edit the "Suggested action" or "Priority" cell in `inventory.xlsx` (openpyxl) and tell the user what you changed and why.

```sh
$PY $K/make_report.py --inventory $C/inventory/inventory.xlsx --crawl-summary $C/crawl/crawl_summary.json \
    --client "<client>" --prepared-by "<name>" --contact "<contact>" --sector <sector> \
    --out $C/report/document-snapshot.docx --pdf
```

Read the finished report (render pages with `pdftoppm -png -r 60` and look at them). Report to the user: the key numbers, the high-priority files, the estimate, and anything that needs their judgement.

## Step 2: fixing

1. Safe quick fixes. Suggest titles first, review them (use the first-page text column to write real titles), then apply:
   ```sh
   $PY $K/fix_basics.py $C/downloads --crawl $C/crawl/documents.csv --suggest-titles $C/titles.csv
   $PY $K/fix_basics.py $C/downloads --out $C/basic-fixes --titles $C/titles.csv \
       --inventory $C/inventory/inventory.xlsx --lang en-US --ocr
   ```
2. Real fixes. Prefer the client's Word file. If there is none, rebuild the document as a structured .docx with python-docx and the helpers in `$K/office_helpers.py` (`set_properties`, `add_table` with a header row, `add_picture` with alt text): real heading styles, real lists, table header rows, alt text, title and language. Keep the text identical to the original and tell the user to compare them.
   ```sh
   $PY $K/docx_to_tagged_pdf.py $C/word/<file>.docx --out $C/fixed --compare $C/downloads/<file>.pdf --validate
   ```
   Scans: OCR, check the text against the image, then rebuild. Forms: recommend Acrobat Pro or an accessible web form. Short simple files: offer an HTML page.
3. Validate and log:
   ```sh
   $PY $K/validate_pdfs.py $C/fixed --out $C/fixed
   $PY $K/make_remediation_log.py --before $C/downloads --after $C/fixed --out $C/remediation-log.xlsx --work "<what was done>" --validate
   ```
4. Tell the user which files are ready for the human check, and hand them `templates/human-check-checklist.md`.

## Selling

- Cold email: `templates/cold-email-ada-coordinator.md`. Fill in one real detail about the prospect's site; keep it under 150 words; no scare tactics.
- Prices (from the README): snapshot $300 to $1,500 by size; fixing $5 to $25 per page by complexity; monthly upkeep for new agendas and minutes.
- Portfolio: `samples/report/fernwick-document-snapshot.pdf` and `samples/fixes/before-after/comparison.md`. Always say the town is fictional.

## Demo and troubleshooting

- `$PY $K/run_sample_demo.py --rebuild` runs everything on the fictional site (local server, no network needed).
- "source file could not be loaded" from LibreOffice: Writer is missing; run `setup.sh` (installs `libreoffice-writer`).
- OCR skipped: Tesseract is missing; run `setup.sh`.
- veraPDF not found: `bash $K/setup.sh --verapdf`, or set `VERAPDF_DIR`.
