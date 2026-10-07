# Intake checklist: submittal packages and handover (O&M) binders

Use this on the first call with a subcontractor. Copy it into the project folder and tick items off as they arrive.

## 1. Project and people

- [ ] Project name, number and address
- [ ] Your client (the subcontractor): company, project manager, phone, email
- [ ] General contractor, architect or engineer, and owner, spelled as they should appear on covers
- [ ] Who signs and stamps the package: the subcontractor's project manager. You never sign or stamp.

## 2. The project's rules (ask for these documents)

- [ ] The specification section on submittal procedures, and the general contractor's own submittal instructions
- [ ] The specification sections on operation and maintenance data, warranties and record documents (for handover binders)
- [ ] The technical specification section for each product in the package
- [ ] The general contractor's cover sheet or transmittal form, if they have one (use theirs)
- [ ] Required order of documents and tab names
- [ ] File naming rules, file size limit, whether bookmarks and page numbers are required
- [ ] Where the package is uploaded (for example Procore or Autodesk Build) and who uploads it
- [ ] Paper copies: how many, binder size, tab dividers, spine labels

## 3. The documents (from the project manager)

- [ ] Equipment or product list with tags (such as RTU-1, EF-1), model numbers and spec sections
- [ ] Product datasheets, with the selected model and options marked by the project manager (or exact written instructions for what to mark)
- [ ] Shop drawings, certificates and test reports, if they belong in this package
- [ ] Installation, operation and maintenance manuals
- [ ] Warranties: start date (often substantial completion), term, serial numbers
- [ ] Spare parts and attic stock lists, contact list, maintenance schedule
- [ ] Record drawings
- [ ] Reviewer comments from the last round, for a resubmittal

## 4. Scope and price

- [ ] Package type: submittal package, handover binder, or both
- [ ] Number of packages and a rough page count
- [ ] Turnaround time and rush fee
- [ ] Revisions included (for example one round of changes; resubmittals priced separately)
- [ ] Confidentiality: drawings and specifications belong to the project; don't share or reuse them

## 5. Your working steps

- [ ] Build the index in `templates/binder-index-template.xlsx`, in the general contractor's order
- [ ] Fill in the cover file (`templates/binder-cover-submittal.toml` or `binder-cover-handover.toml`)
- [ ] Optional: draft a checklist showing where each specification requirement appears in the package. The project manager confirms compliance, not you.
- [ ] Build with `build_binder.py`, run `verify_binder.py`, then check the binder by eye
- [ ] Update the submittal log (`templates/submittal-log.xlsx`)
- [ ] Send the package to the project manager to review and sign before it goes to the general contractor

## 6. Put this in writing

- You assemble and organise documents. You don't alter manufacturer documents and you don't certify compliance.
- The subcontractor's project manager reviews and signs; the design team approves.
