# Sample pack: Sprout S1 plant sensor (FICTIONAL)

> **Everything about this company is made up.** Mossbyte Labs, its staff, address, phone numbers and the `.example` web addresses do not exist. The source projects are small but real, so the SBOM and vulnerability tools produced real output from public databases on 7 October 2026. Use this folder as your portfolio sample: show it to prospects so they can see exactly what they would get.

## The story

Mossbyte Labs is a six-person company in Ghent, Belgium. Its product, the **Sprout S1**, is a Wi-Fi soil-moisture and light sensor for house plants, sold online across the EU and through a Crowd Supply campaign. It has three parts:

| Part | What it is | Source in this folder |
|---|---|---|
| sprout-fw 2.3.0 | Sensor firmware for the ESP32-C3 chip, built with ESP-IDF | [source/firmware-components.csv](source/firmware-components.csv) (listed by hand) |
| Sprout Cloud 2.3.0 | Python (Flask) service that receives readings and sends watering alerts | [source/sprout-cloud/](source/sprout-cloud/) |
| Sprout Companion 2.3.0 | Node.js desktop tool with a local dashboard | [source/sprout-companion/](source/sprout-companion/) |

Mossbyte asked for the **Standard** package. Its answers to the questionnaire are in [client.json](client.json), and the checklist workshop results are in [gap-status.csv](gap-status.csv).

## The deliverables

| Deliverable | Files |
|---|---|
| SBOM for release 2.3.0 (CycloneDX 1.6, schema-checked) | [deliverables/sbom/sprout-s1-2.3.0.cdx.json](deliverables/sbom/sprout-s1-2.3.0.cdx.json), readable list: [.md](deliverables/sbom/sprout-s1-2.3.0-components.md) / [.xlsx](deliverables/sbom/sprout-s1-2.3.0-components.xlsx), one SBOM per part in [sbom/parts/](deliverables/sbom/parts/) |
| Known-vulnerability report | [.docx](deliverables/vulnerability-report.docx) / [.xlsx](deliverables/vulnerability-report.xlsx) / [.md](deliverables/vulnerability-report.md), raw data in [vulnerability-data/](deliverables/vulnerability-data/) |
| Vulnerability handling and disclosure policy (filled in) | [.docx](deliverables/vulnerability-handling-policy.docx) / [.md](deliverables/vulnerability-handling-policy.md) |
| security.txt | [deliverables/security.txt](deliverables/security.txt) |
| Reporting runbook (24 h / 72 h / final report, roles) | [.docx](deliverables/reporting-runbook.docx) / [.md](deliverables/reporting-runbook.md) |
| Support-period statement | [.docx](deliverables/support-period-statement.docx) / [.md](deliverables/support-period-statement.md) |
| CRA gap checklist, partly filled in | [deliverables/cra-gap-checklist.xlsx](deliverables/cra-gap-checklist.xlsx) |
| Handover note | [.docx](deliverables/handover-note.docx) / [.md](deliverables/handover-note.md) |

## What the sample shows (as generated on 7 October 2026)

- **137 components** across three parts: 16 Python packages, 116 npm packages and 5 firmware components listed by hand.
- **26 known vulnerabilities** (6 high, 13 medium, 7 low) in 12 components, none on CISA's known-exploited list. They come down to **6 actions**, led by "Update express from 4.18.2 to 4.22.3", which alone fixes 12 findings.
- The 5 firmware components (ESP-IDF, FreeRTOS, Mbed TLS, lwIP, cJSON) are flagged for a manual check, with links to where to look.
- The gap checklist is partly filled in: 9 items done, 22 in progress, 16 not started, 6 waiting for the lawyer and 1 not applicable.

Because new vulnerabilities are published every day, running the build again later will give different numbers. That is normal, and it is exactly what the monthly care plan sells.

## Rebuild it

To put your own name on the sample, first change `consultant_name` and `consultant_email` (under `engagement`) in [client.json](client.json). Then, from the repository root, after setting up the tools (see the kit [README](../../README.md#set-up-the-tools)):

```sh
CRA_PY=~/.cache/cra-readiness/venv/bin/python bash kits/cra-readiness/scripts/build_sample.sh
```

The script runs every step in order: `make_sbom.py`, `vuln_report.py`, `fill_templates.py`, `make_security_txt.py` and `make_gap_checklist.py`. Read [scripts/build_sample.sh](../../scripts/build_sample.sh) to see the exact commands, which are the same ones you run for a real client.
