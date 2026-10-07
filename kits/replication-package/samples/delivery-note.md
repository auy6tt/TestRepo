# Delivery note (sample)

*The message the (fictional) authors received with their cleaned package, written from templates/delivery-note.md. Replace [Your name] before you show it to anyone.*

```text
Subject: Replication package for "After-School Tutoring and Math Achievement": ready for your review

Dear Jane and John,

The cleaned replication package is in 3-fixed-package. In short:

RESULT
- The package now runs from one master script (main.py) in about 5 seconds on a 4-core Linux computer with Python 3.11.
- Run from a clean copy, starting from the raw data, it recreated all 4 tables and figures, and every file matches your originals byte for byte (4-comparison-report).
- Reports: 2-check-report (34 findings before the clean-up), 4-comparison-report (reproduction), 5-final-check (no findings after the clean-up).

WHAT I CHANGED (no estimates, data values or results were changed)
1. Added main.py. It creates the folders the programs need, runs the four programs in order and saves logs/main.log.
2. Replaced the hard-coded folders (C:/Users/jdoe/..., /Users/jroe/... and ~/Dropbox/...) with paths built from the package folder, and removed os.chdir(). No other line of the analysis changed.
3. Numbered the programs in run order: clean_data.py is now code/01_clean_data.py, analysis.py is code/02_analysis.py and figure1.py is code/03_figure1.py.
4. Added the Table A1 program you sent as code/04_tableA1_attrition.py. Only its file paths changed.
5. Pinned exact package versions in requirements.txt, and added numpy and scipy, which the code imports but the old file did not list.
6. Replaced data/raw/tutoring_pilot.csv with the de-identified version you approved (names, parent emails, phone numbers, home addresses and birth dates removed). The analysis never used those columns, and the comparison shows the results are unchanged.
7. Wrote README.md in the data editors' format, with the data availability statement, the data citation and the table and figure map. Added LICENSE.txt with the licences you chose (MIT for the code, CC0 for the data).
8. Left out old/robustness_check.do, which you confirmed is an unused 2022 check that is not in the paper (it also read a data file that is not in the package), and a stray Thumbs.db file.

DIFFERENCES AND QUESTIONS FOR YOU (you decide)
1. No differences: every number in Tables 1, 2 and A1, and the Figure 1 image, match your originals.
2. Please check the data availability statement and the data citation in the README. Only you can confirm what the district's data sharing agreement allows.
3. Optional, cosmetic: Table 1 and Table A1 print the student counts as 377.0 and 398.0, because those columns also hold decimals. I have not changed this. Tell me if you would like whole numbers in the paper's version.

NOT COVERED
- I did not compare the tables with the numbers quoted in the text of the paper.

AI USE AND ACKNOWLEDGEMENT
- I used AI-assisted coding tools for parts of this work. I reviewed every change, and the reproduction report shows the outputs did not change. The README's Acknowledgements section has a suggested sentence; edit or delete it to match the journal's rules.

Included: one round of changes after the data editor's report, until [date].

[Your name]
```
