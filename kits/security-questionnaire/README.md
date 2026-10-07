# Security questionnaire kit

Answer security questionnaires for small B2B software companies that have no security lead, using **only their own policies and documents**, and leave them with a reusable answer library. The scripts do the slow parts (finding the source text, matching questions, filling the buyer's spreadsheet without breaking it). You and the client's technical owner make every judgement.

- **Portfolio sample:** [`samples/output/`](samples/output/). Open [`cobalt-ridge-supplier-security-questionnaire_DRAFT2.pdf`](samples/output/cobalt-ridge-supplier-security-questionnaire_DRAFT2.pdf) to see a filled questionnaire and its review sheet. Everything in `samples/` is fictional. To put your name on it, see [Put your name on the sample](#put-your-name-on-the-sample).
- **Claude Code skill:** [`.claude/skills/security-questionnaire/SKILL.md`](../../.claude/skills/security-questionnaire/SKILL.md). Ask Claude to "answer this security questionnaire" and it follows the process below.

## The offer

> I fill in your customer's security questionnaire from your own policies, in their spreadsheet, in 3 business days. Every answer cites its source, gaps come back to you as a short question list, and you keep an answer library that makes the next one fast. Fixed price.

What the client gets:

1. The buyer's questionnaire, filled in their own file and formatting, ready to send.
2. A review sheet: every answer with its source document and section, and a list of what still needs their input.
3. An answer library (Excel): approved answers with sources, owner and review dates, reusable for every future questionnaire.

## Who buys, and where to find them

**Buyers:** founders and CTOs of 5 to 50 person B2B software companies whose first larger customers send a security questionnaire (SIG Lite, CAIQ-style or the customer's own spreadsheet). They have policies, or some, but nobody whose job is security. The questionnaire is blocking revenue, so they want it gone this week.

- **LinkedIn.** Search posts for "security questionnaire", "vendor assessment", "security review" and "SOC 2" from founders and CTOs. Comment with something useful first (for example, "answer from your existing policies, and say 'not yet' rather than overclaiming"). Then message with the offer. Your fictional sample is your proof.
- **Indie Hackers.** Founders who post about landing their first enterprise or mid-market customer are about to get a questionnaire. Reply with practical tips; link your sample when asked.
- **r/SaaS.** Answer questions about enterprise deals and security reviews. Read the subreddit rules on self-promotion before mentioning your service, and never spam.
- **Referral partners: SOC 2 consultants, vCISOs and compliance-software implementers.** They don't want small one-off questionnaire jobs, and their clients get questionnaires every month. Offer a referral fee (10 to 20%) or white-label work. One partner can send you steady work.

Short first message:

```text
Hi [name], saw you're closing [customer]. If their security questionnaire lands on your desk: I fill these in from your existing policies, in their spreadsheet, with every answer sourced and gaps flagged for you. Fixed price, about 3 days. Happy to show a sample (fictional company).
```

## Price guide

| Job | Price | Notes |
|---|---|---|
| Short custom questionnaire (up to 60 questions) | $250 to $400 | First job includes building the answer library |
| Medium (60 to 150 questions) | $400 to $800 | |
| SIG Lite, CAIQ-style or large custom (150+) | $800 to $1,500 | Allow more client time for gaps |
| Monthly retainer | $300 to $600 a month | Up to 2 questionnaires, library kept current, faster turnaround |
| Rush (under 48 hours) | +30% | Only if the client can answer gap questions quickly |

Estimates from the October 2026 research; check your market.

Start at the low end for your first three clients in exchange for a testimonial. The library makes repeat work faster, which is where the retainer pays.

## The rules (not negotiable)

1. **Answers are the client's statements to its customer.** Use only the client's documents and their written answers. Never invent a control, a date, a number, a tool or a certification. If the documents are silent, the answer is **NEEDS CLIENT INPUT**.
2. **Every answer cites its source:** document and section, or "Written answers from [name], [date]". No source, no answer.
3. **The client's technical owner reviews and signs off** every answer before it goes to the buyer (see `templates/cover_note.md`).
4. **You are not an auditor.** Never say or imply that you certify, audit or attest anything. Never write "compliant with X" or "certified" unless the client has the certificate or report.
5. **Confidential handling.** NDA first. One folder per client under `clients/` (git ignores it). Never commit client files, never paste them anywhere outside the NDA, and delete them when the engagement ends. Tell clients you use AI-assisted tools with model training turned off.
6. **"No" and "not yet" are good answers.** An honest gap is better for the client than an overclaim the buyer later finds out about.

## How the work goes

Commands run from `kits/security-questionnaire/` with the environment activated (see [Setup](#setup)).

1. **Intake.** Use `templates/client_intake_checklist.md`: NDA, deadline, technical owner, the questionnaire file, and every relevant document. Quote with `templates/fixed_price_offer.md`.
2. **Set up the client folder.** `clients/<client>/docs/` for their documents, `clients/<client>/` for the library and questionnaire files. Git ignores `clients/`. Cloud sessions are temporary: download what you deliver.
3. **Build the draft library.**
   `python scripts/build_library.py --docs clients/acme/docs --out clients/acme/answer_library.xlsx --client "Acme" --owner "Jo Smith, CTO"`
   Every seed question gets the best matching passage from the client's documents (document, section, excerpt) and Status **Draft**, or **NEEDS CLIENT INPUT** when nothing matches.
4. **Write the answers.** For each Draft row, read the cited section (and the full document if needed) and write the answer using only what it says. Watch for traps: text about the client's *vendors* is not evidence about the client ("we review our vendors' SOC 2 reports" does not mean the client has one). If the source doesn't support an answer, set NEEDS CLIENT INPUT. Fill Short Answer, Source Document, Source Section, Source Excerpt and Confidence.
5. **Ask about the gaps.** `python scripts/build_library.py --check clients/acme/answer_library.xlsx --gaps clients/acme/questions_for_client.md` writes the open questions as a checklist to send. Record the replies as a dated document and cite it.
6. **Client approves the library.** Go through it with the technical owner. Set Status to Approved with Owner and Last Reviewed. Run `--check` again: it must show no errors.
7. **Fill the questionnaire.** Try `--dry-run` first to see the columns it found, then:
   `python scripts/fill_questionnaire.py clients/acme/buyer.xlsx --library clients/acme/answer_library.xlsx`
   This writes `clients/acme/buyer_DRAFT.xlsx` next to the original (never changing the original) with a review sheet.
8. **Your review pass.** Work through the review sheet: NEEDS CLIENT INPUT first, then CHECK, then read every OK answer. Fix a wrong match by typing the right library ID in "Use library ID", then run the fill again on the **original** file: `python scripts/fill_questionnaire.py clients/acme/buyer.xlsx --library clients/acme/answer_library.xlsx --use-review clients/acme/buyer_DRAFT.xlsx --out clients/acme/buyer_DRAFT2.xlsx`. Add the buyer's wording to that entry's Alternate Phrasings so it matches next time. Edit two-part questions by hand.
9. **Client review and sign-off.** Send the draft with part A of `templates/cover_note.md`. Put their answers into the library first, then refill the same way (`--use-review` keeps your choices, notes and Resolved marks). Get the sign-off.
10. **Finalise and deliver.** `python scripts/fill_questionnaire.py --finalize clients/acme/buyer_DRAFT2.xlsx --out clients/acme/buyer_FINAL.xlsx` refuses while any NEEDS CLIENT INPUT text remains or any CHECK/NEEDS row isn't marked Resolved = Y, then removes the review sheet. Send it with part B of the cover note and the updated library.
11. **Close out.** Log changes on the library's Change Log sheet. Delete the client's files when the engagement ends (or keep them in their folder while on retainer).

## Quality checklist (before anything leaves your hands)

- [ ] Every answer was read by a person, not just the CHECK ones.
- [ ] Every answer has a source; every source really says it (open the document and check).
- [ ] No answer claims more than its source: watch "all", "always", "never", "fully", "certified", "compliant". `--check` warns about these words.
- [ ] No certifications, audit reports, pen-test dates, tools or numbers that aren't in a source.
- [ ] Yes/No matches the answer text, and the question's direction ("Are shared accounts used?" needs "No").
- [ ] Two-part questions answer both parts (or say what's missing).
- [ ] Nothing confidential the client asked to keep out (hostnames, staff names, internal policy names if they said no).
- [ ] No "NEEDS CLIENT INPUT" left in the final file, and the review sheet is removed (`--finalize` checks both).
- [ ] The technical owner's sign-off is saved.
- [ ] Library updated: new answers Approved with owner and date, buyer phrasings added, Change Log filled in.

## Setup

You need Python 3.10 or newer. Cloud sessions start from a clean machine, so do this at the start of each session. From the repository root:

```sh
bash kits/setup.sh security-questionnaire
```

That creates the Python environment at `~/.venvs/security-questionnaire` (and installs LibreOffice and other system tools the kits share). To do it by hand instead, on any computer:

```sh
python3 -m venv ~/.venvs/security-questionnaire
~/.venvs/security-questionnaire/bin/pip install -r kits/security-questionnaire/requirements.txt
```

Run the scripts with `~/.venvs/security-questionnaire/bin/python` (`bash kits/setup.sh --list` shows it), or activate the environment and use `python`, as in the examples below. LibreOffice is optional: it's only used to open `.xls` and `.ods` questionnaires.

## The scripts

All commands below are run from `kits/security-questionnaire/`, with the environment activated (`source ~/.venvs/security-questionnaire/bin/activate`). Client files always go in `clients/<client>/`, which git ignores. Replace `<client>` with the client's folder name, for example `acme`.

### `scripts/build_library.py`: draft the answer library from client documents

```sh
python scripts/build_library.py --docs clients/<client>/docs --out clients/<client>/answer_library.xlsx [--client NAME] [--owner "Name, Title"] [--gaps clients/<client>/questions_for_client.md]
python scripts/build_library.py --check clients/<client>/answer_library.xlsx [--gaps clients/<client>/questions_for_client.md]
python scripts/build_library.py --blank templates/answer_library.xlsx
```

- Reads `.md`, `.txt`, `.docx` and `.pdf` files (subfolders too). `.doc`, `.odt` and `.rtf` are skipped with the LibreOffice command to convert them. Scanned PDFs with no text are flagged: ask for the original or run OCR.
- Seed questions come from `templates/question_bank.csv` (95 common questions in our own words). Edit it, or pass `--questions` with your own CSV or an existing library.
- For each question it keeps up to 3 candidate passages (`--top`). A score of 0.12 or more (`--min-score`) counts as a possible source; 0.07 to 0.12 (`--weak-score`) is listed as "weak" on the Evidence sheet but the row stays NEEDS CLIENT INPUT.
- Output sheets: **Library** (the rows to complete), **Evidence** (all candidate passages with scores), **Documents** (what was read, with warnings), Readme, Change Log, Lists.
- `--check` lists errors (duplicate IDs, Approved answers without a source, invalid values) and warnings (missing owner or date, stale reviews, words that could overstate). It exits with code 1 if there are errors.
- It never writes an answer. That is your job, from the sources.

### `scripts/fill_questionnaire.py`: fill the buyer's questionnaire

```sh
python scripts/fill_questionnaire.py clients/<client>/BUYER.xlsx --library clients/<client>/answer_library.xlsx [--out clients/<client>/BUYER_DRAFT.xlsx] [--dry-run]
python scripts/fill_questionnaire.py clients/<client>/BUYER.xlsx --library clients/<client>/answer_library.xlsx --use-review clients/<client>/BUYER_DRAFT.xlsx --out clients/<client>/BUYER_DRAFT2.xlsx
python scripts/fill_questionnaire.py --finalize clients/<client>/BUYER_DRAFT2.xlsx --out clients/<client>/BUYER_FINAL.xlsx [--force]
```

- **Formats:** `.xlsx`, `.xlsm` and `.csv` (any delimiter and encoding). `.xls` and `.ods` are converted with LibreOffice first and come back as `.xlsx`.
- **Finding the questions:** on each visible sheet it looks for the header row and the question, answer, Yes/No, comments, evidence and ID columns (a column with a Yes/No drop-down is treated as the Yes/No column). Check what it found with `--dry-run`. Override anything: `--sheet`, `--header-row`, `--question-col`, `--answer-col`, `--short-col`, `--comment-col`, `--source-col`, `--id-col` (a letter, a number or the header text; `none` switches a column off), `--first-row`, `--last-row`, `--skip-regex`.
- **What it writes:** the approved answer in the answer column (or the comments column), Yes/No/Partial/N/A in the Yes/No column (matched to the buyer's drop-down values), and "Source: document, section" in the evidence column. With no evidence column, the source goes in the comments column, or on a line under the answer. Change this with `--source-mode auto|column|append|review-only`. Unanswered questions get `NEEDS CLIENT INPUT` (`--placeholder ""` leaves them blank). Cells that already have answers are left alone unless you add `--overwrite`; cells with formulas are never touched.
- **The copy is safe:** the buyer's file is never changed. The copy differs only in the filled cells, the added review sheet and the workbook entries that register it (the sheet list and a few styles). Each filled cell keeps its formatting, and everything else (other sheets, drop-downs, conditional formatting, comments, macros) is kept exactly as it was. In testing, filled and finalised files passed the Open XML SDK validator whenever the buyer's original did.
- **Review sheet** ("Review - remove before sending"): every question, NEEDS CLIENT INPUT first, then CHECK, then OK, with the proposed answer, source, what to do, library ID, score, shared keywords, runner-up and a link to the cell. Type Y in **Resolved** as you clear each item; type a library ID (or NONE) in **Use library ID** to correct a match and rerun with `--use-review`.
- **Your name:** `--prepared-by "Your Name, Your Business"` adds "Prepared by ..." at the top of the review sheet. `--finalize` removes the review sheet, so the buyer never sees it.
- **Only Approved library answers are used.** `--include-drafts` also uses Draft answers, always flagged CHECK.
- **Config file:** save the settings for one buyer's file in JSON in the client's folder and pass `--config clients/<client>/settings.json`; see `templates/fill_config.example.json`. Command-line options win over the file.
- `--finalize` refuses (exit code 1) while placeholders remain or CHECK/NEEDS rows aren't Resolved = Y. `--force` overrides when the client accepts the open items.

### How matching works, and what the score means

1. Both texts are normalised: lower case, filler words dropped ("please describe", "the vendor"), words reduced to their stem (encrypted, encryption: encrypt), and common terms grouped (MFA, 2FA and two-factor all become `mfa`). The groups are in `scripts/sqkit.py` (`SYNONYM_GROUPS`); add your clients' vocabulary there.
2. **Score = 70% keyword match + 30% fuzzy match**, from 0 to 1. The keyword match is TF-IDF cosine similarity: rare, specific words count more than common ones, and known security terms count 1.5 times. It uses the best single phrasing of the library entry (70%) and all its phrasings together (30%). The fuzzy match is rapidfuzz's token-sort ratio, which catches spelling and word-order differences.
3. **OK** at 0.50 or more (`--ok-score`), **CHECK** from 0.25 (`--min-score`), below that NEEDS CLIENT INPUT. Answers are also flagged CHECK when the runner-up is within 0.05 (`--margin`), the question looks reversed ("not", "never"), it asks for specifics (dates, attachments, numbers), the library entry is Low confidence or over a year old (`--stale-days`), or the Yes/No value isn't in the buyer's drop-down.

In testing on about 140 questions written in different words from the library, the right entry was the top match about 9 times in 10, and about 7 in 10 for wording the library had never seen. No wrong match scored 0.50 or more, so wrong matches show up as CHECK rather than OK. That is why the review is not optional, and why adding buyer phrasings to the library pays off.

## Try it on the sample

From `kits/security-questionnaire/`, with the environment activated:

```sh
# 1. Draft a library from the fictional company's seven policies
python scripts/build_library.py --docs samples/policies --out /tmp/draft.xlsx --client "Quarterhour (fictional)"

# 2. Check the completed sample library and list its open questions
python scripts/build_library.py --check samples/library/answer_library.xlsx --gaps /tmp/questions.md

# 3. See what the fill script finds, then fill the fictional buyer's questionnaire
python scripts/fill_questionnaire.py samples/questionnaire/cobalt-ridge-supplier-security-questionnaire.xlsx --library samples/library/answer_library.xlsx --dry-run
python scripts/fill_questionnaire.py samples/questionnaire/cobalt-ridge-supplier-security-questionnaire.xlsx --library samples/library/answer_library.xlsx --out /tmp/cobalt_DRAFT.xlsx

# 4. Reuse the sample reviewer's choices, then try to finalise (it refuses: items are still open)
python scripts/fill_questionnaire.py samples/questionnaire/cobalt-ridge-supplier-security-questionnaire.xlsx --library samples/library/answer_library.xlsx --use-review samples/output/cobalt-ridge-supplier-security-questionnaire_DRAFT2.xlsx --out /tmp/cobalt_DRAFT2.xlsx
python scripts/fill_questionnaire.py --finalize /tmp/cobalt_DRAFT2.xlsx --out /tmp/cobalt_FINAL.xlsx
```

Expected: 40 questions found; 15 OK, 18 CHECK, 7 NEEDS CLIENT INPUT on the first pass; 17 OK, 17 CHECK, 6 NEEDS CLIENT INPUT after the review choices. `samples/README.md` explains each sample file.

### Put your name on the sample

Your name goes on the sample with the `--prepared-by` option of `fill_questionnaire.py`. Rebuild the portfolio sample with your name (from `kits/security-questionnaire/`, with the environment activated):

```sh
python scripts/fill_questionnaire.py samples/questionnaire/cobalt-ridge-supplier-security-questionnaire.xlsx --library samples/library/answer_library.xlsx --use-review samples/output/cobalt-ridge-supplier-security-questionnaire_DRAFT2.xlsx --out samples/output/cobalt-ridge-supplier-security-questionnaire_DRAFT2.xlsx --prepared-by "Your Name, Your Business"
soffice --headless --convert-to pdf --outdir samples/output samples/output/cobalt-ridge-supplier-security-questionnaire_DRAFT2.xlsx
```

The review sheet in the `.xlsx` and in the `.pdf` then says "Prepared by Your Name, Your Business" near the top. The company and the buyer stay fictional: always say so when you show the sample.

## Using it with Claude Code

The skill in `.claude/skills/security-questionnaire/` loads when you ask Claude for this kind of work, or when you type `/security-questionnaire`. Things to ask:

- "New client Acme. Their policies are in `clients/acme/docs`. Build their draft answer library and list the gaps to send them."
- "Write the answers for every Draft row in `clients/acme/answer_library.xlsx`, only from the cited sections. Mark anything unsupported NEEDS CLIENT INPUT."
- "Fill `clients/acme/buyer.xlsx` from the library, then go through the review sheet with me."
- "The CTO answered the gap questions (pasted below). Add them to the library with this email as the source, then refill."

## Files in this kit

```text
kits/security-questionnaire/
├── README.md                    this file
├── requirements.txt             Python packages
├── scripts/
│   ├── build_library.py         draft library from client documents; --check; --blank
│   ├── fill_questionnaire.py    fill a questionnaire copy + review sheet; --use-review; --finalize
│   ├── sqkit.py                 shared code: library format, text matching, synonym groups
│   └── xlsx_patch.py            careful .xlsx editing that leaves the rest of the file untouched
├── templates/
│   ├── answer_library.xlsx      blank library with drop-downs and a Readme sheet
│   ├── question_bank.csv        95 seed questions with alternate phrasings and search terms
│   ├── client_intake_checklist.md
│   ├── cover_note.md            draft and final cover notes, plus the client sign-off
│   ├── fixed_price_offer.md
│   └── fill_config.example.json
└── samples/                     FICTIONAL company and buyer (see samples/README.md)
```

## Limits

- The scripts read text. Scanned PDFs need OCR first, and diagrams are ignored.
- Matching compares words, not meaning. It will miss some paraphrases and occasionally pick a wrong entry with a moderate score; the review sheet shows why it matched so you can tell.
- Questionnaires inside web portals (OneTrust, Whistic and similar) need an export, or the questions copied into a spreadsheet; you then paste the answers back.
- A question that bundles two topics gets one library answer: complete the rest by hand.
- `.xls` and `.ods` files come back as `.xlsx`. Convert back with LibreOffice if the buyer insists on the old format.
