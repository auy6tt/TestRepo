# Run the weekly watch and draft as a Routine

A Routine is a saved Claude Code task that runs in the cloud on a schedule, even when your computer is off. Here it does the repetitive part every week: check the sources, draft the items, build a preview and save everything to your repository.

You still check every item, and you send the issue yourself. The Routine never sends anything.

## Before you start (once)

1. **Keep the kit in a GitHub repository you own.** A Routine clones the repository at the start of every run. This repository works: the kit is in `kits/weekly-digest/` and the skill is in `.claude/skills/weekly-digest/`.
2. **Create your digest folder.** In a Claude Code session, ask: *"Use the weekly-digest skill to set up a new digest called ohio-bess from the local-gov-meetings template."* That creates `kits/weekly-digest/digests/ohio-bess/sources.yaml`. Replace the placeholder addresses with real official pages and fill in `terms_checked` for each one.
3. **Allow your sources in the network settings.** Cloud sessions can only reach package registries and a few developer sites by default, so government websites are blocked until you allow them.
   - At claude.ai/code, click the cloud icon above the message box, hover over your environment and click the settings icon.
   - Set **Network access** to **Custom** (called **Limited** in newer versions of the app).
   - Under **Allowed domains**, list every domain your sources use, one per line. `*.example.gov` covers all its subdomains.
   - Keep the package managers box ticked (**Also include default list of common package managers**, or **Allow package managers** in newer versions), so the kit's Python packages can still install.
   - Save. A Routine uses the environment you pick for it, so make sure it is this one.
4. **Test by hand.** In a session, run the watcher twice (the first run only saves snapshots). Any source that is still blocked shows "Blocked by the network policy (host)" in `changes.md`.
5. **Commit and push** the digest folder, including `data/`. The snapshots in `data/` are how next week's run knows what changed. Every cloud session starts from a fresh copy of your repository, so anything you do not push is lost.

## Create the Routine

1. Go to **claude.ai/code/routines** and click **New routine**. (In the desktop app: Code tab, then Routines, then New routine, then Cloud. On your own computer, `/schedule` in the terminal also works; it is not available inside a cloud session.)
2. **Name:** `Weekly watch: <digest name>`.
3. **Prompt:** paste the prompt below and replace `[DIGEST]` with your folder name.
4. **Repository:** pick the repository that holds the kit.
5. **Environment:** pick the environment where you allowed your sources' domains.
6. **Trigger:** Schedule, then Weekly. Pick a few minutes past the hour (for example Monday 6:07 AM), because runs set for exactly :00 can start late.
7. **Connectors:** remove all of them. This job needs none, and without email or chat connectors the Routine cannot contact anyone.
8. Click **Create**, then **Run now** to test it.

### Prompt to paste

```text
Run the weekly watch and draft for the digest in kits/weekly-digest/digests/[DIGEST].

1. Use the weekly-digest skill and set up its Python environment.
2. Run the watcher on kits/weekly-digest/digests/[DIGEST]/sources.yaml with the
   default output folder (issues/<this week>/).
3. Draft items.yaml in this week's issue folder from changes.json and the saved
   document text, following the skill's drafting guide. Every item gets
   status: needs_review and a link to the official document. Do not approve anything.
4. Build a preview with build_digest.py --preview.
5. Commit the digest's data/ folder and this week's issue folder, and push to main.
6. Finish with a short report: sources checked, changed, unchanged and errors
   (name any host blocked by the network policy), then the drafted items with
   their source links.

Never send email or messages, never publish anything and never contact anyone.
A person checks every item before anything is sent.
```

**Good to know**

- The prompt pushes to `main` so next week's run starts from this week's snapshots. If you prefer a pull request, ask for a branch and a pull request instead, and merge it before the next run; otherwise next week compares against old snapshots and repeats this week's changes.
- Runs use your plan's usage like any other session.
- A green status in the run list only means the session ran. Open the run and read the report.
- If a run says a host is blocked, add it under Allowed domains and click **Run now** again.

## Each week (30 to 90 minutes)

1. Open this week's run from the Routine's page. It is a normal session: read the report and `changes.md`.
2. Check every item with the review checklist below. Edit `items.yaml`, or tell Claude in the same session what to fix, for example *"W41-03: the hearing is at 6 PM, not 7 PM."*
3. For each item you checked, set `status: approved` and fill in `checked_by` and `checked_on`. Set `status: rejected` for anything you leave out. Only you approve items.
4. Ask Claude to build the final issue (`build_digest.py` without `--preview`), then commit and push.
5. Download the files from GitHub. Open the HTML and the PDF, click every link and import the `.ics` into a test calendar.
6. Send the issue yourself (see "Sending an issue" in the README). Check by hand any source that had an error this week.

## Review checklist

Before you approve an item:

- [ ] The link opens the official document itself: not a news story, a copy or a search page.
- [ ] Every fact in the title and summary is in that document: bodies, companies, case numbers, sizes and amounts.
- [ ] Every date and time matches the source, in the right time zone, and the deadline is the next thing that happens.
- [ ] Nothing newer changes it: look for a later notice, a cancellation or an updated agenda.
- [ ] The status words are exact: proposed or adopted, first reading or passed, filed or approved, recommended or awarded.
- [ ] The page, item or section reference is right.
- [ ] There is no personal data about private individuals: no names of residents, homeowners, speakers or sole traders, and no home addresses, phone numbers or personal emails.
- [ ] It gives no advice: it says what the document says, not what the reader should do, and "Why it matters" states facts.
- [ ] The words are your own: quotes are short and in quotation marks, and nothing is copied from paid services or law-firm alerts.
- [ ] If the source is a "current agenda" file that gets replaced, the source name says which meeting it is.

Before you send:

- [ ] Skim `changes.md`: nothing important is missing, and the skipped changes really are out of scope.
- [ ] Sources with errors this week were checked by hand, or the issue says which ones were not checked.
- [ ] The HTML and PDF look right on a phone and a computer, every link works and the calendar file imports.
- [ ] The footer has your postal address and a working unsubscribe or manage link.
