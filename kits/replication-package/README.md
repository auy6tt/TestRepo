# Replication package starter kit

A paid service you can deliver from day one: getting researchers' replication packages ready
for journal data editors, and moving old statistics code onto current software. The kit has the
offer, the process, two tools that do the mechanical checking, templates, and a finished sample
to show prospects.

**Contents:** [The offer](#the-offer) · [Who buys](#who-buys-and-where-to-find-them) ·
[Prices](#prices) · [Process](#how-a-job-runs-step-by-step) ·
[Checklist](#checklist-before-you-deliver) · [Ethics](#ethics-rules) · [Tools](#the-tools) ·
[What's in the kit](#whats-in-the-kit) · [Limits](#limits)

## The offer

Economics and social science journals with a data editor check the code and data of accepted
papers before publication. The package must run from one master script and come with a README in the
data editors' standard format: data availability and provenance statements, computational
requirements with software versions, instructions, and a list mapping every table and figure to
the program that produces it. It also needs pinned dependencies, no hard-coded absolute paths,
logs and data citations. Many authors are good researchers but have never packaged code this
way, and the check stands between acceptance and publication.

You sell two things:

1. **README and structure check.** You run the checker, write the README from the template, build
   the table and figure map, and send the author a list of fixes.
2. **Full clean-up.** All of the above, plus the fixes themselves: master script, relative
   paths, pinned versions, logs, a reproduction run with a comparison report, and a delivery note.

The promise is "your package will run and be documented", never "your results are right".

## Who buys, and where to find them

The buyer is usually the corresponding author, a postdoc or a research assistant on a paper that
has just been accepted, or conditionally accepted, at a journal with a data editor. Examples:
the American Economic Association's journals, Econometrica, the Review of Economic Studies and
the Economic Journal in economics, and the American Journal of Political Science in political
science. Policies change, so read each journal's current data and code policy before you pitch.

- **Authors of recent working papers.** Working-paper series (NBER, CEPR, IZA, SSRN) show
  recent papers, and authors list "conditionally accepted" or "forthcoming" papers on their
  websites and CVs. Conditionally accepted papers are the best leads: the data editor's check is
  still ahead of them. Write one personal email to the corresponding author, using
  [templates/offer.md](templates/offer.md). No bulk mailing.
- **Postdoc and PhD networks.** Department mailing lists, graduate student associations,
  research-group Slack or Discord channels, and LinkedIn or Bluesky groups for economists and
  political scientists. Post the short version of the offer, or offer a free 30-minute talk on
  "getting your package past the data editor".
- **Research-computing help desks and library data services.** Universities' research
  computing, data services and reproducibility teams get these requests and often cannot take
  them all. Ask to be on their list of external helpers.

## Prices

| Service | Price guide | Includes |
|---|---|---|
| README and structure check | $300–600 | Check report, README in the standard format, table and figure map, list of fixes for the author |
| Full clean-up | $800–2,500 | All of the above, plus master script, path fixes, pinned versions, logs, reproduction run and comparison report, delivery note, one round of changes after the data editor's report |
| Migration of old code | Quote separately | For example an old Stata version to a current one, or SAS to R or Python, with a comparison report showing the outputs match |

Quote a fixed price after a free first look: run `check_package.py` on their package (with their
permission) and price by the number of programs, languages, run time and High findings. Charge
more when data are restricted (the author has to run things for you), programs are missing, or
the deadline is short. Ask for 50% upfront; the repo's
[simple agreement](../../templates/simple-agreement.md) works for this.

## How a job runs, step by step

1. **Intake.** Send [templates/client-intake-checklist.md](templates/client-intake-checklist.md).
   Get the code, the public data, the original outputs and any data editor report. Restricted
   data stay with the author.
2. **First look and quote.** Run `check_package.py`. Send the author the top findings and a fixed
   price. Agree in writing that the author decides about any difference in results.
3. **Baseline.** Keep an untouched copy of the package as received. Put your working copy in its
   own private Git repository and commit after each kind of change.
4. **Clean up.**
   - Add a master script from [templates/](templates/) (`main.py`, `main.R` or `main.do`).
   - Replace hard-coded paths with paths relative to the package. Remove `setwd()` and `cd`.
   - Pin dependencies at the **author's** versions (`pip freeze`, `renv::snapshot()`, or the ado
     files from their computer), never today's latest.
   - Make the master script write a log.
   - Ask the author for anything missing: programs, data, citations, licences. Never invent them.
   - Seeds and version changes can move results: agree each one with the author first.
5. **Reproduce.** Run `run_and_compare.py` against the author's original outputs. For Stata,
   MATLAB or SAS, the author runs the master script and you use `--compare-only`.
6. **Document.** Write the README from [templates/README-template.md](templates/README-template.md)
   and fill in [templates/table-figure-map.xlsx](templates/table-figure-map.xlsx).
7. **Final check.** Run `check_package.py` again. Fix or explain every remaining High finding.
8. **Deliver.** Send the package, the reports and a delivery note
   ([template](templates/delivery-note.md), [example](samples/delivery-note.md)) listing every
   change and every difference.
9. **Follow up.** Handle the data editor's questions (one round is included), then ask for a
   testimonial with the repo's [testimonial request](../../templates/testimonial-request.md).

## Checklist before you deliver

- [ ] The package runs from one master script on a clean copy, and the comparison report says
      REPRODUCED, or every difference is in the delivery note.
- [ ] No High findings left in the final check, or each one is explained.
- [ ] README: every section, exact software and package versions, run time and computer, a data
      availability statement for each source, data citations, and the table and figure map with
      program lines.
- [ ] Dependencies pinned at the author's versions.
- [ ] Logs from the final run are included.
- [ ] No personal or restricted data in the deposit, confirmed by the author.
- [ ] The author chose the licences.
- [ ] The delivery note lists every change and every difference.
- [ ] AI use disclosed; acknowledgement worded the way the journal requires.
- [ ] Client files deleted from your computer and cloud storage once the job is closed.

## Ethics rules

1. **Never change estimates or "fix" results.** No changes to specifications, samples, data
   values or outputs to make numbers match. Your job is to make the package run and document it.
2. **Report every discrepancy to the author**, however small, with the likely cause if you know
   it. The author decides what to do.
3. **Never recreate an output by hand.** If no program makes a table, ask the author for it.
4. **Restricted and confidential data stay with the client.** Don't ask for them. If you receive
   them by mistake, delete them and tell the client. Work from the code and let the author run it.
5. **Acknowledge help the way the journal requires.** Suggest wording; the author decides. Never
   claim authorship.
6. **Disclose AI use.** Tell clients upfront that you use AI-assisted coding tools and that you
   review every change, and say it again in the delivery note. Turn off model training on your
   data in your tools' privacy settings, and never paste restricted data into an AI tool.
7. **Keep client work private.** Show prospects the fictional sample, not client packages.
8. **Say exactly what you checked:** "reproduced on my computer with these versions", not
   "verified".

## The tools

### Setup

Python 3.10 or newer (tested with 3.11). From the repository's top folder:

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r kits/replication-package/requirements.txt
```

The scripts also run with only the standard library: without `openpyxl` there is no Excel
report, and without `pillow` images are compared by bytes only.

### check_package.py: find the problems

```sh
python kits/replication-package/scripts/check_package.py path/to/package --out reports/smith-2026
```

Reads the package (it never changes it) and writes `check_report.md` and `check_report.xlsx`.
Each finding has a severity (High, Medium, Low, Info), a location and a suggested fix. The Excel
file has a Status column so you can track fixes. It checks:

- README: present, the expected sections, software versions, data citations
- a master script that runs everything
- hard-coded absolute paths (Windows and Unix), home-folder paths, backslash paths, and
  `setwd()`/`cd` calls in R, Stata, Python (including notebooks), MATLAB and SAS
- dependency pins: `renv.lock`, `requirements.txt`/`environment.yml`, a Stata ado folder or list
- data files the code reads that are not in the package, and data downloaded at run time
- tables and figures that no program appears to create
- very large files (`--large-mb`, default 100)
- column names in CSV/TSV files that suggest personal data (names, emails, phone numbers,
  addresses, birth dates, ID numbers, locations). It reads the header row only and never
  prints values.
- random numbers without a seed, missing logs, missing licence, stray system files

### run_and_compare.py: prove it reproduces

```sh
python kits/replication-package/scripts/run_and_compare.py path/to/package --master main.py \
    --outputs output --clean data/derived --originals path/to/original/output \
    --report-dir reports/smith-2026/run1
```

First install the package's own dependencies, ideally in a fresh virtual environment, and pass
that interpreter with `--python` (for example `--python .venv/bin/python`). An error like
"No module named pandas" means a missing dependency, not a failed reproduction.

Copies the package to a temporary folder, empties the output folders there, runs the master
script with a time limit, saves everything it prints to `run_log.txt`, and compares every
regenerated output with the original. It writes `comparison_report.md`, and
`comparison_details.csv` when cells differ.

| Option | Meaning |
|---|---|
| `--master` | Master script, relative to the package (`.py` or `.R`) |
| `--outputs` | Output folders to empty before the run and compare after it (default `output`) |
| `--clean` | Other folders to empty first, such as `data/derived` |
| `--originals` | Folder with the original outputs (default: the package's own output folders) |
| `--timeout` | Time limit in seconds (default 3600) |
| `--rtol`, `--atol` | Tolerance for numbers (defaults 1e-6 and 1e-9) |
| `--compare-only` | Compare `--originals` with `--regenerated` without running anything |
| `--keep-temp` | Keep the clean copy for inspection |

Tables (CSV, TSV, Excel, Stata `.dta`) are compared cell by cell: numbers within the
tolerance, everything else (stars, brackets, labels) exactly. Text outputs such as `.tex` are
compared line by line the same way. Images are compared by SHA-256 hash, then size, dimensions
and the share of pixels that differ. PDF and SVG files are compared after removing embedded
dates. It also warns if the run changed files in the original package folder, which means the
code still writes to absolute paths. Exit codes: 0 all outputs match, 1 differences or missing
outputs, 2 the run failed or timed out.

R scripts need R (`sudo apt-get install r-base` in this cloud container). Stata, MATLAB and SAS
need licences, so the author runs the master script and you compare with `--compare-only`.

### With Claude Code

This repository includes a skill at
[.claude/skills/replication-package/SKILL.md](../../.claude/skills/replication-package/SKILL.md),
so Claude Code follows this process. Try:

- "Check the replication package in clients/smith-2026 and summarise the High findings for the author."
- "Clean up clients/smith-2026 for the AEA data editor. Don't change any estimates."
- "Run the package from a clean copy and compare the outputs with the originals in clients/smith-2026/as-received/output."

## What's in the kit

```text
kits/replication-package/
├── README.md                    this guide
├── requirements.txt             Python packages, pinned
├── scripts/
│   ├── check_package.py         findings report (.md and .xlsx)
│   └── run_and_compare.py       clean-copy run and output comparison
├── templates/
│   ├── README-template.md       README in the data editors' section structure
│   ├── main.py, main.R, main.do master scripts with logging
│   ├── table-figure-map.xlsx    table and figure to program map, with progress counts
│   ├── client-intake-checklist.md
│   ├── offer.md                 email and short post
│   └── delivery-note.md         what you send with the finished package
└── samples/                     fictional before-and-after portfolio sample (see samples/README.md)
```

## Limits

- The checker reads text patterns. It misses things, and it flags some things that are fine.
  Read every finding before you act on it or pass it on.
- `main.R` and `main.do` follow common practice but were not run while building this kit,
  because R and Stata were not installed. Test them on your first R or Stata job.
- A match in `run_and_compare.py` means the code reproduces the outputs on your computer with
  your software. The data editor may still find issues on theirs.
- Useful references: the Social Science Data Editors' template README
  (https://social-science-data-editors.github.io/template_README/), the AEA Data Editor's
  guidance (https://aeadataeditor.github.io/aea-de-guidance/) and the Data and Code
  Availability Standard (https://datacodestandard.org/).
- This cloud container is temporary. Keep each client's work in its own private repository and
  commit as you go.
