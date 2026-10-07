# Weekly digest starter kit

Run a paid weekly brief for one industry in one region, and start this week.

Every week a watcher checks a list of **official sources** for changes. Claude Code drafts short items from what changed, each with a link to its source. **You check every item against its source.** The kit then builds the issue as an email, a PDF, a spreadsheet tracker and a calendar file, and **you send it**. A Claude Code Routine can run the watch-and-draft step every week on a schedule; the reviewing and sending are always yours.

**Start here**

1. Install the kit and run the self-test ([Set up](#set-up)). It takes two minutes and works offline.
2. Open the sample issue in [`samples/battery-storage-ohio-week41/output/`](samples/battery-storage-ohio-week41/output/). The `.pdf` is your portfolio piece: put your own name on it ([how](#the-sample-issue)) and send it to prospects.
3. Pick an offer below, copy its sources template and follow [Start a digest](#start-a-digest).

## What is in the kit

```text
kits/weekly-digest/
  README.md                    this guide
  requirements.txt             Python packages
  scripts/
    watch_sources.py           checks the sources and writes changes.json and changes.md
    build_digest.py            builds the email (.html and .txt), .pdf, .xlsx and .ics
    run_demo.py                rebuilds the sample issue offline from simulated sites
  templates/
    sources/                   sources.yaml examples for the five offers
    items.schema.json          the rules every items file must follow
    items.example.yaml         a commented items file
    digest-email.html.j2       the email and PDF layout
    welcome-email.md           welcome email for new subscribers
    founding-subscriber-offer.md   offer text for your first subscribers
    routine-setup.md           schedule the weekly run, plus the review checklist
  samples/battery-storage-ohio-week41/
    sources.yaml, site/        the fictional sources and two weeks of their pages
    data/                      what the watcher saved between the two runs
    changes.json, changes.md   what the watcher found in week 41
    items.reviewed.yaml        the drafted and checked items
    output/                    the finished issue: .html, .txt, .pdf, .xlsx, .ics
  tests/selftest.py            offline checks of the whole kit
```

The Claude Code skill is in [`.claude/skills/weekly-digest/`](../../.claude/skills/weekly-digest/SKILL.md) at the repository root. Your own digests go in `kits/weekly-digest/digests/<name>/` (you create this folder).

## The offers

| Offer | Who buys | Where to find them | Price a month (estimate) | Template |
|---|---|---|---|---|
| **Packaging-law (EPR) update brief**: changes in US state packaging fee laws, deadlines and rules | Food, drink, cosmetics, pet and home-goods brands with $1M–50M revenue; packaging distributors that resell it | Operations and packaging people on LinkedIn, Shopify and direct-to-consumer founder groups, packaging distributors | $39–99 per brand; $300–800 white-label | [`epr-packaging-us.yaml`](templates/sources/epr-packaging-us.yaml) |
| **Public-bid digest for one trade**: every open public bid in one trade, plus past winning prices from bid tabulations | Small contractors in one trade (roofing, cleaning, mowing, paving, pest control) | Firms named on past bid results, state trade associations, builders' exchanges, trade groups such as ISSA for cleaning | $49–149 per contractor | [`public-bids-one-trade.yaml`](templates/sources/public-bids-one-trade.yaml) |
| **Local-government meeting watch**: agendas, rezonings, moratoria, votes and hearing dates for one industry | Small developers and land brokers (battery storage, solar, self-storage, car washes, data centers), commercial brokers, contractors | Development, land and site-selection roles on LinkedIn, state solar and storage associations, CCIM and NAIOP chapters | $150–500 per client | [`local-gov-meetings.yaml`](templates/sources/local-gov-meetings.yaml) |
| **International aid tenders for one specialty**: development bank, UN and EU tenders, filtered and summarised | Small consultancies and freelancers in one specialty (evaluation, GIS, training, translation), often in one language | Evaluation and specialty groups on LinkedIn, national and regional evaluation societies, professional mailing lists | $15–40 for individuals; $100–300 for firms | [`aid-tenders.yaml`](templates/sources/aid-tenders.yaml) |
| **New commercial premises list**: new commercial buildings and fit-outs from city open-data permits | Commercial cleaners, sign makers, alarm, IT cabling and fire-protection firms, commercial insurance brokers | Networking groups such as BNI, chambers of commerce, trade associations, LinkedIn | $79–199 per metro | [`new-commercial-premises.yaml`](templates/sources/new-commercial-premises.yaml) |

Prices are estimates from the October 2026 research in [`PLAYBOOK.md`](../../PLAYBOOK.md), where each niche has its own entry with demand evidence and a one-day test. Most offers land between $39 and $500 a month depending on the audience; individuals buying aid-tender lists pay less.

**Why people pay:** it saves hours of reading agendas and portals, they stop missing deadlines, every item is checked by a person, and the dates go straight into their calendar.

## Pricing

- **Founding subscribers (your first 5–10):** about half the regular price, locked for 12 months, with the first two issues free. Use [`templates/founding-subscriber-offer.md`](templates/founding-subscriber-offer.md). Good starting points: $39 (EPR), $49 (bids), a $150 pilot (meeting watch), $15 or €10 (aid tenders for individuals), $79 (premises).
- **Regular price** after the first 4–8 weeks: raise it for new subscribers only.
- **Tiers:** one person; a team (up to 5 people, about 2× the price); white-label for distributors, agencies or associations that send it to their own clients.
- **Add-ons:** extra counties, states or agencies for a monthly fee; an annual plan at 10× the monthly price.
- Do not race generic alert tools on price. You sell curation, human checking and dates in the calendar.
- Take payment with a payment link or subscription tool. Keep your subscriber list in your email or payment tool, never in this repository.

## The weekly process

| When | Who | What | Your time |
|---|---|---|---|
| Monday 6:07 AM | Routine (or you) | Check the sources, draft items with `status: needs_review`, build a preview, push to GitHub | none |
| Monday morning | You | Check every item against its source with the checklist below. Approve, fix or reject | 30–90 min |
| Monday late morning | Claude Code and you | Build the final issue, then open it, click every link and test the calendar file | 10 min |
| Monday noon | You | Send it | 10 min |
| During the week | You | Check by hand any source that had an error, answer subscribers, find new ones | as needed |

To schedule the first step, follow [`templates/routine-setup.md`](templates/routine-setup.md).

## Review checklist

Before you approve an item:

- [ ] The link opens the official document itself, not a news story, a copy or a search page.
- [ ] Every fact in the title and summary is in that document: bodies, companies, case numbers, sizes and amounts.
- [ ] Every date and time matches the source, in the right time zone, and the deadline is the next thing that happens.
- [ ] Nothing newer changes it: a later notice, a cancellation or an updated agenda.
- [ ] Status words are exact: proposed or adopted, first reading or passed, filed or approved, recommended or awarded.
- [ ] The page, item or section reference is right.
- [ ] No personal data about private individuals.
- [ ] No advice: it says what the document says, not what the reader should do.
- [ ] Your own words, with short quotes only.

Then set `status: approved` with `checked_by` (your initials) and `checked_on` (today), or `status: rejected`. Before sending, skim `changes.md` for anything missed and check the sources that had errors. The full checklist is in [`templates/routine-setup.md`](templates/routine-setup.md#review-checklist).

## Rules

These are not optional. Breaking them can get you blocked, sued or distrusted, and trust is the product.

1. **Official sources and open-data APIs only.** Government sites, official program operators, official procurement portals and open-data portals. Do not scrape news sites, paid databases or other people's alert services.
2. **Respect robots.txt and site terms.** The watcher reads robots.txt before every site and skips anything it disallows. Never fetch a skipped or blocked page another way, never log in with the watcher, and never get around a block. Read each site's terms of use before you add it and write the date in `terms_checked`. Some open-data licences require a credit line: put it in `issue.attribution`. Keep the pause between requests at 5 seconds or more, and put your real contact email in the user agent.
3. **Link to documents; do not repost them.** Summarise in your own words and link to the official document. Do not attach agencies' PDFs to your emails or host copies.
4. **No personal data about private individuals.** No names, home addresses, phone numbers or personal emails of residents, homeowners, public commenters or sole traders, even when a public record shows them. Companies, public bodies and officials acting in their official role are fine. In `sources.yaml`, use `fields` to keep only the fields you need and `skip_records_where` to drop private individuals' records before anything is saved.
5. **Never present it as legal advice.** Describe what the documents say. Never tell a reader what they must do or whether a rule applies to them. Every issue carries a "not legal advice" note, and `build_digest.py` warns about advice-like wording.
6. **Email rules.** Only email people who asked to receive the brief, or follow the rules for business outreach where you are. Commercial email in the US must include your postal address and a working way to unsubscribe, and you must honour unsubscribes promptly. Use an honest subject line and sender name.
7. **Correct mistakes in the open.** Put corrections at the top of the next issue, and email subscribers sooner if a date was wrong.

This kit is not legal, tax or business advice. Check the rules where you live before you take payments.

## Set up

In a Claude Code cloud session, run `bash kits/setup.sh weekly-digest` from the repository root. It makes the kit's Python environment in `kits/weekly-digest/.venv`. Then run the self-test from the `kits/weekly-digest` folder:

```bash
.venv/bin/python tests/selftest.py
```

On your own computer you can make the environment yourself, from the `kits/weekly-digest` folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tests/selftest.py
```

Always run the kit's scripts with `.venv/bin/python` (the weekly-digest line of `bash kits/setup.sh --list`). Plain `python` does not have the kit's packages. The self-test serves the fictional sample sites on your computer and checks the whole kit (about 70 checks, under a minute, no internet needed). On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python`.

On your own computer, the PDF step needs a browser for Playwright. Run `.venv/bin/python -m playwright install chromium` once. Claude Code cloud sessions already have one.

To rebuild the sample issue from its simulated sources:

```bash
.venv/bin/python scripts/run_demo.py
```

It serves the week 40 copy of the fictional sites, runs the watcher, swaps in the week 41 copy, runs it again and builds the issue. `scripts/run_demo.py --serve` only serves the week 41 sites so you can browse them.

## Start a digest

1. Create `digests/<name>/` and copy the closest template from `templates/sources/` to `digests/<name>/sources.yaml`. Or ask Claude Code: *"Use the weekly-digest skill to set up a new digest called roofing-dallas from the public-bids template."*
2. Replace every `example.gov` or `example.org` placeholder address with the real official page. The comments in each template say where to look. The watcher skips placeholder addresses (any `example.gov`, `example.org`, `example.com` or `example.net` address), so nothing is fetched until you do this.
3. For each source, open `https://<site>/robots.txt` and the site's terms of use, then write the date in `terms_checked`.
4. Allow every domain in the environment's network settings (next section).
5. Run the watcher. The first run only saves snapshots; changes show up from the second run, a week later. Use `--dry-run` while you tune selectors and keywords.
6. Commit and push `digests/<name>/`, including `data/`, to a private repository (see below).

**Keep your digests in a private repository.** The weekly run commits your issues and snapshots, and anyone can read a public repository, including the issues your subscribers pay for. This repository is public: make it private in its GitHub settings, or copy the kit and its skill into a new private repository, before you push a digest.

## Network access

Claude Code cloud sessions can only reach package registries and a few developer sites by default, so the real official sources are blocked until you allow them. When that happens, the watcher reports `Blocked by the network policy (<host>)` with a hint, and it never tries to get around the block.

To allow your sources:

1. At claude.ai/code, click the cloud icon showing your environment's name (above the message box), hover over the environment and click the settings icon. In some versions of the app this environment menu is in the session's title bar instead: open it and click **Edit**.
2. Set **Network access** to **Custom** (newer versions of the app may call it **Limited**). If your app shows other labels, pick the level that lets you list your own domains.
3. Under **Allowed domains**, list each domain your sources use, one per line. `*.example.gov` covers every subdomain.
4. Keep the package managers box ticked (**Also include default list of common package managers**; newer versions: **Allow package managers**), so Python packages still install.
5. Save. Existing sessions pick up the change within about a minute.

A Routine uses the environment you choose when you create it, so allow the domains in that environment. The steps are also in the Claude Code documentation: https://code.claude.com/docs/en/cloud-environments#network-access. On your own computer there is no such limit.

## Run each script

All commands run from `kits/weekly-digest` with the virtual environment's Python.

### `scripts/watch_sources.py`: check the sources

```bash
.venv/bin/python scripts/watch_sources.py digests/<name>              # the folder or its sources.yaml
.venv/bin/python scripts/watch_sources.py digests/<name> --dry-run    # report without saving snapshots
.venv/bin/python scripts/watch_sources.py digests/<name> --only "County"   # only matching sources
```

For each source it reads robots.txt, waits between requests to the same site, asks for the page only if it changed since last time, turns it into tidy text and compares it with the last snapshot.

- **Writes:** `digests/<name>/issues/<year>-W<week>/changes.json` (for Claude Code) and `changes.md` (for you), and updates `digests/<name>/data/` (snapshots, a few old versions, the text of new linked documents and a copy of every run's report).
- **Statuses:** `changed`, `unchanged`, `first_run` (snapshot saved), `no_match` (changed, but nothing matched your keywords), `skipped` (placeholder address or robots.txt says no) and `error` (with a hint).
- **Options:** `--data` and `--out` change where files go; `--delay`, `--timeout` and `--user-agent` override the settings; `--map-url FROM=TO` fetches from a local copy for testing.
- **Exit codes:** 0 when the run finished (even if some sources had errors), 1 when every source failed (usually network settings), 2 when `sources.yaml` has a problem.

**`sources.yaml` fields**

| Field | Used for | Meaning |
|---|---|---|
| `digest.name`, `scope`, `audience` | all | What the digest covers. Claude Code uses `scope` to decide what is relevant. |
| `settings.user_agent` | all | Identifies you to the sites. Include a real contact email. |
| `settings.delay_seconds` | all | Pause between requests to the same site (default 5). A robots.txt `Crawl-delay` makes it longer. |
| `settings.keywords` | all | Highlights matching changes on pages and PDFs; filters records in feeds and data. Plurals match; `exempt*` matches any ending. |
| `name`, `url`, `type` | all | A label, the address and one of `html`, `pdf`, `json` or `rss`. |
| `selector` | html | CSS selector for the part of the page to watch, such as `#agendas` or `table.bids`. Without it, the main content is used. |
| `exclude_selector` | html | Parts of the page to ignore. |
| `ignore_patterns` | html, pdf | Regular expressions for lines to ignore, such as `^Last updated`. |
| `follow_new_links` | html, pdf, rss, json | `true` fetches new linked PDFs and saves their text. Or `{pattern: "agenda.*\\.pdf", max: 3}`. |
| `items_path` | json | Where the list of records is, such as `records`, `results` or `features`. |
| `id_field` | json | The field that identifies a record, such as `case_number`. |
| `fields` | json | Keep only these fields. Anything else, such as names and phone numbers, is never saved. |
| `link_field` | json | The field holding each record's link. |
| `skip_records_where` | json | Drop records before saving, such as `{applicant_type: [individual]}`. |
| `report_removed` | json, rss | List records that disappeared (off by default, because feeds drop old items). |
| `keywords` | any | Per-source keywords; `[]` turns filtering off for that source. |
| `tags`, `notes`, `terms_checked`, `enabled` | any | Labels, a note for Claude Code, the date you read the terms, and `false` to pause a source. |

In a `url`, `{{today}}` or `{{today-30:%m/%d/%Y}}` becomes a date (for APIs that need a date window), and `${NAME}` becomes the environment variable `NAME` (for API keys). Never write a key into `sources.yaml`; keys are left out of every report and snapshot.

### `scripts/build_digest.py`: build the issue

```bash
.venv/bin/python scripts/build_digest.py digests/<name>/issues/2026-W41/items.yaml
.venv/bin/python scripts/build_digest.py <items.yaml> --preview          # include unchecked items, clearly marked
.venv/bin/python scripts/build_digest.py <items.yaml> --formats html,pdf
.venv/bin/python scripts/build_digest.py <items.yaml> --changes <changes.json> --paper A4
```

- **Reads** an items file (YAML or JSON) and checks it against `templates/items.schema.json`, with plain-English error messages. The format is explained in [`templates/items.example.yaml`](templates/items.example.yaml).
- **Review gate:** only `approved` items are published. If any item is still `draft` or `needs_review`, it stops with exit code 3. `--preview` builds a draft with a red "PREVIEW, NOT CHECKED" banner and `-PREVIEW` in the file names, for your eyes only.
- **Warnings:** email addresses or phone numbers in items, advice-like wording ("you must"), and dates that have already passed.
- **Writes** to `output/` next to the items file (or `--out`):
  - `.html`: the email, with every style inline, a single 640-pixel column that works on phones, and no images or tracking.
  - `.txt`: the plain-text version.
  - `.pdf`: the same issue as a print-ready Letter or A4 PDF, printed with headless Chromium, with page numbers.
  - `.xlsx`: a tracker with About, Items and Dates sheets, live "days left" formulas, links to sources and columns for the subscriber's own notes.
  - `.ics`: every hearing, vote and deadline as calendar events with a reminder the day before, times converted to UTC.
- **Exit codes:** 0 done, 2 the items file has problems, 3 unchecked items, 4 the PDF could not be made (the other files are still written).

### `scripts/run_demo.py` and `tests/selftest.py`

`run_demo.py` rebuilds the sample issue offline (see [Set up](#set-up)). `selftest.py` checks robots.txt rules, change detection for each source type, the 304 "not modified" path, the private-data filters, API key redaction, the review gate and every output file. Run it after you change anything.

## Using Claude Code

The skill in `.claude/skills/weekly-digest/` tells Claude Code how to run each step and how to write items. Things to ask:

- *"Use the weekly-digest skill to set up a new digest called ohio-bess from the local-gov-meetings template."*
- *"Run the weekly watch for ohio-bess and draft this week's items."*
- *"I checked W41-01 to W41-04 against their sources. Mark them approved, checked by AB today. Reject W41-05: it is a repeat."*
- *"Build the final issue for ohio-bess, then commit and push."*

Claude Code never approves an item unless you say you checked it, and never sends anything.

## Sending an issue

- **Small list:** open the `.html` file in Chrome, select all, copy, and paste into a new message in Gmail or Outlook. Most of the formatting carries over. Attach the `.pdf`, `.xlsx` and `.ics`, and put subscribers in BCC.
- **Bigger list:** use a newsletter tool that accepts your own HTML (look for a "code" or "HTML" editor). Paste the `.html` in and attach or link the files.
- **Always** send a test to yourself first and read it on your phone.

## The sample issue

[`samples/battery-storage-ohio-week41/`](samples/battery-storage-ohio-week41/) is a complete issue of "Battery Storage Zoning Watch — Ohio, Week 41". Everything in it is fictional: the counties, townships, city, planning commission, companies and documents are invented, and the links use the reserved `.example` domain, so they do not open. It shows the whole process: two weeks of simulated official pages, the watcher's change report, the drafted and checked items (including one rejected draft and the skipped changes), and the finished files. The grey "Sample issue" banner comes from `issue.sample_notice` in its items file; leave that field out of your real issues.

**Put your own name on the sample.** In the `issue:` block at the top of `samples/battery-storage-ohio-week41/items.reviewed.yaml`, change `brand` (your business or newsletter name), `contact_email` and `website`. Keep the sample postal address in `mailing_address` (this repository is public), and keep `sample_notice`, so the sample always says it is fictional. Then rebuild the files from the `kits/weekly-digest` folder:

```bash
.venv/bin/python scripts/build_digest.py samples/battery-storage-ohio-week41/items.reviewed.yaml \
  --out samples/battery-storage-ohio-week41/output --changes samples/battery-storage-ohio-week41/changes.json
```

The new `.pdf` in `output/` is your portfolio piece.

## Troubleshooting

| You see | What to do |
|---|---|
| `Blocked by the network policy (host)` | Allow the host under Allowed domains (see [Network access](#network-access)). |
| `robots.txt does not allow automated access` | Do not fetch it another way. Look for an RSS feed, API or open-data version, or check that page by hand. |
| `The site refused access (HTTP 403)` | Do not work around it. Use another official route or check by hand. |
| `Page not found (HTTP 404)` | The page moved. Find the new address on the official site and update `sources.yaml`. |
| `The CSS selector ... matched nothing` | The page layout changed. Pick a new selector. |
| `No text could be read from this PDF` | It is probably a scanned image. The watcher still sees that the file changed; read it yourself. |
| A page shows almost no text | It probably needs JavaScript. Look for its RSS, API or PDF links. |
| The same changes come back every week | The `data/` folder was not committed and pushed after the last run. |
| `Could not make the PDF` | Run `.venv/bin/python -m playwright install chromium`, or set `CHROMIUM_PATH` to a Chrome or Chromium program. |
| `Stopped: ... not checked yet` | Check those items, then set them to approved or rejected. Use `--preview` to look first. |

## Limits

- It watches the pages you list; it does not crawl or search the web.
- It reads web pages, PDFs, RSS and Atom feeds and GET APIs. Pages that need a login, a search form or JavaScript have to be checked by hand.
- Scanned PDFs have no text to compare; the kit does not include OCR.
- It drafts; it does not decide. A person checks every item.
