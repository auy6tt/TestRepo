# Incident Response Plan

> FICTIONAL SAMPLE. Quarterhour, Inc. is a made-up company used to demonstrate this kit.

- Document ID: QH-POL-05
- Version: 1.1
- Owner: Dana Whitfield, CTO
- Approved by: Maya Okafor, CEO
- Last reviewed: 14 April 2026
- Review cycle: at least annually

## 1. Purpose

This plan describes how Quarterhour detects, responds to and learns from security incidents.

## 2. What counts as a security incident

Any event that threatens the confidentiality, integrity or availability of customer data or Quarterhour systems. Examples: unauthorised access, exposure of customer data, malware on a company device, or a compromised account.

## 3. Severity levels

- SEV1: confirmed or likely exposure of customer data, or the service is down for all customers.
- SEV2: a limited security issue or a partial outage.
- SEV3: a suspicious event with no confirmed impact.

## 4. Roles

- Incident Lead: the CTO (backup: the on-call senior engineer). Runs the response and makes technical decisions.
- Communications Lead: the CEO. Approves all messages to customers, regulators and partners.
- Responders: engineers assigned by the Incident Lead.

## 5. Detection and reporting

Security alerts from AWS GuardDuty, AWS CloudTrail, application error monitoring and uptime checks go to the on-call engineer. Employees must report a suspected incident straight away in the #security Slack channel or by email to security@quarterhour.example. Customers and security researchers can report vulnerabilities to the same address.

## 6. Response steps

1. Triage: confirm the incident and set its severity.
2. Contain: limit the damage, for example by revoking credentials or isolating a resource.
3. Eradicate and recover: remove the cause and restore normal service from known-good sources.
4. Preserve evidence: keep relevant logs and snapshots until the post-incident review is complete.
5. Close: confirm the issue is resolved and record the timeline.

## 7. Customer notification

If a security incident affects customer data, Quarterhour notifies the affected customers without undue delay and no later than 72 hours after confirming the incident. The notice explains what happened, which data was involved, what we are doing about it and who to contact.

## 8. Post-incident review

Every SEV1 and SEV2 incident gets a written post-incident review within 10 business days, covering the root cause and follow-up actions. All incidents, whatever their severity, are recorded in the incident register.

## 9. Testing

This plan is tested with a tabletop exercise at least once a year. The results and any improvements are recorded.
