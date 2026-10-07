# Claude Income Playbook

Research and starter kits for earning money with a Claude Max plan when you're starting from zero: no reviews, no portfolio, no network.

- **[Interactive playbook](https://claude.ai/artifact/6XujurYFWKFDJQDofE8n9M)**: the published page with filters, a fee calculator and a 30-day checklist. It's private to your Claude account unless you share it.
- **[PLAYBOOK.md](PLAYBOOK.md)**: the full research. Best bets for beginners, 44 hidden niches with real demand and few competitors, where to find first clients with zero reviews, 36 ways to earn with prices and demand evidence, platforms and fees, rules, a 30-day plan and sources.
- **[kits/](kits/)**: 10 starter kits that cover 15 of the hidden niches. Each has the offer, prices, the step-by-step process, scripts, templates, a fictional portfolio sample and a Claude Code skill.
- **[templates/](templates/)**: copy-ready messages, proposals, a gig description, an intake form, an invoice and a one-page agreement.
- **[playbook/index.html](playbook/index.html)**: the same page as a file you can open in any browser.

## Start here

1. Read **Start here**, **First clients** and **Rules** in the playbook (under an hour). Then look through **Hidden niches** for one that fits you.
2. Turn off model training in Claude's privacy settings before you handle anyone else's files.
3. Start with pick 1 in **Start here** (spreadsheet fixes) this week: small jobs are the fastest way to a first review.
4. When you're ready for a less crowded market, choose a hidden niche with a starter kit and a high Beginner score. Read the kit's README and run `bash kits/setup.sh <kit>` (see [kits/README.md](kits/README.md)).
5. Work through the **30-day plan** one week at a time.

> **This repository is public:** anyone can see it on GitHub. Never put client files, passwords or personal data in it. Client work goes in `clients/`, `work/`, `jobs/` or `reports/` (git ignores these folders) or in a private repository. You can make this repository private in its GitHub settings.

## Using this repo with Claude Code

Each starter kit comes with a skill. Type `/<kit>` in Claude Code, for example `/board-minutes` or `/pdf-binder`, or describe the job in plain words and Claude uses the matching skill.

You can also ask for things like:

- "Build a portfolio sample in `samples/cafe-site`: a one-page website for a made-up café. Then take phone and desktop screenshots."
- "Here's a messy spreadsheet. Fix the formulas, add a summary tab with check totals, and explain what you changed."
- "Write an Upwork proposal for this job post using `templates/upwork-proposal.md`. Keep it under 150 words."
- "Find 15 businesses in [category] in [city] that have no website, and list them in a table. Use public info only."

Cloud sessions start from a clean machine. Run `bash kits/setup.sh` (or name only the kits you need) at the start of each session. Keep each client's work in a folder git ignores or in its own private repo, and commit and push your own changes to the playbook or kits as you go.

## Editing the playbook

The page and the markdown are generated from the data files in `playbook/src/`. Edit those, then run:

```sh
node playbook/src/build.mjs --url https://claude.ai/artifact/6XujurYFWKFDJQDofE8n9M
```

This rewrites `PLAYBOOK.md`, `templates/` and `playbook/index.html`. Keep `--url` so `PLAYBOOK.md` keeps the link to the interactive page. Then ask Claude to republish the interactive page so it shows your changes.
