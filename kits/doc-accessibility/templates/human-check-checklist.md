# Human check checklist (one per file)

Automated checks (triage_pdfs.py, veraPDF, PAC) find only part of the problems. A person does this check on every file before it is delivered, then records the results in the remediation log (`templates/remediation-log-template.xlsx`).

## What you need

- A Windows computer, or a Windows virtual machine.
- **NVDA**, the free screen reader (nvaccess.org).
- **Adobe Acrobat Reader** (free), to read PDFs with NVDA.
- **PAC**, the free PDF Accessibility Checker (pac.axes4.com), or the accessibility checker in Adobe Acrobat Pro.
- The free **Colour Contrast Analyser** (TPGi), for colour checks.
- For Word, Excel and PowerPoint files: the built-in Accessibility Checker (Review > Check Accessibility).

Set up Acrobat Reader once: Edit > Preferences > Reading. Leave "Override the reading order in tagged documents" unticked, and under Screen Reader Options choose to read the entire document.

## NVDA keys you will use

The NVDA key is Insert (or Caps Lock if you chose the laptop layout).

| Keys | What they do |
|---|---|
| NVDA+Down arrow | Read everything from here |
| Ctrl | Stop speaking |
| H, or 1 to 6 | Next heading, or next heading at that level |
| T, then Ctrl+Alt+arrow keys | Next table, then move cell by cell |
| G | Next image |
| K | Next link |
| L / I | Next list / next list item |
| F | Next form field |
| NVDA+F7 | List of headings, links and other elements |
| NVDA+T | Read the window title |
| NVDA+Space | Switch between browse mode and focus mode (for typing in forms) |

## The checks

File: ______________________  Checked by: ____________  Date: __________  NVDA version: ______  PAC version: ______

### 1. Automated checks first

- [ ] PAC: no failures in the PDF/UA and WCAG checks, or each failure written down with the reason. Save the PAC report with the file.
- [ ] veraPDF result recorded (`validate_pdfs.py`).

### 2. Document setup

- [ ] The title bar shows the document title, not the file name (NVDA+T).
- [ ] The document language is right. Passages in another language are tagged with their own language.
- [ ] Long documents have bookmarks that match the headings.
- [ ] No security setting blocks screen readers.

### 3. Reading order

- [ ] Read the whole file with NVDA+Down arrow. Everything is read once, in the order a sighted reader would follow.
- [ ] Columns are read one column at a time.
- [ ] Headers, footers, page numbers and decorative lines are not read in the middle of the text.

### 4. Headings and lists

- [ ] Pressing H moves through every visual heading, and only real headings.
- [ ] Heading levels make sense: the title is level 1, and levels do not jump (for example from 1 to 4).
- [ ] Lists are announced as lists, with the right number of items.

### 5. Images

- [ ] Every image that carries meaning has alt text that says what matters here ("Map of the new bus routes", not "image" or a file name).
- [ ] Charts have alt text, or nearby text, that gives the main point and the key numbers.
- [ ] Decorative images are not read at all.
- [ ] The client approved the alt text for complex charts, maps and diagrams.

### 6. Tables

- [ ] Data tables have header cells. NVDA reads the header when you move to a new cell (Ctrl+Alt+arrow keys).
- [ ] Tables used only for layout are not tagged as data tables.
- [ ] No empty rows or columns used just for spacing.
- [ ] Complex tables (two header rows, merged cells) read correctly, or were split or rebuilt.

### 7. Links

- [ ] Link text says where the link goes ("2026 fee schedule", not "click here").
- [ ] Every link works.

### 8. Forms

- [ ] Every field has a name that matches its visible label (press F and listen).
- [ ] The Tab key moves through the fields in the visual order.
- [ ] Required fields are marked in words, not only with colour or an unexplained asterisk.
- [ ] Check boxes and radio buttons are grouped with their question.
- [ ] You can fill in the form and save it in Acrobat Reader.

### 9. Text, colour and contrast

- [ ] OCR text matches the scan. Check names, numbers, dates and money amounts.
- [ ] No text exists only as a picture (logos are the exception).
- [ ] Information is not given by colour alone.
- [ ] Text contrast is at least 4.5:1, or 3:1 for large text (18 point, or 14 point bold).

### 10. Record it

- [ ] Remediation log row filled in: PAC result, each check (Pass, Fail, Not applicable), checked by, date and notes.
- [ ] Tool versions noted (NVDA, PAC or Acrobat).
- [ ] Wording: "checked on [date] with NVDA [version] and PAC [version]". Never "ADA compliant" or "certified".

## Word, Excel and PowerPoint files

- [ ] Run Review > Check Accessibility. Fix every error and warning, or note why not.
- [ ] Word: headings use heading styles; lists use the list buttons; tables have a header row (Table Design > Header Row, and Layout > Repeat Header Rows); images have alt text or are marked decorative; the title is set (File > Info > Properties); the language is right (Review > Language).
- [ ] Excel: every sheet has a clear name and no blank sheets are left; tables have a header row; no merged cells in data; charts have alt text.
- [ ] PowerPoint: every slide has a unique title; the reading order is right in the Selection Pane (Home > Arrange > Selection Pane, which reads from the bottom up); images have alt text.
- [ ] Then read the file with NVDA as above, or export a tagged PDF and check that.
