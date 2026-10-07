# Starter kits

Ten ready-to-use kits for the hidden niches in [PLAYBOOK.md](../PLAYBOOK.md). Each one gives you what you need to offer a niche as a paid service. Every kit has:

- **A README:** the offer, who buys and where to find them, a price guide, the step-by-step process, a quality checklist and the rules to follow.
- **Scripts** that do the mechanical work and check the results.
- **Templates** for intake, delivery and client messages.
- **A fictional sample** to show prospects as your first portfolio piece.
- **A Claude Code skill** in [`.claude/skills/`](../.claude/skills/), so Claude follows the kit's process.

Prices are estimates from the October 2026 research. Check them against your market before you quote. **Beginner** is the playbook's score out of 5 for how easy the niche is to start from zero (5 = easiest). Kits scored 2 need some background knowledge first, such as basic security for `cra-readiness` and `security-questionnaire`.

| Kit | What you sell | Price guide (est.) | Beginner | Skill |
|---|---|---|---|---|
| [board-minutes](board-minutes/) | Formal board minutes for HOA, condo, nonprofit and church boards, from the meeting transcript | $75–200 a meeting, or $100–300 a month per association | 5 | `/board-minutes` |
| [cra-readiness](cra-readiness/) | EU Cyber Resilience Act readiness packs for small device and software makers: SBOM, vulnerability report, security.txt, gap checklist | €500–2,000 a product, plus €100–300 a month to keep it current | 2 | `/cra-readiness` |
| [doc-accessibility](doc-accessibility/) | Making public bodies' and businesses' documents and PDFs accessible: inventory, fixes and a report | $5–25 a page; a site inventory $300–1,500 | 3 | `/doc-accessibility` |
| [model-retirement](model-retirement/) | Moving apps' AI features off models that are being retired, with before-and-after tests | $300–800 a feature; $1,500–4,000 for a whole app | 3 | `/model-retirement` |
| [pdf-binder](pdf-binder/) | Safety data sheet binders and chemical lists, and construction submittal and handover (O&M) binders | $300–1,500 a site (SDS); $300–3,000 a package or binder | 3 | `/pdf-binder` |
| [publisher-rescue](publisher-rescue/) | Turning old Microsoft Publisher files into searchable PDFs, and rebuilding the layouts people reuse as Word or PowerPoint templates | About $150–600 per organization | 5 | `/publisher-rescue` |
| [redcap-xlsform](redcap-xlsform/) | REDCap data dictionaries and KoboToolbox/ODK forms built from a study's questionnaire | $200–500 a simple form set; $800–2,000 a multi-visit study | 4 | `/redcap-xlsform` |
| [replication-package](replication-package/) | Getting researchers' code and data ready for a journal's reproducibility check | $300–600 a check; $800–2,500 a full clean-up | 3 | `/replication-package` |
| [security-questionnaire](security-questionnaire/) | Filling in customers' security questionnaires for small software companies, from an answer library | $250–1,500 a questionnaire | 2 | `/security-questionnaire` |
| [weekly-digest](weekly-digest/) | Regular (weekly or monthly) briefs from official sources: packaging law, public bids, council meetings, aid tenders, new commercial premises | $15–500 a month for most briefs; $300–800 a month white-label | 3–4 | `/weekly-digest` |

## Set up (each new cloud session)

Cloud sessions start from a clean machine, so set up the kits you need at the start of each session:

```bash
bash kits/setup.sh                    # every kit: about 3 minutes the first time
bash kits/setup.sh board-minutes      # or only the kits you name
bash kits/setup.sh --list             # which Python each kit's scripts run with
```

It installs the system tools (parts of LibreOffice, Tesseract OCR, Ghostscript, Poppler and fonts), then each kit's Python environment, in the place that kit's README says. It ends with a table of the Python to use for each kit.

**Optional: have the system tools ready in every session.** Open your environment's settings: at [claude.ai/code](https://claude.ai/code), click the cloud icon showing the environment's name above the message box, hover over the environment and click the settings icon. Paste this into **Setup script** and save:

```bash
apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends libreoffice-writer libreoffice-calc libreoffice-draw libreoffice-impress libmspub-tools poppler-utils tesseract-ocr ghostscript fonts-crosextra-carlito fonts-crosextra-caladea fonts-liberation fonts-dejavu-core python3-venv
```

The setup script runs as root before Claude starts. When it finishes within about five minutes (this one takes about two), the result is cached, so later sessions start with the tools installed. `bash kits/setup.sh` then only sets up the Python environments, which takes under a minute. The details are in the [cloud environments documentation](https://code.claude.com/docs/en/cloud-environments#setup-scripts).

## How to use a kit

1. **Read its README** first: the offer, the buyers, the prices and the rules.
2. **Set it up** with `bash kits/setup.sh <kit>`.
3. **Put your name on the sample** and look through it. It's your first portfolio piece. Always say it's fictional.
4. **Find the first clients** with the kit's first message and the niche's one-day test in [PLAYBOOK.md](../PLAYBOOK.md).
5. **Deliver with Claude Code.** Type `/<kit>`, for example `/board-minutes`, or just describe the job, such as "Use the pdf-binder skill to build an SDS binder from clients/riverside/sds". Claude follows the kit's steps, runs its scripts and checks the results. You review everything before it goes to the client.

## Rules for every kit

- **Turn off model training** in Claude's privacy settings before you handle anyone's files.
- **Keep client files out of this repository.** It is public. Put client files in `clients/`, `work/`, `jobs/` or `reports/` (at the repo root or inside a kit; git ignores them), or in a private repository per client. Cloud sessions are temporary, so download what you deliver.
- **Never invent facts.** Mark anything unclear and ask the client. The scripts flag problems; they don't replace your own check.
- **Say you use AI tools** and that you check every result yourself.
- **Check dates and rules on the official source** (OSHA, the EU, journals, platforms) before you quote them to a client. They change.
- **Don't give legal, safety or compliance advice.** You prepare documents; the client and their advisers decide.
