# Claude Income Playbook

Research and a starter kit for earning money with a Claude Max plan when you're starting from zero: no reviews, no portfolio, no network.

- **[Interactive playbook](https://claude.ai/artifact/6XujurYFWKFDJQDofE8n9M)**: the published page with filters, a fee calculator and a 30-day checklist. It's private to your Claude account unless you share it.
- **[PLAYBOOK.md](PLAYBOOK.md)**: the full research. Best bets, where to find first clients with zero reviews, 36 ways to earn with prices and demand evidence, platforms and fees, rules, a 30-day plan and sources.
- **[templates/](templates/)**: copy-ready messages, proposals, a gig description, an intake form and a one-page agreement.
- **[playbook/index.html](playbook/index.html)**: the same page as a file you can open in any browser.

## Start here

1. Read **Start here**, **First clients** and **Rules**. That takes about 15 minutes.
2. Turn off model training in Claude's privacy settings before you handle anyone else's files.
3. Work through the **30-day plan** one week at a time.

## Using this repo with Claude Code

Ask Claude for things like:

- "Build a portfolio sample in `samples/cafe-site`: a one-page website for a made-up café. Then take phone and desktop screenshots."
- "Here's a messy spreadsheet. Fix the formulas, add a summary tab with check totals, and explain what you changed."
- "Write an Upwork proposal for this job post using `templates/upwork-proposal.md`. Keep it under 150 words."
- "Find 15 businesses in [category] in [city] that have no website, and list them in a table. Use public info only."

Keep each client's work in its own folder or repo and commit as you go. This cloud container is temporary.

## Editing the playbook

The page and the markdown are generated from the data files in `playbook/src/`. Edit those, then run:

```sh
node playbook/src/build.mjs
```

This rewrites `PLAYBOOK.md`, `templates/` and `playbook/index.html`. Add `--url <link>` to keep the published page's link in `PLAYBOOK.md`.
