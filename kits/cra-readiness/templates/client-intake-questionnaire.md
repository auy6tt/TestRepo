<!--
Send this to the client after the first call (Word version: client-intake-questionnaire.docx).
Their answers go into client.json. Questions about scope, product category and legal role are
asked here only so you can pass them to the client's lawyer: do not answer them yourself.
-->
# CRA readiness: client questionnaire

Thank you for choosing us to prepare your Cyber Resilience Act (CRA) readiness pack. Please answer what you can. "Don't know" is a useful answer too. Everything you send is kept confidential and used only for this work.

## A. Your company

| Question | Your answer |
|---|---|
| Company legal name and trading name |  |
| Postal address of your main establishment (country matters for reporting) |  |
| Number of staff and approximate yearly turnover (micro, small or bigger) |  |
| Website and domain where security pages will live |  |
| Main contact for this project (name, role, email, phone) |  |
| Do you have a lawyer who advises on product compliance? Who? |  |

## B. Your products

Fill in one block per product. Copy the table if you have more products.

| Question | Your answer |
|---|---|
| Product name and model number |  |
| What does it do, in one or two sentences? |  |
| Which parts does it have? (device, firmware, mobile app, desktop app, cloud service, web dashboard) |  |
| How does it connect? (Wi-Fi, Bluetooth, Zigbee or Thread, LoRa, mobile data, Ethernet, USB) |  |
| Does it have security functions, such as locks, cameras, alarms, password storage or network equipment? |  |
| Where do you sell it? (EU countries; own shop, Crowd Supply, Tindie, Kickstarter, Amazon, distributors) |  |
| When did you first sell it in the EU, and roughly how many units are in use? |  |
| Current versions of each part (firmware, app, cloud) |  |
| How often do you release new versions? |  |
| Who imports it into the EU, if you are based outside the EU? |  |

## C. Software and components

| Question | Your answer |
|---|---|
| Where is the code? (GitHub, GitLab, other) Can you give us read-only access, or send the files listed below? |  |
| Languages and frameworks per part (for example C with ESP-IDF, Python with Flask, Node.js) |  |
| Dependency files per part: requirements.txt, poetry.lock, package.json with package-lock.json, yarn.lock, others |  |
| Firmware: chip, SDK and version, real-time operating system and version, libraries copied into the code |  |
| Third-party binaries or drivers shipped with the product |  |
| Do you already have an SBOM? In which format? |  |
| Who builds releases, and how (on a laptop, in CI)? |  |

## D. Updates and support

| Question | Your answer |
|---|---|
| Can every part be updated? How (over the air, app store, installer, manual download)? |  |
| Are updates signed? Are they installed automatically? Can users postpone them? |  |
| How long do customers typically use the product? |  |
| How long do you plan to provide security updates? Is the end date shown anywhere today? |  |
| Do you keep old update files available for download? |  |

## E. Security today

| Question | Your answer |
|---|---|
| Is there a security contact (email, web form, security.txt)? Who reads it? |  |
| Do you have a vulnerability disclosure policy? |  |
| Have you ever received a vulnerability report, or had a security incident? What happened? |  |
| Do devices ship with a default password? How does first set-up work? |  |
| What data does the product collect? Any personal data? Where is it stored? |  |
| Any security testing so far (code review, penetration test, dependency checks)? |  |
| Debug ports (JTAG, serial) and test features: are they disabled in production units? |  |

## F. People for incidents

Since 11 September 2026, manufacturers must report actively exploited vulnerabilities and severe incidents within 24 hours (early warning) and 72 hours (notification), with a final report later (verify current dates). We need to know who would act.

| Role | Name, job title, phone, email | Backup person |
|---|---|---|
| Incident lead |  |  |
| Technical lead |  |  |
| Communications (customers, website) |  |  |
| Management sign-off |  |  |
| Lawyer |  |  |

## G. Other compliance

| Question | Your answer |
|---|---|
| Does the product carry the CE marking today? Under which rules (radio equipment, EMC, low voltage)? |  |
| Have you worked with a test lab? Which one? |  |
| Any other security standards or certifications (for example ETSI EN 303 645, EN 18031)? |  |

## H. Practical details

| Question | Your answer |
|---|---|
| How will you share files (read-only repository access, zip by email, shared folder)? |  |
| Do you need us to sign a confidentiality agreement first? |  |
| Deadline or launch dates we should know about |  |

**Please note:** we provide technical preparation, not legal advice. Whether the CRA applies, your product's category and your legal role are questions for your lawyer; we will list them for you. We never sign the EU declaration of conformity on your behalf.
