# Portfolio sample: a replication package, before and after

A complete worked example of the service, from the package a client sends you to a package
that is ready for the data editor. **Everything here is fictional**: the authors (Jane Doe and
John Roe), the paper, the school district and the data. Show it to prospects as a demonstration.

| Folder or file | What it shows |
|---|---|
| [1-original-package/](1-original-package/) | The package as the authors sent it, with common problems built in |
| [2-check-report/](2-check-report/) | The checker's findings on it: 34 (11 High, 18 Medium, 5 Low), as .md and .xlsx |
| [3-fixed-package/](3-fixed-package/) | The cleaned package: one master script, relative paths, pinned versions, a log and a full README |
| [4-comparison-report/](4-comparison-report/) | The cleaned package, run from a clean copy, recreates every original output exactly |
| [5-final-check/](5-final-check/) | The checker on the cleaned package: no findings |
| [delivery-note.md](delivery-note.md) | The message sent to the authors with the result |

## What was wrong with the original package

- No master script. The README had six lines: no data availability statement, no software
  versions, no instructions and no list of tables.
- Hard-coded folders from two computers (`C:/Users/jdoe/...` on Windows, `/Users/jroe/...` on a
  Mac), a home-folder path (`~/Dropbox/...`) and an `os.chdir()`, so no single computer could run
  all of it, let alone the data editor's.
- `requirements.txt` without versions, and numpy and scipy missing from it.
- A raw data file with columns for names, parent emails, phone numbers, home addresses and birth
  dates. (The values are obvious placeholders such as `Student 0001` and `parent0001@example.org`.)
- An appendix table (Table A1) with no program that creates it.
- An old Stata do-file that reads a data file not in the package, uses community commands with no
  version list, draws bootstrap samples without a seed and writes paths with backslashes.
- No log, no licence, and a stray `Thumbs.db` file (a Windows thumbnail cache) in `output/`.

## What the authors were asked, and their answers (fictional)

1. *Which program makes Table A1?* They sent it. It now runs from the master script and
   reproduces the original table exactly.
2. *May the identifiers be published?* No. They approved a version of the data without the five
   identifier columns. The analysis never used them, and the results did not change.
3. *Is `old/robustness_check.do` part of the paper?* No, it was an abandoned check, so it was left out.
4. *Which licences?* MIT for the code, CC0 for the data.

## How the sample was made

- The dataset (786 students in 20 schools) was generated with a fixed random seed. It is not
  based on any real people or places.
- The files in `1-original-package/output/` were made by running the authors' scripts
  unchanged, with only their hard-coded folders pointed at a temporary copy to stand in for the
  authors' computers.
- In `3-fixed-package/`, the only code changes are file paths, the master script and comments.
  Compare `1-original-package/code/analysis.py` with `3-fixed-package/code/02_analysis.py` to
  see it.

## Re-run it yourself

From the `kits/replication-package` folder, with the kit's requirements installed:

```sh
python scripts/check_package.py samples/1-original-package --out samples/2-check-report

python scripts/run_and_compare.py samples/3-fixed-package --master main.py \
    --clean data/derived --originals samples/1-original-package/output \
    --report-dir samples/4-comparison-report

python scripts/check_package.py samples/3-fixed-package --out samples/5-final-check
```

To see a failed run, try the original package. It stops at the first hard-coded folder:

```sh
python scripts/run_and_compare.py samples/1-original-package --master code/clean_data.py \
    --report-dir ../original-run-report
```

## Before you show it to prospects

- Replace `[Your name]` in `3-fixed-package/README.md` (Acknowledgements) and in `delivery-note.md`.
- Say in your message that it is a fictional demonstration.
- Share the whole `samples` folder as a zip file, or as a public repository of its own.
