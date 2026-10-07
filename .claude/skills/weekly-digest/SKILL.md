---
name: weekly-digest
description: Runs the weekly-digest kit, which makes human-checked weekly briefs from official sources (packaging EPR updates, public-bid digests, local-government meeting watch, aid tenders, new commercial premises lists). Use when the user wants to check a digest's sources for changes, draft digest items from changes.json, prepare items for human review, build an issue's email, PDF, xlsx tracker and calendar file, or set up a new digest. Also use when a scheduled Routine asks for the weekly watch and draft.
argument-hint: "[digest name] [new | watch | draft | build]"
---

# Weekly digest

Human-checked weekly briefs from official sources. The kit is in `kits/weekly-digest/`; run every command below from that folder. Each digest has its own folder:

```text
kits/weekly-digest/digests/<name>/
  sources.yaml                  what to watch (start from templates/sources/)
  data/                         snapshots the watcher compares against (commit it)
  issues/<YYYY>-W<WW>/
    changes.json, changes.md    what changed this week
    items.yaml                  drafted, then reviewed, items
    output/                     .html and .txt email, .pdf, .xlsx, .ics
```

Request: $ARGUMENTS

If no step is named, find the newest issue folder for the digest and carry on from where it stopped: no `changes.json` → Watch; changes but no `items.yaml` → Draft; items still `draft` or `needs_review` → Review handoff; everything approved or rejected → Build.

## Rules that always apply

- Official sources and open-data APIs only. The watcher checks robots.txt. Never fetch a disallowed or blocked page another way, never log in to a portal, never work around a block.
- Link to official documents; never attach or repost them. Summarise in your own words.
- Never include personal data about private individuals (residents, homeowners, public commenters, sole traders): no names, home addresses, phone numbers or personal emails.
- Never write legal advice. Describe what documents say; never tell readers what they must do or whether a rule applies to them.
- A person checks every item. Set `status: approved` only when the user tells you in this conversation that they checked that item against its source, and fill in `checked_by` and `checked_on` as they say. Never send email, post or publish an issue.

## Setup (once per session)

```bash
cd kits/weekly-digest
test -x .venv/bin/python || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
```

Use `.venv/bin/python` for every script. To confirm the kit works (offline, about 20 seconds): `.venv/bin/python tests/selftest.py`.

## New digest

1. Copy the closest template from `templates/sources/` (`epr-packaging-us`, `public-bids-one-trade`, `local-gov-meetings`, `aid-tenders`, `new-commercial-premises`) to `digests/<name>/sources.yaml`.
2. Fill in `digest.name`, `scope` and `audience`, a real contact email in `settings.user_agent`, and the keywords.
3. Help the user replace the `example.gov` placeholders with real official pages, following the comments in the template. For each source they read the site's terms and set `terms_checked`.
4. Remind them to add every domain under Allowed domains in the environment's Network access settings (README, "Network access").
5. Run Watch once to save the first snapshots, then commit and push `digests/<name>/`.

## Watch

```bash
.venv/bin/python scripts/watch_sources.py digests/<name>
```

- Writes `issues/<this week>/changes.json` and `changes.md` in the digest folder and updates `data/`.
- A source's first check only saves a snapshot (`first_run`). Changes appear from the next run.
- Report every error to the user with its hint. "Blocked by the network policy (host)" means the host must be added under Allowed domains: do not retry or route around it. "Page not found" means the page moved: suggest finding the new address on the official site.
- `--dry-run` checks without updating snapshots. `--only "text"` checks only matching sources.

## Draft

Read [drafting-guide.md](drafting-guide.md) first. Then:

1. Read `changes.json`: the `changed` list with its added lines (PDF lines start with `[p. N]`, the page number), new links, new records and fetched `documents`. Open a document's `text_file` (relative to the digest folder) when the excerpt is not enough. Ignore `changed_without_keyword_match` unless the user asks.
2. Copy the `issue:` block and `sections:` from last week's `items.yaml` if there is one; otherwise start from `templates/items.example.yaml`.
3. Write `items.yaml` in this week's issue folder: one item per relevant event, every item `status: needs_review`, `source_url` pointing to the official document, and `review_notes` starting with `CHECK:` that list every date, number and status word to verify. List everything you left out under `skipped_changes` with a reason.
4. Validate and build a preview:

   ```bash
   .venv/bin/python scripts/build_digest.py digests/<name>/issues/<week>/items.yaml --preview --changes digests/<name>/issues/<week>/changes.json
   ```

   Fix any errors it prints, and act on its warnings (personal data, advice wording, dates already passed).

## Review handoff

Stop here and hand over to the user. Give a numbered list: item id, title, source link and what to check. Point to the review checklist in `templates/routine-setup.md`, and list sources with errors that need a manual check. Do not build the final issue until the user has approved or rejected every item.

## Build

When every item is approved or rejected:

```bash
.venv/bin/python scripts/build_digest.py digests/<name>/issues/<week>/items.yaml --changes digests/<name>/issues/<week>/changes.json
```

Exit code 3 means an item is still unchecked: go back to the review handoff. Look at the HTML and PDF (screenshots are fine) to confirm they render well. Tell the user where the files are and that they send the issue themselves (README, "Sending an issue").

## Save (cloud sessions and Routines)

Commit `digests/<name>/data/` and the week's issue folder, then push (to `main` unless the user or the Routine prompt says otherwise). Every cloud run starts from a fresh clone, so without the pushed snapshots the next run cannot tell what changed.

## Sample and tests

- `samples/battery-storage-ohio-week41/` is a complete fictional issue, from sources to finished files. `scripts/run_demo.py` rebuilds it offline.
- `tests/selftest.py` checks the watcher and the builder offline.
