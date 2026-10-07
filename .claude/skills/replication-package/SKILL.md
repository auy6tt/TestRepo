---
name: replication-package
description: Use when preparing, checking or cleaning up a research replication package for a journal data editor or code check (AEA and other economics or social science journals), writing a replication README, data availability statement or table-and-figure-to-program map, adding a master script, pinning dependencies, removing hard-coded paths, reproducing a paper's tables and figures from its code, or migrating old Stata, R, SAS, MATLAB or Python statistics code.
argument-hint: "[path to the package]"
---

# Replication package service

Make a researcher's package run from one master script and document it for the data editor,
**without changing any result**. Tools, templates and a worked example are in
`${CLAUDE_PROJECT_DIR}/kits/replication-package/` (its README.md covers pricing and the client side).

Package to work on: $ARGUMENTS (if empty, ask the user which folder).

## Rules that override everything else

- Never change estimates, specifications, samples, data values or output files to make numbers
  match or to "fix" results.
- Report every discrepancy to the author, with the likely cause if known. The author decides.
- Never recreate an output by hand, and never invent a missing program, dataset, citation,
  software version or licence. List it as a question for the author.
- Restricted or confidential data stay with the client. Do not request, open, copy or upload
  them. If a package contains data that look restricted, stop and tell the user.
- Never print or open data values to check for personal data. The checker reads CSV headers only.
- A new seed or a different package version can move results. Propose it; apply it only after
  the author agrees; report the effect.
- Keep the package as received untouched. Work on a copy, and write reports outside the package.

## Setup

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r "${CLAUDE_PROJECT_DIR}/kits/replication-package/requirements.txt"
```

## Workflow

1. **Intake.** Confirm journal, deadline, scope (README check or full clean-up), software and
   versions, and which data are restricted. Questions: `templates/client-intake-checklist.md`.
2. **Check.** `python "${CLAUDE_PROJECT_DIR}/kits/replication-package/scripts/check_package.py" PACKAGE --out REPORTS/before`.
   Read every finding, drop false positives, and summarise the High findings in plain words.
3. **Baseline.** Keep `as-received/` read-only. Work in a separate copy under Git, one commit
   per kind of change.
4. **Fix with the smallest change that works.**

   | Problem | Fix |
   |---|---|
   | No master script | Copy `templates/main.py`, `main.R` or `main.do`; list the programs in run order |
   | Absolute paths | Python: `ROOT = Path(__file__).resolve().parents[1]`. R: paths relative to the top folder (or `here::here()`). Stata: `` global root "`c(pwd)'" `` once in main.do, then `"$root/..."`. MATLAB: `fileparts(mfilename('fullpath'))` |
   | `setwd()` / `cd` | Remove; at most one in the master script, pointing at the root |
   | Unpinned packages | The author's versions: `pip freeze`, `renv::snapshot()`, or ado files in `ado/plus`. Never "latest" |
   | No logs | The master templates write logs |
   | Missing program, data or citation | Ask the author |
   | Personal-data columns | Ask the author for a de-identified file or a restricted-access plan |

   Diff every program against the original. Only paths, the master script and comments should change.
5. **Reproduce.** `python "${CLAUDE_PROJECT_DIR}/kits/replication-package/scripts/run_and_compare.py" PACKAGE --master main.py --clean data/derived --originals as-received/output --report-dir REPORTS/run1`.
   Exit 0 = reproduced, 1 = differences, 2 = run failed. Stata, MATLAB and SAS need licences:
   the author runs the master script, then use `--compare-only --originals A --regenerated B`.
   R needs `sudo apt-get install r-base`. If outputs differ, find the likely cause and report
   it; do not edit code to close the gap.
6. **Document.** README from `templates/README-template.md`: every section, exact versions, run
   time and computer, a data availability statement per source, data citations with DOI or
   URL, and the table and figure map with program and line (find lines with
   `grep -n "to_csv\|savefig\|ggsave\|esttab\|graph export"`).
7. **Final check.** Re-run `check_package.py`. No High findings left, or each one explained.
8. **Deliver.** Package, both check reports, the comparison report and a delivery note
   (`templates/delivery-note.md`; example in `samples/delivery-note.md`) listing every change
   and every difference. Disclose AI use. Suggest acknowledgement wording; the journal's rules
   and the author decide.

## Common mistakes

| Mistake | Instead |
|---|---|
| Updating packages to the latest versions | Pin the versions the author used |
| Adding a seed and calling the new numbers "reproduced" | A new seed is a change: report old and new values |
| Treating checker findings as facts | They are pattern matches: confirm each one in the code |
| Running the original scripts in place | `run_and_compare.py` runs a clean copy and warns about writes to the original |
| "Verified" in the delivery note | "Reproduced on this computer with these versions" |

## Example

`kits/replication-package/samples/`: a fictional package before (34 findings), the fixed
package (0 findings), the comparison report (all outputs reproduced) and the delivery note.
