# Replication package for "After-School Tutoring and Math Achievement: Evidence from a Fictional Pilot"

Jane Doe and John Roe · Package version 1.0 · Last updated 2026-10-07

> **Demonstration only.** The authors, the paper, the school district and the data are invented.
> This package shows what a cleaned-up replication package looks like.

## Overview

The code in this package uses one dataset to produce the two tables and one figure in the paper
and one appendix table. One master script, `main.py`, runs everything in under 10 seconds on a
laptop. Results appear in `output/` and a log of the run in `logs/main.log`.

## Data availability and provenance statements

### Statement about rights

- [x] The authors have legitimate access to all the data used in the paper and permission to use them.
- [x] The authors have permission to publish the data included in this package.

### License for data

The data file `data/raw/tutoring_pilot.csv` is released under CC0 1.0 (see `LICENSE.txt`).

### Summary of availability

- [x] All data are publicly available.
- [ ] Some data cannot be made publicly available.
- [ ] No data can be made publicly available.

### Details on each data source

**Tutoring pilot student records, 2022-2023** (Example County School District, 2024; fictional).
One row per student (786 students in 20 schools) with the school, grade, sex, low-income status,
whether the student was offered tutoring by lottery, and math scores (0-100) at the start and
end of the school year. Thirty-six students have no endline score because they left before the
endline test. The authors received the file from the district under a data sharing agreement
that allows publication of de-identified data. Names, contact details, home addresses and birth
dates were removed before publication; the analysis never used them. The file is included as
`data/raw/tutoring_pilot.csv`. Cite as Example County School District (2024), listed in References.

## Dataset list

| Data file | Source | Notes | Provided |
|---|---|---|---|
| `data/raw/tutoring_pilot.csv` | Example County School District (2024), fictional | Student records, identifiers removed | Yes |
| `data/derived/analysis_sample.csv` | Created by `code/01_clean_data.py` | Students with an endline score; standardised scores | Yes, and re-created by `main.py` |

## Computational requirements

### Software requirements

- Python 3.11.15
  - numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.11.2,
    all pinned in `requirements.txt`
- `logs/main.log` records the version of each package used in the last run.

### Controlled randomness

- [ ] A random seed is set in the code.
- [x] No random numbers are used. (The tutoring lottery took place before the data were collected.)

### Memory, runtime and storage requirements

- Full run time: about 5 seconds.
- Storage needed: under 1 MB.
- Computer used for the last full run: 4 processor cores, 15 GB memory, Ubuntu Linux 24.04,
  on 2026-10-07.

## Description of programs

| Program | What it does |
|---|---|
| `main.py` | Runs the four programs below in order and writes `logs/main.log`. |
| `code/01_clean_data.py` | Keeps students with an endline score, standardises scores using the control group, and writes `data/derived/analysis_sample.csv`. |
| `code/02_analysis.py` | Table 1 (baseline characteristics by group) and Table 2 (effect of the tutoring offer, standard errors clustered by school). |
| `code/03_figure1.py` | Figure 1 (endline score by baseline quintile and group). |
| `code/04_tableA1_attrition.py` | Appendix Table A1 (share of students missing the endline test, by group). |

### License for code

MIT License (see `LICENSE.txt`).

## Instructions to replicators

1. Install Python 3.11.
2. In this folder, create an environment and install the packages:
   `python -m venv .venv`, then activate it (`source .venv/bin/activate` on Mac and Linux,
   `.venv\Scripts\activate` on Windows), then `pip install -r requirements.txt`.
3. Run `python main.py`. No file paths need editing.
4. The tables and the figure appear in `output/`; the log is `logs/main.log`.

## List of tables and programs

| Exhibit | Program | Line | Output file | Note |
|---|---|---|---|---|
| Table 1 | `code/02_analysis.py` | 42 | `output/table1_summary_stats.csv` | |
| Table 2 | `code/02_analysis.py` | 78 | `output/table2_main_results.csv` | |
| Figure 1 | `code/03_figure1.py` | 47 | `output/figure1_scores_by_baseline.png` | |
| Table A1 | `code/04_tableA1_attrition.py` | 37 | `output/tableA1_attrition.csv` | Appendix |

## References

Example County School District. 2024. "Tutoring Pilot Student Records, 2022-2023" [data set].
Fictional data created for a demonstration. https://example.org/tutoring-pilot-data
(placeholder address). Accessed 2026-10-07.

## Acknowledgements

[Your name] prepared this replication package for the authors with the help of AI-assisted
coding tools, and reviewed every change. No estimates were changed.
