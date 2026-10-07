---
name: cra-readiness
description: Prepare an EU Cyber Resilience Act (CRA) readiness pack for a small maker of connected hardware, firmware or downloadable software, using the scripts and templates in kits/cra-readiness. Produces a CycloneDX SBOM, a known-vulnerability report, a vulnerability handling and coordinated disclosure policy, a security.txt file, a 24h/72h reporting runbook, a support-period statement and a CRA gap checklist.
when_to_use: Use when the user mentions the Cyber Resilience Act or CRA, asks for an SBOM or CycloneDX file, a vulnerability check or report on a client's dependencies, security.txt, a disclosure policy, an ENISA incident or vulnerability reporting runbook, a support period statement, a CRA gap analysis or checklist, a monthly re-check for a CRA client, or wants to sell or quote this service.
argument-hint: "[client folder or product name]"
---

# CRA readiness pack

You help a freelancer deliver a paid, fixed-price CRA readiness pack. The kit lives in `kits/cra-readiness/` at the repository root. Read `kits/cra-readiness/README.md` once for the offer, prices and process. The finished example is `kits/cra-readiness/samples/mossbyte-sprout-s1/` (a fictional company).

Target for this request: $ARGUMENTS

## Ground rules (never break these)

1. **Not legal advice.** Every deliverable and quote says so.
2. **Never write that a product is "CRA compliant"**, "certified" or "guaranteed compliant". Never sign, or offer to sign, the EU declaration of conformity. The manufacturer signs it after the conformity assessment.
3. **Scope, product category (default, important, critical), legal role and conformity-assessment questions go to the client's lawyer.** List them; do not answer them.
4. **The client confirms that the SBOM matches what ships.** Until they do, call it a draft.
5. **Dates: write "verify current dates"** next to CRA dates. Reporting duties apply from 11 September 2026 (early warning within 24 hours, notification within 72 hours; final report within 14 days after a fix is available for an actively exploited vulnerability, or within one month after the notification for a severe incident) through ENISA's single reporting platform. Everything else applies from 11 December 2027.
6. Read-only access to client code. Never ask for production passwords, signing keys or customer data. Keep client work out of this repository: use a private folder or `kits/cra-readiness/clients/` (ignored by git).
7. Plain, clear English. Short sentences.

## Set up the tools (once per session)

The usual setup route is `bash kits/setup.sh cra-readiness` (see kits/README.md and PLAYBOOK.md). It installs the tools in `~/.cache/cra-readiness`, and `bash kits/setup.sh --list` shows the kit's Python there (`~/.cache/cra-readiness/venv/bin/python`). Run this block from the repository root. It uses those tools, or installs them if they are missing:

```sh
TOOLS="${TOOLS:-$HOME/.cache/cra-readiness}"   # where kits/setup.sh cra-readiness installs; or set your own scratch folder
test -x "$TOOLS/venv/bin/python" || bash kits/cra-readiness/scripts/setup.sh "$TOOLS"
export CRA_PY="$TOOLS/venv/bin/python" CRA_NPM_TOOLS="$TOOLS/npm"
```

If `bash kits/setup.sh cra-readiness` already ran, leave TOOLS unset and the install is skipped. Otherwise the block installs only this kit's tools (about a minute); you may set TOOLS to a folder inside the session's scratchpad first. Nothing is installed globally. `"$CRA_PY"` in the commands below is the kit's Python. If a later command finds `$CRA_PY` empty (some shells do not keep variables between commands), run the block again in the same command; it is quick once the tools are there. Never use a bare `python` or `python3` for the scripts. The scripts need the PyPI and npm registries. The OSV API and cisa.gov may be blocked: the scripts fall back to OSV's data files and the GitHub copy of CISA's list, and the report says what was used. If the known-exploited list cannot be reached, ask the user to download `known_exploited_vulnerabilities.json` and pass it with `--kev-file`.

## Workflow for a new client

Keep every client file in the client's folder `<client>` = `kits/cra-readiness/clients/<name>/` (ignored by git), or in a private folder outside this repository. `<out>` below is `<client>/<YYYY-MM>`. Never write client files anywhere else in the repository: it is public.

1. **Intake.** Send `templates/client-intake-questionnaire.docx`. Copy `templates/client.example.json` to `<client>/client.json` and fill it from the answers. Leave nothing in [brackets].
2. **Firmware components.** Put SDKs, RTOS and C libraries (with versions) in `<client>/firmware-components.csv`, in the format of `templates/extra-components.csv`. One row whose name equals the part name describes the firmware itself.
3. **SBOM.**
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/make_sbom.py <python-folder> <node-folder> [existing.cdx.json] \
     --extra-components <client>/firmware-components.csv --client <client>/client.json --product-type device --out <out>/sbom
   ```
   Read every WARNING it prints (unpinned versions, missing lockfiles, install failures) and pass them to the client as questions. Confirm "Schema check: ... is valid". Use `--product-type application` for software-only products.
4. **Vulnerability report.**
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/vuln_report.py <out>/sbom/<product>-<version>.cdx.json \
     --node-project <node-folder> --client <client>/client.json --out <out>
   ```
   Check that the action list makes sense (versions, major-version warnings). Never invent CVE numbers, severities or fixed versions: use only what the tools report. Hand-listed components appear under "Need a manual check"; say so plainly rather than guessing.
5. **Documents.**
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/fill_templates.py --client <client>/client.json --out <out>
   ```
   Fix every `[TO FILL: ...]` it lists by editing client.json and running it again. Then read each document and adapt it to the client.
6. **security.txt.**
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/make_security_txt.py --client <client>/client.json --out <out>/security.txt
   "$CRA_PY" kits/cra-readiness/scripts/make_security_txt.py --check <out>/security.txt
   ```
7. **Gap checklist.** Build it, then fill the yellow columns with the client in a 60 to 90 minute workshop (or pre-fill from a status CSV with columns `id,status,evidence,owner,target_date,notes`):
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/make_gap_checklist.py --client <client>/client.json [--status <client>/gap-status.csv] \
     --out <out>/cra-gap-checklist.xlsx
   ```
8. **Delivery checklist** (from the kit README): SBOM confirmed or marked draft; no placeholders; every finding has an action; security.txt passes `--check`; dates verified; no compliance claims; legal questions listed; client data private.
9. **Handover.** Send the files with `handover-note.docx` and offer monthly care.

## Monthly care

- New release: run `make_sbom.py` again with the new version.
- Every month: run `vuln_report.py` on the latest SBOM with `--previous <last-month>/vulnerability-data/findings.json` and `--out <client>/<new YYYY-MM>`. Pass the same `--node-project <node-folder>` as the first report when you still have the code. Without it, npm packages are checked through the npm bulk advisory service instead of `npm audit`, so the action list can be grouped or worded differently even when the findings did not change; tell the client so if the wording moves. Send a short note: new findings, fixed findings, top actions.
   ```sh
   "$CRA_PY" kits/cra-readiness/scripts/vuln_report.py <client>/<YYYY-MM>/sbom/<product>-<version>.cdx.json \
     --node-project <node-folder> --client <client>/client.json \
     --previous <client>/<last YYYY-MM>/vulnerability-data/findings.json --out <client>/<new YYYY-MM>
   ```
- A month before security.txt expires: make a new one.
- Every quarter: check the runbook contacts and the checklist owners.

## Other jobs

- **Quote or outreach message:** adapt `templates/offer.md`. Mention one specific detail about the prospect's product. One message per company, no bulk mailing.
- **Check a client's existing security.txt:** `"$CRA_PY" kits/cra-readiness/scripts/make_security_txt.py --check <file>`.
- **List an SBOM the client already has:** `"$CRA_PY" kits/cra-readiness/scripts/make_sbom.py <client>/client-sbom.cdx.json --out <out>/sbom`.
- **Any Markdown to Word:** `"$CRA_PY" kits/cra-readiness/scripts/md2docx.py <out>/file.md` (writes `file.docx` next to it).
- **Put the user's name on the portfolio sample:** change `consultant_name` and `consultant_email` (under `engagement`) in `kits/cra-readiness/samples/mossbyte-sprout-s1/client.json`, then rebuild it with `CRA_PY="$CRA_PY" bash kits/cra-readiness/scripts/build_sample.sh`.
- **After changing the kit:** run `CRA_PY="$CRA_PY" bash kits/cra-readiness/scripts/build_sample.sh` to rebuild the blank templates and the sample, as an end-to-end test (it also checks a relative `--out` folder).

## Troubleshooting

- *yarn.lock or pnpm-lock.yaml:* make_sbom uses cdxgen automatically (installed by setup.sh).
- *Python requirements will not install* (private packages, build errors): make_sbom falls back to reading the file only and warns that indirect dependencies are missing. Ask the client for `pip freeze` output from the release build, or for an SBOM from their CI.
- *Firmware in C/C++:* no tool here reads it. List the components by hand and check them manually; say so in the report.
- *"Not rated" severity:* OSV data was unreachable. Re-run later, or read the advisory link.
