# Claude Income Playbook

Research and starter kits for earning money with a Claude Max plan when you're starting from zero: no reviews, no portfolio, no network.

- **[Interactive playbook](https://claude.ai/artifact/6XujurYFWKFDJQDofE8n9M)**: the published page with filters, a fee calculator and a 30-day checklist. It's private to your Claude account unless you share it.
- **[PLAYBOOK.md](PLAYBOOK.md)**: the full research. Best bets for beginners, 44 hidden niches with real demand and few competitors, where to find first clients with zero reviews, 36 ways to earn with prices and demand evidence, platforms and fees, rules, a 30-day plan and sources.
- **[kits/](kits/)**: 10 starter kits that cover 14 of the hidden niches. Each has the offer, prices, the step-by-step process, scripts, templates, a fictional portfolio sample and a Claude Code skill.
- **[templates/](templates/)**: copy-ready messages, proposals, a gig description, an intake form, an invoice and a one-page agreement.
- **[playbook/index.html](playbook/index.html)**: the same page as a file you can open in any browser.

## Start here

1. Read **Start here**, **Hidden niches**, **First clients** and **Rules** in the playbook. That takes about 30 minutes.
2. Turn off model training in Claude's privacy settings before you handle anyone else's files.
3. Pick one offer. If its niche has a starter kit, read the kit's README and run `bash kits/setup.sh <kit>` (see [kits/README.md](kits/README.md)).
4. Work through the **30-day plan** one week at a time.

## Using this repo with Claude Code

Each starter kit comes with a skill. Type `/<kit>` in Claude Code, for example `/board-minutes` or `/pdf-binder`, or describe the job in plain words and Claude uses the matching skill.

You can also ask for things like:

- "Build a portfolio sample in `samples/cafe-site`: a one-page website for a made-up café. Then take phone and desktop screenshots."
- "Here's a messy spreadsheet. Fix the formulas, add a summary tab with check totals, and explain what you changed."
- "Write an Upwork proposal for this job post using `templates/upwork-proposal.md`. Keep it under 150 words."
- "Find 15 businesses in [category] in [city] that have no website, and list them in a table. Use public info only."

Cloud sessions start from a clean machine. Run `bash kits/setup.sh` (or name only the kits you need) at the start of each session, and keep each client's work in its own private repo or a folder git ignores. Commit and push as you go.

## Editing the playbook

The page and the markdown are generated from the data files in `playbook/src/`. Edit those, then run:

```sh
node playbook/src/build.mjs
```

This rewrites `PLAYBOOK.md`, `templates/` and `playbook/index.html`. Add `--url <link>` to keep the published page's link in `PLAYBOOK.md`.
