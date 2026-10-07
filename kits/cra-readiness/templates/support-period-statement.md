<!--
TEMPLATE. Fill it with: python scripts/fill_templates.py --client client.json --out <folder>
Part 1 is for customers (product page, manual, packaging insert). Part 2 is internal and goes into
the technical documentation. The support period is the manufacturer's decision; the client's
management approves it and the lawyer checks it.
-->
# Security support period statement

**{{ company.legal_name }}** · Version {{ support.version }} · {{ today | longdate }}

> **Draft for review.** Prepared by {{ engagement.consultant_name }}. Management must approve the support period, and your lawyer should check it. Delete this box when it is final.

## Part 1: For customers

{% for p in products %}
### {{ p.name }} ({{ p.model }})

- **Security updates until:** the end of **{{ p.support_end | monthyear }}**.
- **Covers:** {{ p.parts | join("; ") }}.
- **What you get:** we fix security problems in this product and make the fixes available as security updates, free of charge, until the date above.
- **How updates reach you:** {{ p.update_method }}.
- **Automatic updates:** {{ p.automatic_updates }}
- **Check your version:** {{ p.how_to_check_version }}
- **When support ends:** {{ p.after_support }}
- **Older updates:** each security update stays available for download for at least 10 years after its release, or until the end of the support period if that is later.

{% endfor %}
**Found a security problem?** Email [{{ contacts.security_email }}](mailto:{{ contacts.security_email }}). Our vulnerability disclosure policy is at <{{ contacts.policy_url }}>.

**Short text for product pages and packaging:**

{% for p in products %}
> {{ p.name }}: security updates until {{ p.support_end | monthyear }}. Details: {{ contacts.support_page_url }}

{% endfor %}
## Part 2: How we decided (internal, for the technical documentation)

{% for p in products %}
### {{ p.name }}

| Item | Answer |
|---|---|
| On the market since | {{ p.placed_on_market | monthyear }} |
| Expected time in use | {{ p.expected_use }} |
| Support period ends | end of {{ p.support_end | monthyear }} |
| Decided by | {{ p.support_decided_by }} |
| Date of decision | {{ p.support_decision_date | longdate }} |

**Reasons for this support period:**

{% for reason in p.support_reasons %}
- {{ reason }}
{% endfor %}

**Components we depend on, and how long they are supported:**

| Component | Supported until | Our plan |
|---|---|---|
{% for c in p.component_support %}
| {{ c.component }} | {{ c.supported_until }} | {{ c.note }} |
{% endfor %}

{% endfor %}
**Rules we checked against (plain-English summary of the CRA, verify current text and dates):**

- The support period should reflect how long people are expected to use the product, taking into account reasonable user expectations, the nature and purpose of the product, and relevant EU law on product lifetimes.
- It must be at least five years, unless the product is expected to be in use for less than that; then it can match the expected time in use.
- The end date, at least the month and year, must be clear at the time of purchase, for example on the product page, the packaging or by digital means.
- Each security update must stay available for at least 10 years after release, or for the rest of the support period if that is longer.
- The information used to decide the support period belongs in the technical documentation.
