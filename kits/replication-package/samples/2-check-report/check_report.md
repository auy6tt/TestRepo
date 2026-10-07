# Replication package check: 1-original-package

Checked 2026-10-07 with check_package.py 1.0. This is an automated first pass: every finding needs a human look before you act on it.

## Summary

| Severity | Findings | What it means |
|---|---:|---|
| High | 11 | Likely to stop the code running, or to fail the journal's code check |
| Medium | 18 | The data editor will probably ask for a change |
| Low | 5 | Good practice, quick to fix |
| Info | 0 | For your information |
| **Total** | **34** | |

## Package at a glance

- **Files:** 11 (0.2 MB)
- **Code files:** Stata 1, Python 3
- **README:** README.txt
- **Master script:** none found
- **Dependency files:** requirements.txt
- **Tables and figures found:** 4

## Findings

### High (11)

| ID | Check | Where | Finding | Suggested fix |
|---|---|---|---|---|
| F01 | README | README.txt | Section missing: Data availability and provenance statements. | Add a data availability statement: where each dataset comes from, whether it is included, and how a replicator can get any data that is not included (cost, wait time, application). |
| F02 | README | README.txt | Section missing: Computational requirements. | Add the software and versions used (including packages), the operating system, and hardware. |
| F03 | README | README.txt | Section missing: Instructions to replicators. | Add step-by-step instructions: what to install, which single script to run, and where the results appear. |
| F04 | README | README.txt | Section missing: List of tables and figures with the programs that make them. | Add a table mapping every table and figure in the paper to the program (and line) that creates it and the output file name. |
| F05 | Master script | (package) | No master script found. Nothing runs the whole package from start to finish. | Add one master script in the top folder (main.py, main.R or main.do from templates/) that runs every program in order and writes a log. |
| F06 | Paths | code/analysis.py (line 7) | Hard-coded absolute path: `/Users/jroe/Dropbox/tutoring-paper/`. It points into a synced folder (Dropbox, OneDrive or similar). | Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], then ROOT / "data" / "raw" / "file.csv". |
| F07 | Paths | code/clean_data.py (line 6) | Changes the working folder to a hard-coded path: `C:/Users/jdoe/Dropbox/tutoring-paper`. It points into a synced folder (Dropbox, OneDrive or similar). | Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], then ROOT / "data" / "raw" / "file.csv". |
| F08 | Paths | code/clean_data.py (line 8) | Hard-coded absolute path: `C:/Users/jdoe/Dropbox/tutoring-paper/data/raw/tutoring_pilot.csv`. It points into a synced folder (Dropbox, OneDrive or similar). | Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], then ROOT / "data" / "raw" / "file.csv". |
| F09 | Paths | old/robustness_check.do (line 2) | Changes the working folder to a hard-coded path: `C:\Users\jdoe\Dropbox\tutoring-paper`. It points into a synced folder (Dropbox, OneDrive or similar). | Set the root once in the master do-file (global root "`c(pwd)'") and write paths as "$root/data/raw/file.dta". |
| F10 | Data files | old/robustness_check.do (line 3) | Reads `robustness_sample.dta`, which is not in the package. | Add the file. If the data are restricted or confidential, keep the code, and explain in the README's data availability section how a replicator can get access. |
| F11 | Personal data | data/raw/tutoring_pilot.csv | Column names suggest personal data (name: student_name; email: parent_email; phone: phone; address: home_address; birth date: dob). Only the header row was read; no values were opened. | Ask the author. If these are real identifiers, remove the columns before publishing (if the analysis does not use them) or move the file to restricted access and explain access in the README. Do not open or share the values. |

### Medium (18)

| ID | Check | Where | Finding | Suggested fix |
|---|---|---|---|---|
| F12 | README | README.txt | Section missing: Statement about rights (permission to use and share the data). | State that the authors may use the data and may (or may not) share them, and under which licence or terms. |
| F13 | README | README.txt | Section missing: Dataset list (each data file, its source, and whether it is provided). | Add a table of every data file: name, source, whether it is provided, and its format. |
| F14 | README | README.txt | Section missing: Hardware and run time. | Say how long a full run takes and on what computer (processor, memory, operating system). |
| F15 | README | README.txt | Section missing: Description of programs. | Describe the programs: what each folder and script does, in the order they run. |
| F16 | README | README.txt | Section missing: References and data citations. | Add a References section that cites every dataset (creator, year, title, publisher or repository, version, DOI or web address). |
| F17 | README | README.txt | The README does not say which version of Stata was used. | Add the exact version (for example Stata/MP 18.0) under Computational requirements, and check it with the author. |
| F18 | README | README.txt | The README does not say which version of Python was used. | Add the exact version (for example Python 3.11.9) under Computational requirements, and check it with the author. |
| F19 | README | README.txt | No data citation found (no DOI or web address in the README). | Cite each dataset in the References section with a DOI or a stable web address, and cite the same datasets in the paper. |
| F20 | Paths | code/figure1.py (line 6) | Path inside one person's home folder: `~/Dropbox/tutoring-paper/data/derived/analysis_sample.csv`. It works only on that computer. It points into a synced folder (Dropbox, OneDrive or similar). | Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], then ROOT / "data" / "raw" / "file.csv". |
| F21 | Paths | code/figure1.py (line 40) | Path inside one person's home folder: `~/Dropbox/tutoring-paper/output/figure1_scores_by_baseline.png`. It works only on that computer. It points into a synced folder (Dropbox, OneDrive or similar). | Build paths from the package folder: ROOT = Path(__file__).resolve().parents[1], then ROOT / "data" / "raw" / "file.csv". |
| F22 | Paths | old/robustness_check.do (line 3) | Path written with backslashes: `data\derived\robustness_sample.dta`. This works only on Windows. | Use forward slashes (data/raw/file.csv). They work on Windows, Mac and Linux. |
| F23 | Paths | old/robustness_check.do (line 11) | Path written with backslashes: `output\tableA2_robustness.tex`. This works only on Windows. | Use forward slashes (data/raw/file.csv). They work on Windows, Mac and Linux. |
| F24 | Dependencies | old/robustness_check.do | Uses Stata community commands with no list or copy of them: eststo, esttab, reghdfe. | Save the exact ado files inside the package (an ado/ folder set up in the master do-file, see templates/main.do) and list them with versions in the README. |
| F25 | Dependencies | requirements.txt | Packages listed without exact versions: matplotlib, pandas, statsmodels. | Pin each one with ==, using the versions the author actually used (pip freeze on their computer), not today's latest versions. |
| F26 | Dependencies | requirements.txt | Imported in the code but not in the package list: numpy (imported in code/analysis.py); scipy (imported in code/analysis.py). | Add each one with its exact version (name==version). |
| F27 | Outputs | output/tableA1_attrition.csv | No program in the package appears to create this file. | Ask the author for the program that makes it and add it to the master script and the table/figure list. If the file is not in the paper, remove it. Never recreate an output by hand. |
| F28 | Randomness | old/robustness_check.do (line 8) | Uses random numbers but no seed is set: `bootstrap _b, reps(500) cluster(school_id): regress endli...`. | Set a seed once, e.g. set seed 20240101, and describe it in the README. A new seed can change results slightly: agree with the author first and report any change. |
| F29 | Logs | (package) | No log files, and no code that writes a log. | Have the master script save a log of the full run (templates/main.* do this), run it once, and include the logs in the package. |

### Low (5)

| ID | Check | Where | Finding | Suggested fix |
|---|---|---|---|---|
| F30 | README | README.txt | Section missing: Overview. | Add a short overview: what the package reproduces, which script to run, and roughly how long it takes. |
| F31 | Paths | code/clean_data.py (line 2) | Absolute path in a comment: `D:\projects\tutoring\raw`. | Harmless when running, but it reveals where files lived on the author's computer. Delete or update the comment. |
| F32 | Dependencies | (Stata code) | No version statement in the do-files. | Add version NN (the Stata version the author used) near the top of the master do-file. |
| F33 | Housekeeping | (package) | No LICENSE file. | Ask the author which licence to use for code and data (for example MIT for code, CC BY 4.0 for data they own) and add a LICENSE file. |
| F34 | Housekeeping | output/Thumbs.db | 1 stray system or temporary file(s) or folder(s). | Delete them from the deposit (they are created by Mac, Windows, Python, R or Office). |

## What this check does not do

- It does not run the code. Use run_and_compare.py for that.
- It reads text patterns, so it can miss problems and can flag things that are fine.
- For CSV and TSV files it reads only the header row. It never opens or prints data values.
- It cannot judge whether the README is accurate, only whether the expected sections exist.
