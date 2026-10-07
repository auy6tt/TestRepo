# Security support period statement

**Mossbyte Labs BV (fictional)** · Version 1.0 · 7 October 2026

> **Draft for review.** Prepared by Alex Example, Example Consulting (fictional). Management must approve the support period, and your lawyer should check it. Delete this box when it is final.

## Part 1: For customers

### Sprout S1 (SPR-S1)

- **Security updates until:** the end of **March 2031**.
- **Covers:** sprout-fw firmware 2.3.0 (ESP32-C3); Sprout Companion desktop app 2.3.0; Sprout Cloud service 2.3.0.
- **What you get:** we fix security problems in this product and make the fixes available as security updates, free of charge, until the date above.
- **How updates reach you:** over-the-air (OTA) updates for the sensor, sent from Sprout Cloud; the companion app updates through its own installer.
- **Automatic updates:** Security updates install automatically at night by default. You can postpone an update for up to 7 days, or switch automatic updates off in the companion app (Settings > Updates).
- **Check your version:** Settings > About in the companion app shows the sensor firmware version and the app version.
- **When support ends:** The sensor keeps working on your local network but gets no more security updates. We will tell you 12 months before support ends and explain how to keep using the sensor safely or recycle it.
- **Older updates:** each security update stays available for download for at least 10 years after its release, or until the end of the support period if that is later.

**Found a security problem?** Email [security@mossbyte.example](mailto:security@mossbyte.example). Our vulnerability disclosure policy is at <https://mossbyte.example/security/policy>.

**Short text for product pages and packaging:**

> Sprout S1: security updates until March 2031. Details: https://mossbyte.example/support/security-updates

## Part 2: How we decided (internal, for the technical documentation)

### Sprout S1

| Item | Answer |
|---|---|
| On the market since | March 2025 |
| Expected time in use | 5 to 7 years. The battery can be replaced; the soil probe wears out after about 6 years. |
| Support period ends | end of March 2031 |
| Decided by | Pieter Claes, CEO |
| Date of decision | 7 October 2026 |

**Reasons for this support period:**

- Customers keep plant sensors for 5 to 7 years; the probe wears out after about 6 years.
- Six years from launch (March 2025 to March 2031) covers the expected use time and is longer than the five-year minimum.
- The ESP32-C3 chip family and our cloud hosting contract are both expected to stay available for longer than that.

**Components we depend on, and how long they are supported:**

| Component | Supported until | Our plan |
|---|---|---|
| ESP-IDF 5.1 (firmware SDK) | check Espressif's support policy | Plan the move to a newer ESP-IDF release line in 2027. |
| Python 3.11 (Sprout Cloud) | 2027-10 | Move Sprout Cloud to a newer Python version before October 2027. |
| Node.js 22 (Sprout Companion) | 2027-04 | Move to the next long-term support version of Node.js in early 2027. |

**Rules we checked against (plain-English summary of the CRA, verify current text and dates):**

- The support period should reflect how long people are expected to use the product, taking into account reasonable user expectations, the nature and purpose of the product, and relevant EU law on product lifetimes.
- It must be at least five years, unless the product is expected to be in use for less than that; then it can match the expected time in use.
- The end date, at least the month and year, must be clear at the time of purchase, for example on the product page, the packaging or by digital means.
- Each security update must stay available for at least 10 years after release, or for the rest of the support period if that is longer.
- The information used to decide the support period belongs in the technical documentation.
