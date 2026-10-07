# Vulnerability and incident reporting runbook

**Mossbyte Labs BV (fictional)** · Version 1.0 · Last practice run: not yet · Next practice run: 18 November 2026

> **Keep a printed copy where the team can find it.** This runbook explains what to do, and by when, if a vulnerability in one of our products is being actively exploited, or if a severe incident affects the security of one of our products. It summarises the EU Cyber Resilience Act (CRA) reporting duties, which apply from 11 September 2026. It is not legal advice: verify current dates and requirements with our lawyer.

## The short version

The clock starts when we **become aware** of the problem. Write that moment down.

| When | What | Who |
|---|---|---|
| Straight away | Open the incident log, call the incident lead, call the lawyer if it might be reportable | Whoever spots it |
| Within 24 hours | **Early warning** on ENISA's single reporting platform | Incident lead |
| Within 72 hours | **Notification** with the details we have so far | Incident lead with the technical lead |
| As soon as possible | **Tell affected users** what is happening and what they can do | Communications lead |
| When the authorities ask | Intermediate update | Incident lead |
| Vulnerability: within 14 days after a fix or workaround is available | **Final report** | Incident lead |
| Severe incident: within one month after the notification | **Final report** | Incident lead |

Reports go through ENISA's single reporting platform. The platform passes them to the national CSIRT that acts as our coordinator and to ENISA at the same time.

## Roles and contacts

| Role | Name | Phone | Email | Backup |
|---|---|---|---|---|
| Incident lead | Mara Janssens, CTO | +32 000 00 00 01 (fictional) | mara@mossbyte.example | Lina Haddad |
| Deputy incident lead | Lina Haddad, firmware lead | +32 000 00 00 02 (fictional) | lina@mossbyte.example | Mara Janssens |
| Technical lead (cloud and app) | Tom Willems, backend developer | +32 000 00 00 03 (fictional) | tom@mossbyte.example | Lina Haddad |
| Communications lead | Sofie Peeters, customer care | +32 000 00 00 04 (fictional) | sofie@mossbyte.example | Pieter Claes |
| Management sign-off | Pieter Claes, CEO | +32 000 00 00 05 (fictional) | pieter@mossbyte.example | Mara Janssens |
| Lawyer | Example Law Firm (fictional) | +32 000 00 00 99 (fictional) | office@lawfirm.example | Firm's on-call number |

**Outside contacts**

| Who | How to reach them |
|---|---|
| Reporting platform | ENISA's single reporting platform (current address to be confirmed before the first practice run) |
| Our CSIRT coordinator | The CSIRT that Belgium has designated as coordinator (name to be confirmed with the lawyer) |
| Cloud hosting provider (fictional EU host) | Support portal, priority ticket; account number in the password manager |
| Espressif (chip and SDK vendor) | Espressif's security advisories page and product security contact |
| Crowd Supply (sales channel) | Creator support contact, for messages to backers |

## Before you need it

Do these now, not during an incident.

- [ ] Find the current address of ENISA's single reporting platform and get access for the incident lead and the deputy. Access: Mara Janssens and Lina Haddad (access requested).
- [ ] Confirm with the lawyer which CSIRT acts as our coordinator. It depends on where our main establishment in the EU is (Belgium). Companies outside the EU follow different rules, so ask.
- [ ] Write down where our products are sold, because reports must say which EU countries are affected: All EU countries (sold online across the EU).
- [ ] Keep an up-to-date SBOM for every product version still in use, so we can tell quickly whether a new vulnerability affects us.
- [ ] Save this runbook and the contact table where everyone can find them, including offline.
- [ ] Prepare the user notice template (below) and agree who approves it.
- [ ] Run a one-hour practice run (tabletop exercise) at least once a year, and after every change of people in the roles table.

## Step 1: Something has happened (first hour)

You might learn about a problem from a security researcher, a customer, a supplier's advisory, our own monitoring, a news article or the authorities.

1. Open the incident log (template at the end) and write down the date and time, the source and what is known.
2. Call the incident lead. If you cannot reach them within 30 minutes, call the deputy.
3. Do not delete logs or data. Keep evidence: emails, screenshots, server logs, affected devices.
4. Do not discuss the problem in public or on social media until the communications lead has agreed the wording.

## Step 2: Decide whether it must be reported (within a few hours)

Answer these questions with the technical lead. Write the answers and the time in the log.

1. **Is it about one of our products?** This includes our firmware, apps, cloud services the product needs, and third-party components inside them.
2. **Is it an actively exploited vulnerability?** That means there is reliable evidence that someone has exploited the vulnerability in a real system without the owner's permission. Examples: the supplier's advisory says it is being exploited, the vulnerability is on CISA's Known Exploited Vulnerabilities list *and* can be exploited in our product, or we see attacks in our logs.
3. **Is it a severe incident affecting the security of our product?** That means something that harms, or could harm, the product's ability to protect the availability, authenticity, integrity or confidentiality of important data or functions, or that has led, or could lead, to malicious code running on our product or in our users' systems. Example: someone has broken into the update server.
4. **Not sure?** Treat it as reportable and call the lawyer. A careful early warning is better than a missed deadline.

If the answer to question 2 or 3 is yes, continue with step 3. If not, handle it as a normal vulnerability under our vulnerability handling policy, and consider a voluntary report.

## Step 3: Early warning (within 24 hours)

Submit it on ENISA's single reporting platform. Keep it short: it is fine to send it before we know everything.

**For an actively exploited vulnerability, include:**

- that we have become aware of an actively exploited vulnerability in our product, and which product;
- where known, the EU countries in which the product has been made available.

**For a severe incident, include:**

- that a severe incident affects the security of our product, and which product;
- whether we suspect it was caused by unlawful or malicious acts;
- where known, the EU countries in which the product has been made available.

## Step 4: Notification (within 72 hours)

Unless we have already sent this information, submit a notification with:

- general information about the product concerned;
- for a vulnerability: the general nature of the exploit and of the vulnerability;
- for an incident: the nature of the incident and our first assessment of it;
- what we have already done to correct or reduce the problem;
- what users can do to protect themselves;
- how sensitive we consider the information to be (for example, if details would help attackers).

## Step 5: Tell the users

After an actively exploited vulnerability or a severe incident, we must inform the affected users, and all users where appropriate, about the problem and what they can do about it. Use a structured, machine-readable format (for example a CSAF security advisory) as well as a plain-language notice by email, in the app and on the website.

The communications lead drafts the notice, the incident lead checks the facts, and management approves it. Use the template below.

## Step 6: Fix, and keep the authorities informed

- Develop, test and release the fix or workaround as fast as the risk requires. Security updates are free of charge.
- If the CSIRT asks for an intermediate report, send one with what has changed.
- If the vulnerability is in a third-party component, also report it to whoever maintains that component and share our fix if appropriate.

## Step 7: Final report

**Actively exploited vulnerability: no later than 14 days after a fix or workaround is available.** Include:

- a description of the vulnerability, including how severe it is and its impact;
- where available, information about who exploited or is exploiting it;
- details of the security update or other measures we made available to fix it.

**Severe incident: within one month after the notification in step 4.** Include:

- a detailed description of the incident, including how severe it was and its impact;
- the type of threat or the root cause that probably triggered it;
- the measures we have applied and those still in progress.

## Step 8: Close and learn

- Hold a short review within two weeks: what happened, what worked, what to change.
- Update the risk assessment, the SBOM, this runbook and the user documentation.
- Publish the security advisory if it is not out yet.
- Consider voluntary reports to the CSIRT or ENISA about near misses or threats that did not need a mandatory report.

## Templates

### Early warning (copy and adapt)

```text
Subject: Early warning - actively exploited vulnerability / severe incident - Mossbyte Labs BV (fictional)

Manufacturer: Mossbyte Labs BV (fictional), Example Street 1, 9000 Ghent, Belgium (fictional address)
Contact: [incident lead name, phone, email]
Product: [product name, model, affected versions]
What we know: [one or two sentences]
Suspected malicious act (incidents only): [yes / no / unknown]
EU countries where the product is available: All EU countries (sold online across the EU)
Time we became aware: [date, time, time zone]
```

### User notice (copy and adapt)

```text
Subject: Security update for [product] - please [update / take action]

We have found [a security problem / an incident] affecting [product, versions].
What it means for you: [plain-language impact].
What we have done: [fix, workaround, investigation].
What you should do: [update to version X / change setting Y / nothing for now].
How to check your version: [where to look].
More information: [link to the advisory]. Questions: security@mossbyte.example
```

### Reply to a researcher (copy and adapt)

```text
Thank you for your report about [product]. Our reference is [number].
We will send our first assessment within 10 working days
and keep you updated at least every 14 days.
Please keep the details private while we work on a fix.
```

## Incident log

| Date and time | What happened or was decided | Who | Evidence or link |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

Mossbyte Labs BV (fictional) · Runbook version 1.0 · Verify current dates and requirements before each use.
