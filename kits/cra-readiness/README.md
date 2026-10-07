# CRA readiness kit

A starter kit for one paid service: an **EU Cyber Resilience Act (CRA) readiness pack** for micro and small makers of connected hardware, firmware and downloadable software sold in the EU. It comes with scripts that do the technical work, document templates, and a finished sample for a fictional product that you can show to prospects.

> **Beginner level: 2 out of 5** in the playbook. The scripts do the technical work, but the policies and the reporting plan need some security knowledge. For your first jobs, work with an experienced reviewer or partner who checks the documents before you deliver them.

> **Not legal advice.** This kit prepares technical documents. It never makes a product "CRA compliant" on its own. Dates and duties below come from Regulation (EU) 2024/2847 as published: **verify current dates** before you rely on them.

**Contents:** [Why now](#why-now) · [The offer](#the-offer) · [Who buys](#who-buys-and-where-to-find-them) · [Prices](#price-guide) · [Process](#step-by-step-process) · [Delivery checklist](#delivery-checklist) · [Rules](#rules) · [Tools](#set-up-the-tools) · [Scripts](#how-to-run-each-script) · [Files](#whats-in-this-folder) · [Limits](#limits-to-know)

## Why now

- **Since 11 September 2026** manufacturers must report **actively exploited vulnerabilities** and **severe incidents** affecting their products to ENISA's single reporting platform: an **early warning within 24 hours**, a **notification within 72 hours**, and a **final report** (for a vulnerability, within 14 days after a fix or workaround is available; for a severe incident, within one month after the notification). This also covers products already on the market. *Verify current dates.*
- **From 11 December 2027** everything else applies: the essential security requirements, an SBOM, vulnerability handling, a support period, technical documentation, the EU declaration of conformity and CE marking. *Verify current dates.*
- Fines for breaking the core duties can reach €15 million or 2.5% of worldwide yearly turnover, whichever is higher. *Verify.*
- Small makers rarely have any of it: no SBOM, no security contact, no disclosure policy, no plan for a 24-hour report, no stated support period. That is the gap you fill.

## The offer

A fixed-price pack per product, delivered in about a week:

| Deliverable | Format | Made with |
|---|---|---|
| Software bill of materials (SBOM) for the release | CycloneDX 1.6 JSON + readable table (.xlsx, .md) | `scripts/make_sbom.py` |
| Known-vulnerability report with an ordered action list | .docx, .xlsx, .md | `scripts/vuln_report.py` |
| Vulnerability handling and coordinated disclosure policy | .docx, .md | `scripts/fill_templates.py` |
| security.txt (RFC 9116) | plain text | `scripts/make_security_txt.py` |
| Reporting runbook: 24 h, 72 h, final report, roles | .docx, .md | `scripts/fill_templates.py` |
| Support-period statement (customer text + internal reasons) | .docx, .md | `scripts/fill_templates.py` |
| CRA gap checklist: plain-English requirements, status, evidence, owner | .xlsx | `scripts/make_gap_checklist.py` |
| Handover note with the client's to-do list | .docx, .md | `scripts/fill_templates.py` |

Then offer **monthly care** to keep the SBOM and vulnerability checks current.

See the finished example in [samples/mossbyte-sprout-s1/](samples/mossbyte-sprout-s1/) and ready-to-send messages in [templates/offer.md](templates/offer.md).

**Put your own name on the sample.** In [samples/mossbyte-sprout-s1/client.json](samples/mossbyte-sprout-s1/client.json), change `consultant_name` and `consultant_email` (under `engagement`) to your name, business and email. Then rebuild the sample from the repository root (see [Set up the tools](#set-up-the-tools) first):

```sh
CRA_PY=~/.cache/cra-readiness/venv/bin/python bash kits/cra-readiness/scripts/build_sample.sh
```

It takes a few minutes and needs the network. The vulnerability numbers may change, because the databases are updated every day.

## Who buys, and where to find them

**Buyers:** founders and lead engineers of companies with 1 to 50 people that sell a connected product in the EU: a device with firmware, often with an app or cloud service, or downloadable software. They are worried about the CRA but have no security team and no budget for a big consultancy.

**Where to find them:**

- **Crowd Supply.** Open-hardware campaigns and store listings. Look for products with Wi-Fi, Bluetooth, LoRa or an app that ship to the EU.
- **Tindie.** Small sellers of boards, sensors and kits with firmware. Many ship worldwide, including the EU.
- **Kickstarter** (Technology and Design categories). Hardware campaigns that ship to EU backers. Campaigns close to shipping have a deadline and a reason to act.
- **EU startup networks.** Hardware accelerators and incubators, university spin-off programmes, European Digital Innovation Hubs, the Enterprise Europe Network, national startup associations, and local IoT and maker meetups. Offer a short talk or a free checklist review session.
- **Partners who meet these makers first.** CE and radio test labs, product-compliance consultants, electronics design houses and contract manufacturers. Offer them a referral fee or a white-label price.
- **Indie software sellers** in the EU: desktop apps, plug-ins and downloadable tools.

**A good opening:** check whether the product has a security contact (a security page or `/.well-known/security.txt`). If it has public code, you can mention that you could run a free SBOM and vulnerability check on it, with their permission.

**Etiquette:** one personal message per company, through the platform's contact feature or the business contact on their website. Rules on unsolicited email differ between EU countries, so prefer contact forms and platform messages, and never send bulk mailings. Follow each platform's rules, and never post sales pitches in campaign comments.

## Price guide

| Package | Fits | Price (estimate) |
|---|---|---|
| Starter | One product, one codebase (for example a desktop app, or a device with one firmware) | €500 to €700 |
| Standard | A device with firmware plus an app and/or cloud service (two or three codebases) | €900 to €1,400 |
| Extended | Several variants or versions, larger codebases, plus a practice run of the runbook | €1,500 to €2,000 |
| Monthly care | New SBOM for each release, monthly vulnerability check with a "what changed" note, security.txt renewal, checklist update | €100 to €300 per month |

Prices are estimates from the October 2026 research. Check what your market pays.

Quote per product, not per hour. Ask new clients for 50% up front. Your first two or three clients can be at the lower end in exchange for a testimonial.

## Step-by-step process

1. **Find and message prospects.** Use [templates/offer.md](templates/offer.md). Link to your sample pack.
2. **15-minute call.** Which products, which parts (firmware, app, cloud), which codebases, any deadline. Pick the package and send the quote (message 4 in the offer file).
3. **Agreement and deposit.** Include the rules below in the quote. Then send the [client questionnaire](templates/client-intake-questionnaire.docx).
4. **Collect inputs.** Read-only access to the code, or just the dependency files (`requirements.txt`, `poetry.lock`, `package.json` with `package-lock.json`...), plus a list of firmware components (SDK, RTOS, libraries with versions) in the format of [templates/extra-components.csv](templates/extra-components.csv).
5. **Make a private client folder** outside this repository, or under `kits/cra-readiness/clients/` (that folder is ignored by git). Copy [templates/client.example.json](templates/client.example.json) into it as `client.json` and fill it from the questionnaire.
6. **SBOM.** Run `make_sbom.py`. Read the notes it prints (unpinned versions, missing lockfiles). Send the component table to the client and ask them to confirm it matches what they ship.
7. **Vulnerability report.** Run `vuln_report.py`. Read the action list and check that it makes sense. Check the hand-listed firmware components yourself (the spreadsheet lists where to look).
8. **Documents.** Run `fill_templates.py`, then read every document from start to finish and adjust it to the client.
9. **security.txt.** Run `make_security_txt.py`, then check it with `--check`.
10. **Gap checklist workshop.** 60 to 90 minutes with the client. Fill in Status, Evidence, Owner and Target date. Mark scope, category and role questions "Needs lawyer".
11. **Run the delivery checklist** below.
12. **Deliver and hand over.** Send the files with the handover note and walk through it on a 30-minute call. Offer monthly care.
13. **Monthly care.** For each new release: run `make_sbom.py` again. Every month: run `vuln_report.py` with `--previous` pointing to last month's `findings.json` (and the same `--node-project` folders as the first report, if you still have the code), and send the "what changed" summary. Renew security.txt a month before it expires.

## Delivery checklist

- [ ] The client has confirmed the SBOM matches the shipped release, or the SBOM is clearly marked as a draft waiting for confirmation.
- [ ] `fill_templates.py` reported no placeholders left, and you read every document.
- [ ] Every vulnerability finding has an action, and every hand-listed component has been checked or is clearly marked for checking.
- [ ] `make_security_txt.py --check` shows no errors, the Expires date is less than a year away, and the addresses are the client's real ones.
- [ ] Dates and duties checked against official sources (see Further reading).
- [ ] No "CRA compliant", "certified" or "guaranteed" anywhere.
- [ ] The legal questions for the client's lawyer are listed (scope, category, role, safe-harbour wording, other EU rules such as radio equipment rules).
- [ ] The SBOM file name has the product and version, and its SHA-256 in the report matches the file.
- [ ] Client code and data are stored privately, and deleted from temporary places when the job is done.

## Rules

1. **Not legal advice.** Say so in your quote and in every deliverable.
2. **Never claim "CRA compliant"**, never call a product certified, and **never sign** (or offer to sign) the EU declaration of conformity. The manufacturer signs it after the conformity assessment.
3. **Classification and scope questions go to the client's lawyer**: whether the CRA applies, the product category (default, important, critical), the client's role (manufacturer, importer, distributor), and how conformity is assessed.
4. **The client confirms that the SBOM matches what ships.** Until then it is a draft.
5. **Verify current dates** before every delivery. The rules and the guidance around them are still settling.
6. **Read-only access only.** Never ask for production passwords, signing keys or customer data. Only scan code you have permission to scan.
7. Keep each client's work out of this repository: use a private repository or folder per client.

## Set up the tools

The scripts need Python 3.10+ and Node.js 20+. The kit's tools install into one folder, never globally:

```sh
bash kits/setup.sh cra-readiness                          # the usual route: installs into ~/.cache/cra-readiness
bash kits/cra-readiness/scripts/setup.sh /path/to/tools   # or this kit's tools only, into a folder of your choice
export CRA_PY=~/.cache/cra-readiness/venv/bin/python      # the Python the scripts must run with
```

`bash kits/setup.sh cra-readiness` also installs the system tools the other kits use, and `bash kits/setup.sh --list` shows where each kit's Python is. To install only this kit's tools, run `bash kits/cra-readiness/scripts/setup.sh` (into `~/.cache/cra-readiness`) or give it a folder, as above.

This installs cyclonedx-py, pip-audit, openpyxl, python-docx and Jinja2 into `<folder>/venv`, and cyclonedx-npm and cdxgen into `<folder>/npm`. The scripts find the Node tools automatically when they sit next to the virtualenv; otherwise set `CRA_NPM_TOOLS=<folder>/npm`. In a temporary cloud session, run the setup again in each new session (it takes about a minute).

**Network:** the scripts need the PyPI and npm registries. They also try the OSV vulnerability database (api.osv.dev; if it is blocked they fall back to OSV's public data files) and CISA's known-exploited list (cisa.gov, or its GitHub copy). If a source is blocked, the report says so. You can download CISA's list in your own browser and pass it with `--kev-file`.

## How to run each script

All commands run from the repository root with the kit's Python (`$CRA_PY`). The examples keep the client's files in `kits/cra-readiness/clients/acme/`, a folder that git ignores (see step 5). Add `--help` to any script for every option.

### make_sbom.py: the SBOM

```sh
"$CRA_PY" kits/cra-readiness/scripts/make_sbom.py \
  path/to/backend path/to/app \
  --extra-components kits/cra-readiness/clients/acme/firmware-components.csv \
  --client kits/cra-readiness/clients/acme/client.json --product-type device \
  --out kits/cra-readiness/clients/acme/2026-10/sbom
```

- Give it project folders (it detects Python or Node) and/or existing CycloneDX JSON files from the client's own build.
- Python: reads `requirements.txt`, `pyproject.toml`, `poetry.lock` or `Pipfile.lock`. By default it installs the requirements into a throwaway folder to find indirect dependencies too. Use `--python-mode requirements` to read the file only.
- Node: uses `package-lock.json` (no `node_modules` needed). Without a lockfile it resolves `package.json` today and warns you. For `yarn.lock` or `pnpm-lock.yaml` it uses cdxgen.
- Firmware and anything else no tool can see: list it in a CSV ([template](templates/extra-components.csv)). One row whose name equals the part name describes the part itself.
- Development-only dependencies are left out unless you add `--include-dev`.
- Output: `<product>-<version>.cdx.json` (checked against the CycloneDX 1.6 schema), `<product>-<version>-components.xlsx` and `.md`, and one SBOM per part in `parts/`. With a single existing SBOM file as input, it only lists its components.

### vuln_report.py: the known-vulnerability report

```sh
"$CRA_PY" kits/cra-readiness/scripts/vuln_report.py \
  kits/cra-readiness/clients/acme/2026-10/sbom/acme-sensor-1.4.0.cdx.json \
  --node-project path/to/app --client kits/cra-readiness/clients/acme/client.json \
  --out kits/cra-readiness/clients/acme/2026-10
```

- Python packages: pip-audit. Node packages: `npm audit --json` in each `--node-project` folder; any npm packages not covered that way are checked against the same npm advisory database directly, so a stored SBOM can be re-checked without the code. Other ecosystems (Go, Rust, Java...): OSV API, only if it can be reached.
- Adds severity, CVE numbers and fixed versions from OSV, and flags anything on CISA's known-exploited list.
- Groups findings into a short list of actions (for example "Update express from 4.18.2 to 4.22.3"), and warns about major version jumps.
- Output: `vulnerability-report.docx`, `.xlsx` (with a "Your assessment" column for the client) and `.md`, plus `vulnerability-data/` with `findings.json` and the raw tool output.
- Monthly: add `--previous kits/cra-readiness/clients/acme/2026-10/vulnerability-data/findings.json` to mark new findings and list fixed ones, and write to the new month's folder (`--out kits/cra-readiness/clients/acme/2026-11`). Keep the same `--node-project` folders if you still have the code. Without them, npm packages are checked through the npm advisory service instead of `npm audit`, so the action list can be grouped or worded differently even when the findings are the same.

### fill_templates.py: policy, runbook, support statement, handover note

```sh
"$CRA_PY" kits/cra-readiness/scripts/fill_templates.py --client kits/cra-readiness/clients/acme/client.json \
  --out kits/cra-readiness/clients/acme/2026-10
"$CRA_PY" kits/cra-readiness/scripts/fill_templates.py --client kits/cra-readiness/clients/acme/client.json \
  --out kits/cra-readiness/clients/acme/2026-10 --only policy,runbook
```

- Writes each document as `.md` and `.docx`. Anything missing from `client.json` appears as `[TO FILL: name]` and is listed at the end.
- `--blank --out kits/cra-readiness/templates` rebuilds the blank Word templates.

### make_security_txt.py: security.txt

```sh
"$CRA_PY" kits/cra-readiness/scripts/make_security_txt.py --client kits/cra-readiness/clients/acme/client.json \
  --out kits/cra-readiness/clients/acme/2026-10/security.txt
"$CRA_PY" kits/cra-readiness/scripts/make_security_txt.py --check kits/cra-readiness/clients/acme/2026-10/security.txt
```

- Builds the RFC 9116 fields (Contact, Expires, Encryption, Acknowledgments, Preferred-Languages, Canonical, Policy, Hiring, CSAF) from `client.json` or from options such as `--contact` and `--policy`.
- `--check` validates any security.txt file, including one the client already has. It exits with code 1 on errors.
- Publish the file at `https://<domain>/.well-known/security.txt`, served over HTTPS as plain text.

### make_gap_checklist.py: the gap checklist

```sh
"$CRA_PY" kits/cra-readiness/scripts/make_gap_checklist.py --client kits/cra-readiness/clients/acme/client.json \
  --out kits/cra-readiness/clients/acme/2026-10/cra-gap-checklist.xlsx
"$CRA_PY" kits/cra-readiness/scripts/make_gap_checklist.py --client kits/cra-readiness/clients/acme/client.json \
  --status kits/cra-readiness/clients/acme/gap-status.csv \
  --out kits/cra-readiness/clients/acme/2026-10/cra-gap-checklist.xlsx
```

- The 54 checklist items live in [templates/gap-checklist-items.csv](templates/gap-checklist-items.csv): our own plain-English paraphrase of the essential requirements (Annex I), user information (Annex II), reporting, support period and documentation duties, each with a reference to the regulation.
- Fill the yellow columns in Excel or LibreOffice during the workshop, or pre-fill them from a status CSV (columns `id,status,evidence,owner,target_date,notes`). The Summary sheet counts progress by area.

### Other scripts

- `setup.sh`: installs the tools (see above).
- `build_sample.sh`: rebuilds the blank templates and the whole sample (`CRA_PY=~/.cache/cra-readiness/venv/bin/python bash kits/cra-readiness/scripts/build_sample.sh`). Also a quick end-to-end test after you change anything.
- `md2docx.py`: turns any Markdown file into a tidy Word document next to it (`"$CRA_PY" kits/cra-readiness/scripts/md2docx.py kits/cra-readiness/clients/acme/2026-10/notes.md`).

## What's in this folder

```text
kits/cra-readiness/
├── README.md                  this file
├── requirements.txt           Python tools (installed by setup.sh)
├── package.json               Node tools (installed by setup.sh into a local folder)
├── scripts/                   make_sbom.py, vuln_report.py, fill_templates.py, make_security_txt.py,
│                              make_gap_checklist.py, md2docx.py, kitlib.py, setup.sh, build_sample.sh
├── templates/                 policy, runbook, support statement and questionnaire (.md sources +
│                              blank .docx), handover note (.md only), security.txt template, gap
│                              checklist (.xlsx + items CSV), client.example.json, extra-components.csv,
│                              offer.md
└── samples/mossbyte-sprout-s1 FICTIONAL portfolio sample: source projects, client.json, and the
                               generated deliverables
```

## Limits to know

- **SBOM coverage.** Python and Node projects are read automatically. Firmware written in C or C++ is listed by hand, so its accuracy depends on the client's answers. Other ecosystems can be merged in from an SBOM the client's own build produces.
- **Vulnerability checks** only find problems that have been published, and only for components that tools can identify. A listed vulnerability is not always exploitable in the product; the client's developers decide, and record why.
- **Hand-listed components** (SDKs, RTOS, C libraries) need a manual check in the vendor's advisories, OSV, the US National Vulnerability Database or the EU Vulnerability Database.
- **Spreadsheets** store both formulas and their results, so they show correct numbers in any viewer and recalculate when opened in Excel, LibreOffice or Google Sheets.
- **Templates** are a starting point. The client's lawyer must review the policy (especially the safe-harbour wording) and anything with legal effect.

## Further reading

- Regulation (EU) 2024/2847 (Cyber Resilience Act), official text: <https://eur-lex.europa.eu/eli/reg/2024/2847/oj>
- European Commission CRA page: <https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act>
- ENISA (single reporting platform and guidance): <https://www.enisa.europa.eu>
- CycloneDX SBOM standard: <https://cyclonedx.org>
- security.txt (RFC 9116): <https://www.rfc-editor.org/rfc/rfc9116>
- CISA Known Exploited Vulnerabilities catalogue: <https://www.cisa.gov/known-exploited-vulnerabilities-catalog>
- OSV vulnerability database: <https://osv.dev>
- Germany's BSI technical guideline TR-03183-2 describes what a good SBOM contains; useful when clients ask "is this SBOM good enough?".
