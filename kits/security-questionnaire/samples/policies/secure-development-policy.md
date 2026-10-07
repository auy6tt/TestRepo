# Secure Development Policy

> FICTIONAL SAMPLE. Quarterhour, Inc. is a made-up company used to demonstrate this kit.

- Document ID: QH-POL-11
- Version: 1.2
- Owner: Dana Whitfield, CTO
- Approved by: Maya Okafor, CEO
- Last reviewed: 8 August 2026
- Review cycle: at least annually

## 1. Purpose

To make sure security is part of how Quarterhour designs, builds, tests and releases software.

## 2. Source code

All code is stored in private GitHub repositories. Engineers use individual accounts with MFA. The main branch is protected, so nobody can push to it directly.

## 3. Code review

Every change is made through a pull request and needs at least one approving review from an engineer other than the author before it can be merged.

## 4. Automated checks

Every pull request runs automated tests, static code analysis for common security flaws, and dependency scanning for known vulnerable packages. Secret scanning is turned on for all repositories. A pull request cannot be merged while a required check is failing.

## 5. Environments

Development, staging and production are separate. Staging and production run in separate AWS accounts. Production customer data is never copied to development or staging; those environments use synthetic test data.

## 6. Deployment and change management

Only code merged to the main branch can be deployed to production, and only through the automated CI/CD pipeline. Each deployment is logged with the changes it contains. A failed deployment is rolled back to the previous version. Infrastructure is defined as code and changes to it are reviewed the same way as application code.

## 7. Vulnerability remediation

Vulnerabilities found by scanning, testing or outside reports are fixed within these times after they are confirmed:

- Critical: 7 days
- High: 30 days
- Medium: 90 days
- Low: at the next planned update

## 8. Penetration testing

An independent third party performs a penetration test of the Quarterhour application and its public infrastructure at least once a year. Findings are fixed within the times in section 7.

## 9. Training

Engineers complete secure coding training based on the OWASP Top 10 when they join and every year after that.

## 10. Third-party components

New open-source dependencies are added through pull requests. Automated update requests keep dependencies current. Dependencies with known critical vulnerabilities are not allowed in production.
