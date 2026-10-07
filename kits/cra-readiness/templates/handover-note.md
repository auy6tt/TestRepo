<!--
TEMPLATE. Fill it with: python scripts/fill_templates.py --client client.json --out <folder>
Send this with the deliverables. Book a 30-minute handover call to walk through it.
-->
# Handover: CRA readiness pack for {{ products[0].name }}

- **For:** {{ company.contact_person }}, {{ company.legal_name }}
- **From:** {{ engagement.consultant_name }} ({{ engagement.consultant_email }})
- **Date:** {{ today | longdate }} · **Reference:** {{ engagement.reference }}
- **Files:** {{ engagement.deliverables_folder }}

## What is in the pack

| Deliverable | File | What to do with it |
|---|---|---|
| Software bill of materials (SBOM) | `sbom/*.cdx.json` and `sbom/*-components.xlsx` | Check that the list matches what you ship, then confirm (see below). Keep one SBOM per release. |
| Known-vulnerability report | `vulnerability-report.docx` / `.xlsx` | Plan the actions at the top. Fill in 'Your assessment' for each finding. |
| Vulnerability handling and disclosure policy | `vulnerability-handling-policy.docx` | Lawyer review, then publish at {{ contacts.policy_url }}. |
| security.txt | `security.txt` | Publish at {{ contacts.security_txt_url }}. Renew it before the Expires date. |
| Reporting runbook | `reporting-runbook.docx` | Complete 'Before you need it', print it, and schedule a practice run. |
| Support period statement | `support-period-statement.docx` | Management approves the dates, then put the customer text on the product page. |
| CRA gap checklist | `cra-gap-checklist.xlsx` | Work through the open items with their owners. |

## What we need from you

- [ ] **Confirm the SBOM.** Check that the component list matches the release you actually ship, including the firmware libraries we listed by hand. Fill in the 'Client confirmation' box on the About sheet. Until you do, the SBOM is a draft.
- [ ] **Assess the vulnerability findings** with your developers: fix, or write down why a finding cannot be exploited in your product.
- [ ] **Check the components marked for a manual check** (mostly firmware libraries) against the vendors' security advisories.
- [ ] **Lawyer review:** whether and how the CRA applies to each product, the product category, your role, the safe-harbour wording in the policy, the reporting duties, and other EU rules that apply (for example radio equipment rules for wireless products).
- [ ] **Approve the support period** and publish the end date where customers see it before buying.
- [ ] **Publish** the policy and security.txt, and make sure a person reads {{ contacts.security_email }} every working day.
- [ ] **Get access to ENISA's single reporting platform** for the incident lead and deputy.

## What this pack is, and is not

- It is technical preparation to help you meet the Cyber Resilience Act. It is **not legal advice**.
- It does **not** make a product "CRA compliant" on its own, and we do not use that phrase.
- We do not decide whether the CRA applies, which category your product is in, or how its conformity must be assessed. Those questions go to your lawyer.
- We never sign the EU declaration of conformity. The manufacturer does that, after the conformity assessment.
- The SBOM and vulnerability report are only as complete as the dependency files and component lists we received.
- Dates and duties are summarised from Regulation (EU) 2024/2847 as we understand it today. Verify current dates.

## Keeping it current

New vulnerabilities are published every day, and every release changes the SBOM. Our monthly plan: {{ engagement.monthly_plan }}.

Thank you. Questions: {{ engagement.consultant_email }}
