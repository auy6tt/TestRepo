# Client intake checklist

*Send the questions before you quote. Keep the answers in the client's folder.*

## 1. Paper and deadline

- [ ] Paper title, authors, journal
- [ ] Stage: conditionally accepted, data editor report received, or preparing ahead
- [ ] Deadline for the replication package
- [ ] The data editor's report, if there is one (ask for the file)
- [ ] Link to the journal's data and code policy
- [ ] Number of tables and figures (paper, appendix, online appendix)

## 2. Code

- [ ] Software and exact versions (Stata version and edition, R, Python, MATLAB, SAS, other)
- [ ] Number of programs, roughly how many lines
- [ ] Is there a master script? A README?
- [ ] Community packages used (Stata ado files, R packages, Python libraries)
- [ ] How long a full run takes on their computer, and on what computer
- [ ] Anything special: computing cluster, large memory, paid software, internet downloads during the run

## 3. Data

- [ ] Every dataset: source, public or restricted, size
- [ ] Any data they cannot share with you (confidential, licensed, under a data use agreement)?
  If yes, those data stay with the client. You work on the code only, and the client runs the
  package on their side and sends you the output folder to compare.
- [ ] Any personal data (names, contact details, addresses, exact locations, birth dates)?
- [ ] May the data be published in the journal's repository, and under which licence?
- [ ] A citation (with a DOI or web address) for each dataset

## 4. Scope

- [ ] README and structure check only
- [ ] Full clean-up: master script, paths, pinned packages, logs, README, table and figure map,
      reproduction run and comparison report
- [ ] Migration of old code (for example an old Stata version, or SAS to R or Python): quote separately
- [ ] One round of changes after the data editor's report: included until [date]
- [ ] Agreed in writing: if results differ, the author decides. You never change estimates.

## 5. Practicalities

- [ ] How files are shared: private Git repository, shared folder or zip. Never restricted data by email.
- [ ] Main contact and time zone
- [ ] Does the journal require acknowledging paid help? How do they want it worded?
- [ ] AI tools: tell them you use AI-assisted coding tools under your review, and get their OK.
      Check that their data agreement allows it. Turn off model training in your tools' privacy settings.
- [ ] Price, payment terms (for example 50% upfront), invoice details

## Stop and talk first if

- They ask you to change estimates, drop observations or "make the numbers match"
- They ask you to recreate a table or figure by hand
- They offer restricted data that their agreement does not let them share
- The deadline is under 48 hours for a full clean-up
