# Delivery note

*Send with the cleaned package. Fill in every [bracket]. State facts, list every difference, and leave every decision about results to the author. A filled-in example is in samples/delivery-note.md.*

```text
Subject: Replication package for "[paper title]": ready for your review

Dear [name],

The cleaned replication package is [attached / at link]. In short:

RESULT
- The package now runs from one master script ([main.do]) in [time] on [computer and software].
- [All N tables and figures were regenerated and match your originals exactly.] / [N of M match; the differences are listed below.]
- Reports: check before the clean-up, reproduction report, check after the clean-up.

WHAT I CHANGED (no estimates, data values or results were changed)
1. [Added main.do, which runs every program in order and saves a log.]
2. [Replaced hard-coded folder paths with paths relative to the package (N files).]
3. [Recorded exact package versions in requirements.txt / renv.lock / ado folder.]
4. [Wrote the README in the data editors' format, including the table and figure map.]

DIFFERENCES AND QUESTIONS FOR YOU (you decide)
1. [Table 3, column 2: standard error 0.045 in the paper, 0.046 when regenerated. Likely cause: a newer package version. Do you want to update the paper or pin the old version?]
2. [Table A1 has no program in the package. Please send it, or confirm the table should go.]
3. [Please check the data availability statement and the licence in the README.]

NOT COVERED
- [Restricted data: I did not receive or run X. Please run main.do on your computer and send me the output folder, and I will compare it.]

AI USE AND ACKNOWLEDGEMENT
- I used AI-assisted coding tools for parts of this work. I reviewed every change, and the reproduction report shows the outputs did not change. If [journal] asks authors to acknowledge help with the replication package, please mention it.

Included: one round of changes after the data editor's report, until [date].

[Your name]
```
