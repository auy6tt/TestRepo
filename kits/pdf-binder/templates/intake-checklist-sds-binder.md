# Intake checklist: safety data sheet (SDS) binder

Use this on the first call or email with a new client. Copy it into the client's folder and tick items off as they arrive.

## 1. About the client

- [ ] Business name, and the name to put on the invoice
- [ ] Site address (one binder per site unless you agree otherwise)
- [ ] Main contact: name, role, phone, email
- [ ] Who will confirm the final chemical list (owner, manager or safety lead)
- [ ] Rough number of employees and the work areas (for example: service bays, paint room, storage, janitorial closet, office, vans)
- [ ] Who trains staff on chemical hazards. This must be a qualified person, not you. Note the name if the client wants it in the binder.

## 2. Scope and price

- [ ] Number of sites and a rough count of products (count the shelves in the photos)
- [ ] What you deliver: inventory spreadsheet, binder PDF, printed binder (who prints it, how many copies), written programme draft (optional extra)
- [ ] Deadline (see "Dates" below; never use the OSHA date to scare anyone)
- [ ] Price and what it includes, for example: up to 40 products, extra products at $X each, rush fee for 48 hours
- [ ] How files are sent (shared folder or email) and that you use them only for this job

## 3. What the client sends

- [ ] Photos of every shelf, cabinet, cart, van and closet where chemicals are kept, with the front labels readable (product name and manufacturer)
- [ ] Purchase records for the last 12 months (supplier invoices, online orders)
- [ ] Their current SDS binder (photos or scans of the index and the sheets) or an export from their SDS software
- [ ] Supplier and distributor names (many have SDS downloads in the customer portal)
- [ ] Products they no longer use, so they can be left out (the client decides)
- [ ] Any existing written hazard communication programme

## 4. Your working steps

- [ ] Build the on-site list in `templates/sds-site-list-template.xlsx` from the photos and records
- [ ] Download the current SDS for each product from the manufacturer or supplier and save it as a PDF with a clear name
- [ ] Run `extract_sds.py` and work through every REVIEW, MISSING SDS, REPLACE: OLD FORMAT and CHECK FOR NEWER SDS row
- [ ] Request missing sheets from the manufacturer or supplier and note the date you asked
- [ ] Send the list (the Chemical List sheet) to the client to confirm, and record who confirmed it and when
- [ ] Fill in the cover file, build the binder with `build_binder.py`, then run `verify_binder.py`
- [ ] Open the binder and spot-check the cover, contents, some bookmarks and any PENDING pages
- [ ] Deliver: binder PDF, `inventory.xlsx`, the binder's index spreadsheet, and the written programme draft if ordered

## 5. Put this in writing

- You collect and organise the manufacturers' sheets. You don't write, change or "correct" any safety data sheet.
- You don't classify chemicals, assess hazards or give safety advice.
- The employer confirms the on-site list and is responsible for compliance and for staff training by a qualified person.

## Dates

OSHA revised its Hazard Communication Standard in 2024. Check the current compliance dates on osha.gov before you quote a deadline. The employer compliance date for single-substance chemicals is reported as 20 November 2026, with later dates for mixtures.
