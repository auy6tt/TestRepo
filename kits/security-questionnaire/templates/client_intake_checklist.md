# Client intake checklist: security questionnaire

*Use it on the first call, before any work starts. Copy it into the client's folder and tick items off.*

## 1. The job

- [ ] Client company name, product and website
- [ ] Your contact, and the **technical owner** who will review and sign off every answer (name, title, email)
- [ ] The buyer who sent the questionnaire, and why (new deal, renewal, yearly review)
- [ ] The questionnaire exactly as received (.xlsx, .csv, .docx, PDF or a portal link). If it's a portal, ask for an export or copy the questions into a spreadsheet.
- [ ] The buyer's deadline, and the date you need the client's answers by to meet it
- [ ] Number of questions and sheets (for the quote)
- [ ] Any answers the client already wrote (keep them)
- [ ] How the answers go back: email the file, upload to a portal, or paste into a web form

## 2. Confidentiality (before you receive any document)

- [ ] NDA signed (theirs or yours). Check it allows the tools you use: say plainly that you use AI-assisted tools (Claude) on your own account with model training turned off, and that you review everything yourself.
- [ ] Where files live: one folder per client, never in a public repository or shared drive outside the NDA. In this repo, use `kits/security-questionnaire/clients/<client>/` (git ignores it).
- [ ] How files are shared (their drive or an encrypted link if they prefer it to email)
- [ ] When you delete their files: [30] days after delivery, unless they're on a retainer
- [ ] May answers name their internal policies, e.g. "Access Control Policy, section 4.2"? **Yes / No**
- [ ] Anything that must never appear in an answer (internal hostnames, IP addresses, staff names, contract terms)

## 3. Documents to collect

Ask for whatever already exists. Writing new policies is a separate job.

- [ ] Information security policy, or the set of security policies
- [ ] Access control (accounts, passwords, MFA, reviews, leavers)
- [ ] Incident response plan
- [ ] Backup, business continuity and disaster recovery plans
- [ ] Encryption or key management standard
- [ ] Secure development and change management policy
- [ ] Vendor management policy and the list of subprocessors
- [ ] HR security: onboarding and offboarding, background checks, training
- [ ] Data retention and deletion; privacy policy; their customer DPA template
- [ ] Architecture or data-flow overview; hosting provider and regions
- [ ] Reports or certificates that **actually exist**, with dates: SOC 2 report, ISO 27001 certificate, penetration test summary
- [ ] Insurance certificate (only if they're happy to share it)
- [ ] Past questionnaires they've answered, and the text of their security or trust page

## 4. Quick questions for the technical owner (the usual gaps)

Written answers by email are fine. Save the email: it becomes the source for those answers ("Written answers from <name>, <date>").

- Do you have a SOC 2 report or an ISO 27001 certificate? If not, say so plainly.
- Is MFA enforced on every system, or only some?
- Background checks: who gets checked, and what is checked?
- Security awareness training: who takes it, and how often?
- How long are logs kept? Who looks at security alerts, and is that 24/7?
- Laptops: disk encryption, device management (MDM), anti-malware or EDR? Are personal devices allowed?
- Is there a web application firewall or DDoS protection?
- What happens to customer data when a contract ends, including backups?
- Does the product offer SSO (SAML) or audit logs to customers?
- Is there an uptime commitment (SLA) and a status page?
- Is customer data used for AI features or model training?
- Any security incidents or breaches in the last three years?

## 5. Scope, price and timeline (confirm in writing)

- [ ] Price and what it covers (see `fixed_price_offer.md`)
- [ ] Turnaround: [3] business days after you have the documents
- [ ] Review rounds included: [2]
- [ ] Deposit: [50]% before you start
- [ ] Sign-off: the technical owner approves every answer before it goes to the buyer
