# Written answers from the CTO, 30 September 2026

> FICTIONAL SAMPLE. Quarterhour, Inc. is a made-up company used to demonstrate this kit.

The policies did not cover these questions, so the freelancer sent them to Quarterhour's technical owner. These are the replies, copied from the email of 30 September 2026 from Dana Whitfield, CTO. Library answers that rely on them cite this record as "Written answers from Dana Whitfield, CTO, 30 Sep 2026" and the question number.

Questions she has not answered yet stay NEEDS CLIENT INPUT in the library.

## Q1. Does Quarterhour have a SOC 2 report?

No. We have not had a SOC 2 audit and do not have a SOC 2 report.

## Q2. Is Quarterhour certified to ISO/IEC 27001?

No. We are not ISO 27001 certified.

## Q3. Are background checks done before people start?

Yes. Every employee goes through a background check before their start date: identity, employment history and, where the law allows it, criminal records. Contractors who get access to production systems are checked the same way.

## Q4. Do employees and contractors sign confidentiality agreements?

Yes. Confidentiality obligations are part of every employment contract and contractor agreement, and they are signed before any access is given.

## Q5. Does everyone get security awareness training?

Yes. All staff complete security and privacy awareness training when they join and once a year after that. Engineers also do the OWASP-based secure coding training in our development policy.

## Q6. How is one customer's data kept apart from another's?

Quarterhour is multi-tenant. Every record carries the customer's account ID, and the application's data-access layer limits every query to the signed-in customer's account. Customers do not share accounts or data.

## Q7. How long do you keep customer data, and what happens when a contract ends?

We keep customer data while the contract is active. When a contract ends, the customer can export their data for 30 days, and then we delete it from production systems. Deleted data remains in encrypted backups until those backups expire: 35 days for daily backups and up to 12 months for monthly snapshots.

## Q8. Do you offer a data processing agreement to customers?

Yes. We offer our standard Data Processing Agreement to any customer on request.

## Q9. Is customer data used to train AI models?

No. We do not use customer data to train AI or machine learning models, and we do not send customer data to third-party AI services.
