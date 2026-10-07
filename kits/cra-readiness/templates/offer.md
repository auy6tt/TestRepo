# Offer texts: CRA readiness pack

Starting points for your messages and quotes. Replace everything in [brackets]. Write to one company at a time and mention something specific about their product. No mass mailings.

## The offer in one sentence

I help small makers of connected hardware and software get ready for the EU Cyber Resilience Act: a software bill of materials, a known-vulnerability report, a disclosure policy, a security.txt file, a 24/72-hour reporting runbook, a support-period statement and a gap checklist, delivered in about a week, from €500 per product.

## What the client gets

- **SBOM** (CycloneDX, machine-readable) for the current release, plus a readable component list.
- **Known-vulnerability report** with a short, ordered list of what to update first.
- **Vulnerability handling and coordinated disclosure policy**, ready for their lawyer to review.
- **security.txt** file (RFC 9116) so researchers know where to report.
- **Reporting runbook** for actively exploited vulnerabilities and severe incidents: who does what within 24 hours, 72 hours and up to the final report.
- **Support-period statement**: customer text plus the internal reasoning.
- **Gap checklist** against the CRA's essential requirements in plain English, with status, evidence and owner for each item.
- A 30-minute handover call.

## Price guide

| Package | Fits | Price |
|---|---|---|
| Starter | One product with one codebase (for example a desktop app, or a device with one firmware) | €500 to €700 |
| Standard | One device with firmware plus an app and/or cloud service (two or three codebases) | €900 to €1,400 |
| Extended | Several variants or versions, larger codebases, plus a practice run of the reporting runbook | €1,500 to €2,000 |
| Monthly care | New SBOM for each release, monthly vulnerability check with a "what changed" note, security.txt renewal, checklist update | €100 to €300 per month |

Ask for 50% up front for new clients. Quote per product, not per hour.

## Message 1: to a maker on Crowd Supply, Tindie or Kickstarter

```text
Subject: [Product name] and the EU Cyber Resilience Act

Hi [first name],

I came across [product name] on [Crowd Supply / Tindie / Kickstarter] and saw you ship to the EU. [One honest sentence about what you liked.]

Since 11 September 2026, makers of connected products sold in the EU must report actively exploited vulnerabilities and severe incidents within 24 hours, and the rest of the Cyber Resilience Act applies from December 2027 (worth checking with your lawyer).

I prepare small makers for this: a software bill of materials, a vulnerability check, a disclosure policy, security.txt, a 24/72-hour reporting runbook and a plain-English gap checklist. One product usually takes about a week and costs from €500. You can see a sample pack for a made-up plant sensor here: [link to your sample].

Would a 15-minute call next week be useful?

[Your name]
```

## Message 2: post in an EU startup network or maker community

```text
If you sell connected hardware or downloadable software in the EU: the Cyber Resilience Act's reporting duties started on 11 September 2026 (24-hour early warning for actively exploited vulnerabilities and severe incidents), and full obligations follow in December 2027.

I've put together a fixed-price readiness pack for small teams: SBOM, vulnerability report, disclosure policy, security.txt, reporting runbook, support-period statement and a plain-English gap checklist. Here's a sample for a fictional product: [link].

Happy to answer questions here. Not legal advice; I work alongside your lawyer.
```

## Message 3: one follow-up, a week later

```text
Hi [first name], a quick follow-up on my note about the Cyber Resilience Act. If timing is wrong, no problem. If it helps, I can run a free SBOM and vulnerability check on one public repository of yours and send you the one-page summary. [Your name]
```

Only offer the free check for public code, and only with their permission.

## Message 4: quote

```text
CRA readiness pack for [product], [Standard] package

Scope: [product name and parts, for example firmware 2.3.0, companion app 2.3.0, cloud service]
Deliverables: SBOM (CycloneDX) and component list; known-vulnerability report; vulnerability handling and disclosure policy; security.txt; reporting runbook; support-period statement; CRA gap checklist; 30-minute handover call.
What I need from you: the completed questionnaire, read-only access to the code or the dependency files, your firmware component list, and 90 minutes for the checklist workshop.
Timeline: [5 to 10] working days after I receive everything.
Price: €[amount], 50% to start, 50% on delivery.
Optional monthly care: €[amount] per month, cancel any time.

Please note: this is technical preparation, not legal advice. It does not on its own make a product compliant with the Cyber Resilience Act. Questions about scope, product category, your legal role and conformity assessment go to your lawyer. You confirm that the SBOM matches the product you ship, and you sign your own EU declaration of conformity.
```

## Message 5: monthly care, at handover

```text
Your pack is current as of [date]. New vulnerabilities are published every day and every release changes the SBOM. For €[amount] per month I will: make a new SBOM for each release, check all components every month and send you a short "what changed" note, renew security.txt before it expires, and check the runbook contacts every quarter. Cancel any time.
```

## Answers to common questions

- **"Are you a lawyer?"** No. I do the technical preparation and work alongside your lawyer. I'll give you a list of the legal questions to ask them.
- **"Will this make us CRA compliant?"** No single pack can promise that. It covers the technical documents the CRA expects and shows you the remaining gaps, with owners and dates.
- **"Do we have to publish the SBOM?"** Not necessarily. It goes into your technical documentation and you show it to authorities when they ask. Publishing it is your choice.
- **"Our firmware is C, not Python or Node."** The tools read Python and Node projects automatically. For firmware, we list the SDK, RTOS and libraries together, and I check those by hand.
- **"What do you need access to?"** Read-only access to the repositories, or just the dependency files and a list of firmware components. Never production passwords or customer data.

## Words to avoid

Never write "CRA compliant", "certified", "guaranteed compliance" or "legal advice", and never offer to sign the EU declaration of conformity. Say "CRA readiness", "preparation" and "gap checklist" instead.
