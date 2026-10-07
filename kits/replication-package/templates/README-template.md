# Replication package for "[Paper title]"

[Author 1], [Author 2] · [Journal], [year] · Package version [1.0] · Last updated [YYYY-MM-DD]

> **How to use this template.** Replace everything in [square brackets]. Delete these grey
> notes when you are done. Keep the headings: data editors look for them. The order and
> headings follow the community template README used by social science data editors
> (social-science-data-editors.github.io/template_README). Ask the author to confirm every
> statement about data rights, because only they know.

## Overview

[Two to four sentences. What does the package reproduce? Which single script runs everything?
How long does a full run take, and on what kind of computer?]

Example: *The code in this package rebuilds the analysis data from three public sources and
produces all 4 tables and 3 figures in the paper and 6 tables in the appendix. Run `main.do`.
A full run takes about 2 hours on a laptop.*

## Data availability and provenance statements

> Say where every piece of data came from and whether a replicator can get it. Restricted or
> confidential data are fine: say so, and explain how someone else could apply for access.

### Statement about rights

- [ ] The authors have legitimate access to all the data used in the paper and permission to use them.
- [ ] The authors have permission to publish the data included in this package (or the data's terms allow it).

### License for data

[Licence of the data you include, for example CC BY 4.0, or the provider's terms. If different
files have different terms, say so file by file.]

### Summary of availability

- [ ] All data are publicly available.
- [ ] Some data cannot be made publicly available.
- [ ] No data can be made publicly available.

### Details on each data source

> One short paragraph per source: who provides it, what it contains, how you got it (download
> date, request, licence), where it is in this package, and its citation. For restricted data:
> how to apply, how long it takes, what it costs, and which exact files and variables to request.

**[Dataset name]** ([Provider], [year]). [What it contains.] [How it was obtained, and when.]
The file `[data/raw/file.csv]` is included / is not included because [reason]. To get it,
[steps, cost, wait time]. Cite as: [citation, also listed in References].

## Dataset list

| Data file | Source | Notes | Provided |
|---|---|---|---|
| `data/raw/[file]` | [Provider (year)] | [What it is] | Yes / No |
| `data/derived/[file]` | Created by `[program]` | [What it is] | Yes / Re-created by the code |

## Computational requirements

### Software requirements

> List the exact version of every program and package. The master script's log records them.

- [Python 3.11.9 / R 4.4.1 / Stata/MP 18.0 / MATLAB R2024a / SAS 9.4]
  - [Packages and versions, or: "all packages are pinned in `requirements.txt` / `renv.lock`";
    for Stata: "community packages are saved in `ado/` (reghdfe [version], estout [version])"]
- [Any other tool, for example a LaTeX distribution or a GIS program]

### Controlled randomness

- [ ] A random seed is set at line [number] of `[program]`.
- [ ] No random numbers are used.

### Memory, runtime and storage requirements

- Full run time: [under 10 minutes / about 2 hours / several days].
- Storage needed: [under 1 GB / 25 GB].
- Computer used for the last full run: [processor, number of cores, memory, operating system],
  on [date].

## Description of programs

> Explain what each folder and program does, in the order they run.

| Program | What it does |
|---|---|
| `main.[py/R/do]` | Runs every program below in order and writes a log to `logs/`. |
| `code/01_[name]` | [Cleans the raw data and writes ...] |
| `code/02_[name]` | [Estimates ... and writes Table 1 and Table 2] |

### License for code

[For example MIT. See `LICENSE`.]

## Instructions to replicators

1. Install [software and version].
2. [Install packages: `pip install -r requirements.txt` / open R in this folder and run
   `renv::restore()` / nothing to do: Stata packages are in `ado/`.]
3. [For data not included: put the files in `data/raw/` with exactly these names: ...]
4. Run `[main.py / main.R / main.do]` from this folder. Nothing else needs editing.
5. Tables and figures appear in `[output/]`; the log is in `[logs/]`.

## List of tables and programs

> Every table and figure in the paper and appendix, the program and line that makes it, and the
> output file. Keep templates/table-figure-map.xlsx as your working copy and paste the final
> version here.

| Exhibit | Program | Line | Output file | Note |
|---|---|---|---|---|
| Table 1 | `code/02_[name]` | [42] | `output/table1.csv` | |
| Figure 1 | `code/03_[name]` | [17] | `output/figure1.png` | |
| Table A1 | `code/04_[name]` | [30] | `output/tableA1.csv` | Online appendix |

## References

> Cite every dataset (and any code you reused), with a DOI or stable web address. Cite the same
> datasets in the paper.

[Provider]. [Year]. "[Dataset title]" [data set]. [Publisher or repository], version [x].
https://doi.org/[...]. Accessed [date].

## Acknowledgements

[Optional. Follow the journal's rules. If someone helped prepare the package, for example a
paid assistant who used AI-assisted coding tools, say so here if the journal asks for it.]
