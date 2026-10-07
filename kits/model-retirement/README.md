# Model retirement rescue kit

AI providers retire old model versions on fixed dates. After that date, every call to the old model fails, and the feature built on it stops working. Many small companies built AI features in 2023–25 on a specific model version and don't know their date is coming.

This kit lets you sell one service from day one: **find every model a client's code uses, move it to the successor, prove it still works, and hand over a before/after report.** It has scripts for the technical work, templates for the client, a Claude Code skill that walks you through each job, and a fictional sample you can show prospects.

Everything here uses placeholder model names such as `old-model-v1`. Real model names and dates go in `data/retirements.csv`, which you fill in from each provider's official page (see [Fill the retirement list](#fill-the-retirement-list)).

## The offer

> Your AI feature uses a model that is being retired. I find every place your code uses it, move it to the successor, and prove it still works with a side-by-side test on your real examples, before the deadline. Fixed price. You get a before/after report and a test set you can re-use next time.

## Who buys, and where to find them

**Who:**

- Small software companies whose AI feature (chat widget, email drafts, summaries, search) was built in 2023–25, often by a contractor who has since left.
- Agencies that sold AI bots or AI features to many clients. One fix pattern can be sold many times.
- Non-technical owners of apps built with no-code tools or WordPress plugins that call an AI model.

**What makes them buy:** an email from a provider saying a model is "deprecated", "retired" or "shutting down"; a deprecation notice on the provider's page; or errors after a shutdown date.

**Where:**

- Deprecation threads in the providers' developer forums. Answer questions helpfully; don't spam.
- Bubble, FlutterFlow and WordPress-plugin communities.
- Agencies that sold AI bots in 2023–24 (LinkedIn, their websites).
- A gig listing on Upwork or Fiverr. Buyers search for "model deprecated" and "model shutdown".
- Your own network: anyone who runs a small software product.

**Test it in one day:** publish a one-page "model shutdown checklist + fixed-price fix" (use the short version in `templates/fixed_price_offer.md`), list it as a gig, and message 15 agencies and no-code builders. Two replies or one job within 72 hours is a good sign.

## Price guide

| Job | Price |
|---|---|
| One feature (one prompt, one model call) | $300–800 |
| Whole app with several features and a reusable test set | $1,500–4,000 |
| Already broken (the date has passed), fixed the same week | Suggested: add 50% for urgent work |

The price goes up with the number of features, how much testing they need, missing staging environments, several providers, and short deadlines. Quote embeddings and fine-tuned models separately (see [Risks](#risks-and-how-to-handle-them)). A good follow-up offer: re-run the scan and the test set before the client's next retirement date.

## What's in the kit

```text
kits/model-retirement/
├── README.md                        this guide
├── requirements.txt                 Python packages (openpyxl, python-docx)
├── data/
│   └── retirements.csv              retirement list: fill it from the providers' pages
├── scripts/
│   ├── scan_models.py               finds model references and checks them against the list
│   ├── compare_runs.py              runs old vs new on a test set and writes an Excel comparison
│   ├── runners.py                   how a test case reaches a model: mock, recorded, client API stub
│   └── md_to_docx.py                turns a Markdown report into a Word file
├── templates/
│   ├── scoping_questionnaire.md     questions to send before you quote
│   ├── fixed_price_offer.md         short offer, price guide, gig text
│   ├── client_report_template.md    the report you deliver (and .docx version)
│   ├── runner_config_template.json  settings for one side of a comparison
│   └── test_set_template.jsonl      format of the test set
└── samples/                         fictional portfolio sample (see "The sample" below)
```

The Claude Code skill lives in `.claude/skills/model-retirement/SKILL.md` at the root of this repo.

## Setup

The scanner needs only Python 3.9 or newer. The comparison and report scripts need two packages. The cloud container is temporary, so do this at the start of each session:

```sh
python3 -m venv /tmp/mr-venv
/tmp/mr-venv/bin/pip install -r kits/model-retirement/requirements.txt
```

Then run the scripts with `/tmp/mr-venv/bin/python`, or activate the environment first with `. /tmp/mr-venv/bin/activate`. The commands below assume you are in the root of this repo with the environment active.

Keep each client's work (scan, test set, configs, results, report) in its own private folder, for example `~/client-work/acme`. Never put it inside this repo if the repo is public. The container is temporary, so make that folder a private Git repo and push it as you go.

## Step by step

### 1. Scope and quote

1. Send `templates/scoping_questionnaire.md`. It asks which features use AI, where the code is, whether there is a staging environment, and whether the client can share 20–50 real examples.
2. Quote a fixed price with `templates/fixed_price_offer.md`. Take 50% up front.
3. Get read access to the code. Agree that you work on a new branch and the client releases.

### 2. Fill the retirement list

Fill `data/retirements.csv` from each provider's official page before every job (details in [Fill the retirement list](#fill-the-retirement-list)). Keep a copy per client if they use different providers.

### 3. Scan the code

```sh
python3 kits/model-retirement/scripts/scan_models.py ~/client-work/acme/repo \
    --retirements kits/model-retirement/data/retirements.csv --out-dir ~/client-work/acme/scan
```

Open `model_scan.md`. Section 1 lists what is retired or retires within 90 days. Open every row in the code and confirm it is a real model call. Then:

- Ask the client for the real values of the environment variables in section 4. A setting in their hosting dashboard overrides the default in the code.
- Ask about anything the scan cannot see: model names stored in a database, set in a no-code tool, or used in another repo or a scheduled job.
- Write down the parameters next to each call (temperature, top_p, max_tokens and so on).

### 4. Plan the change

For each retiring model, take the replacement from the provider's page and read the provider's migration notes. Newer models can reject old parameters, rename them, or count tokens differently. List what has to change and confirm the scope with the client.

### 5. Make the change on a branch

- Create a branch in the client's repo. Never commit to the main branch and never deploy to production yourself unless the contract says so.
- Change the model names. Put each name in one place (a config file or an environment variable), so the next change is one line.
- Fix parameters the new model rejects.
- Keep the old model selectable by a setting until the retirement date, so the client can roll back.

### 6. Build the test set

Collect 20–50 real inputs per feature, with names, emails, phone numbers and addresses removed. Include hard cases: very long, very short, angry, other languages, missing information. Save them as JSONL (`templates/test_set_template.jsonl` shows the format) and add simple checks such as `must_include` for facts the answer must keep. Ask the client to approve the test set.

### 7. Compare old and new

1. Copy `templates/runner_config_template.json` to `runner_old.json` and `runner_new.json` in `~/client-work/acme/compare`. Set the model, the settings and the prompt for each side.
2. Connect the runner to the client's API. Copy the `client_api_run` stub from `scripts/runners.py` into a file in the client's work folder (for example `client_runner.py`), fill in the marked block, and set `"runner": "client_runner.py:client_api_run"`. Calling the client's own function (example C in the stub) is best, because it tests their real code. Claude Code can do this with you.
3. Check everything without calling anything: add `--dry-run`. It shows the number of calls and a rough maximum cost.
4. The comparison runs **in staging, with the client's own API key, while the old model still works**. Either the client runs it, or they give you a staging key with a spending limit and you set it as an environment variable (`export CLIENT_API_KEY=...`). Never paste a key into a file or a chat.
5. Run it (calls to a real API need `--yes`):

```sh
W=~/client-work/acme/compare
python kits/model-retirement/scripts/compare_runs.py --tests $W/test_set.jsonl \
    --old $W/runner_old.json --new $W/runner_new.json --out $W/comparison.xlsx --yes
```

### 8. Re-tune the prompts

Open `comparison.xlsx`. Read the cases where the checks failed or the answers differ a lot. Adjust the new prompt (in `runner_new.json` and in the code), and run the comparison again. Two or three rounds are normal. Write down what you changed and why for the report.

### 9. Grade

Someone who knows the client's business grades every case in the yellow columns of the Comparison sheet: **Preferred** (old, new or same) and **New OK?** (yes or no). The Summary sheet counts the grades. If the reviewer prefers a plain spreadsheet, have them fill a CSV with `id,preferred,new_ok,notes` and add `--grades grades.csv` when you re-build the workbook.

### 10. Report and hand over

1. Copy `templates/client_report_template.md` to the client's folder as `report.md` and fill it in.
2. Convert it: `python kits/model-retirement/scripts/md_to_docx.py ~/client-work/acme/report.md ~/client-work/acme/report.docx --footer "Prepared for Acme"`.
3. Send the report, `comparison.xlsx`, `model_scan.md`, the test set and the pull request link.
4. The client reviews, merges and releases. Agree a 7-day watch period.
5. Invoice the second 50%. Offer a reminder and a re-run before the next retirement date in the scan.

## Fill the retirement list

`data/retirements.csv` ships with one fake example row. Delete it and add one row per model ID:

| Column | What to put |
|---|---|
| `provider` | Who runs the model. Add a separate row per cloud platform (for example "Azure" or "AWS Bedrock"), because platforms set their own dates |
| `model_id` | The exact ID string that appears in code, copied from the provider's page. List each dated version and each alias separately |
| `retirement_date` | The shutdown date as YYYY-MM-DD. If the page gives only a month, use the first day and say so in `notes`. Leave it empty if a model is deprecated but has no date yet |
| `replacement` | The model the provider recommends instead |
| `source_url` | The exact page you copied the row from |
| `notes` | "checked YYYY-MM-DD", plus anything special: an earlier deprecation date, regions, fine-tuned models |

Where to find the official pages. Search the provider's own documentation site, and only trust that site:

| Provider | Page to look for |
|---|---|
| OpenAI | "Deprecations" in the API platform documentation |
| Anthropic | "Model deprecations" in Anthropic's developer documentation |
| Google Cloud (Vertex AI) | "Model versions and lifecycle" in the Vertex AI generative AI documentation |
| Google AI Studio API | The models page and the changelog in the Google AI for Developers documentation |
| Microsoft Azure | "Model deprecations and retirements" for Azure OpenAI in Microsoft Learn |
| AWS Bedrock | "Model lifecycle" in the Amazon Bedrock user guide |
| Any other provider or plugin | Their "deprecations", "model lifecycle" or "changelog" page, plus the page of the underlying provider |

Rules:

- Copy dates only from official pages. Never from memory, blog posts or an AI chat answer, including Claude's. Model names and dates change often.
- Providers also email account owners before a retirement. Ask the client to forward those emails.
- Check the page again before each job and a month before each deadline. Dates sometimes move.

## How to run each script

Run these from the kit folder (`cd kits/model-retirement`), or give full paths.

### scan_models.py

```sh
python3 scripts/scan_models.py PATH/TO/REPO --retirements data/retirements.csv --out-dir scan_output
```

| Option | What it does |
|---|---|
| `--retirements FILE` | The retirement list. Default: `data/retirements.csv` |
| `--out-dir DIR` | Where `model_scan.csv` and `model_scan.md` go. Default: `scan_output` |
| `--today YYYY-MM-DD` | Pretend today is this date. Use it for repeatable reports |
| `--warn-days 90` | How many days ahead counts as "retiring soon" |
| `--exclude 'tests/*'` | Skip matching files or folders (repeatable) |
| `--ext .lua` | Also scan files with this extension (repeatable) |
| `--fail-on-flagged` | Exit with code 2 if anything is retired or retiring soon (for automatic checks) |

It reads Python, JavaScript, TypeScript and other code files, notebooks, JSON, YAML, TOML, INI, `.env` files, shell scripts and Dockerfiles. It skips `node_modules`, virtual environments, build folders and files over 2 MB. Secrets in the code lines it shows are replaced with `***`.

Each reference gets a status: **RETIRED**, **RETIRING SOON** (within 90 days), **SCHEDULED** (later), **LISTED (NO DATE)**, **CHECK VALUE** (the model name comes from a variable or setting it could not resolve) or **NOT IN LIST** (no entry in your list, which does not prove the model is safe).

### compare_runs.py

```sh
python scripts/compare_runs.py --tests test_set.jsonl --old runner_old.json --new runner_new.json --out comparison.xlsx
```

| Option | What it does |
|---|---|
| `--dry-run` | Check the files and show the plan and a rough maximum cost. Calls nothing |
| `--yes` | Required when a runner calls a real API |
| `--grades FILE` | CSV with `id,preferred,new_ok,notes` to fill the grading columns |
| `--limit N` | Only the first N cases (a cheap first try) |
| `--delay S` | Wait S seconds after each call (for rate limits) |
| `--retries N` | Retry a failed call N times (default 2) |
| `--raw-out FILE` | Where to save every prompt and answer. Default: `comparison_raw.jsonl` next to the Excel file |

**Test set** (JSONL, one case per line). Only `input` is required:

| Field | Meaning |
|---|---|
| `id` | Short name for the case, such as `S01` |
| `feature` | Which feature it tests. Runner configs can set prompts per feature |
| `input` | What the feature receives |
| `system` | System prompt, if the runner config doesn't set one |
| `expected` | Notes on what a good answer contains (for the grader) |
| `must_include` / `must_not_include` | Phrases checked automatically |
| `expect_json` | `true` if the answer must be valid JSON |
| `max_chars` | Longest acceptable answer |
| `tags` | Labels shown in the sheet |

**Runner config** (JSON): `name`, `runner`, `model`, `params` (settings sent to the model), optional `system` and `prompt_template` (`{input}` is replaced by the case input), optional `features` (settings per feature; `null` removes a setting), `price_per_1m_input_tokens`, `price_per_1m_output_tokens`, and `api_key_env` (the name of the environment variable that holds the key, never the key itself). Keys starting with `_` are notes. See `templates/runner_config_template.json`.

**Runners:**

| Runner | Use it for |
|---|---|
| `mock` | Testing the whole process with fake answers. No key, no cost |
| `recorded` | Replaying saved answers from a JSONL file (`recorded_outputs`). Use it when the old model is already retired and you only have its answers from logs, or to reuse one side of an earlier run (`recorded_side`: `old` or `new`) |
| `client_api` | The stub in `scripts/runners.py` that shows where the client's API call goes. It reads the key from the environment variable named in `api_key_env`. Copy it into a runner file for each client (step 7) |
| `client_runner.py:client_api_run` | Your own file and function, with the shape `(prompt, system, config, case)` returning `{"output": ...}`. The path is relative to the runner config |

The workbook has three sheets. **Summary**: run details, averages, changes, checks, and live counts of the human grades. **Comparison**: one row per case with both answers, lengths, a simple similarity score, response times, tokens, costs, check results, errors and the yellow grading columns. **Settings**: the full configuration of both sides.

### md_to_docx.py

```sh
python scripts/md_to_docx.py report.md report.docx --footer "Prepared for Client Name"
```

It handles headings, paragraphs, bold, italic, code, links, bullet and numbered lists, tick boxes, tables, quotes and code blocks. Text inside `<!-- ... -->` is left out, so you can keep notes to yourself in the Markdown.

## Checklist

- [ ] Scoping answers received, fixed price agreed, 50% paid
- [ ] Read access to the code, new branch created, staging environment and staging key available
- [ ] Retirement list filled from the official pages, with the date you checked
- [ ] Scan run, every hit confirmed in the code
- [ ] Environment variable and dashboard values confirmed with the client
- [ ] Replacement models and parameter changes checked in the providers' migration notes
- [ ] Test set built (20–50 cases per feature), personal details removed, approved by the client
- [ ] Old vs new comparison run in staging with the client's key, before the retirement date
- [ ] Prompts re-tuned and the comparison re-run
- [ ] Every case graded by the client's reviewer
- [ ] Changes in a pull request, with release and rollback steps
- [ ] Report, `comparison.xlsx`, `model_scan.md` and test set sent
- [ ] Client released, 7-day watch done, final invoice sent
- [ ] Reminders set for the next retirement dates in the scan

## Risks and how to handle them

**You touch production code.** Work on a branch and open a pull request. Test in staging. The client reviews and releases. Write the rollback steps in the report, and remember that rolling back to the old model only works until its retirement date.

**API keys and accounts.** All test calls use the client's own API key and the client's bill, ideally a staging key with a spending limit. Keys stay in environment variables, never in files, configs or chats. Never run a client's system or test calls on your personal Claude subscription. Claude Code helps you read and change code; the client's AI features must call their own API account.

**Client data.** Test sets often start from real customer messages. Remove personal details before they leave the client, keep client work in a private repo or folder (never this repo if it is public), and delete your copies when the job ends. Turn off model training in your Claude privacy settings before you handle client files, and sign an NDA if asked.

**Never generate training data for other models.** Don't use Claude, or any provider's outputs, to create training or fine-tuning data for another AI model. Provider terms forbid it. The test set is for testing only. Turn down requests to build a training set from model outputs.

**Post-deadline emergencies.** If the date has passed, the feature is already failing and a live side-by-side test is no longer possible.

1. Confirm the cause in the client's logs (typically a "model not found" or "deprecated" error).
2. Make the smallest safe fix on a branch: the replacement model name, plus any parameters it rejects. The client releases it through their normal process, with written approval.
3. Test after the fix: compare the new model against old answers saved in logs, using the `recorded` runner.
4. Charge an urgent rate and say clearly what could and could not be tested.
5. Put in writing that the provider's retirement caused the outage, not your work. Don't accept open-ended blame for breakage.

**New answers are never identical.** Promise "as good or better on the agreed test set", not "the same". The client's reviewer signs off the grades.

**Parameters and token counts change.** Newer models may reject or rename settings (for example the output limit, or temperature and top_p used together) and count tokens differently, which changes cost. The comparison shows both. Check the provider's migration notes.

**Hidden references.** Model names can live in hosting dashboards, databases, no-code tools, other repos and scheduled jobs. The scan is a helper, not a guarantee. Ask.

**Embeddings and fine-tuned models.** A new embedding model means re-processing every stored document and re-testing search. A retired base model means the fine-tune has to be rebuilt. Both are separate, bigger quotes.

**Cloud platforms.** Azure, AWS Bedrock and Google Cloud set their own retirement dates. On Azure, the code holds a deployment name, not a model ID; check which model version each deployment uses in the Azure portal.

**Your liability.** Put the scope in writing, keep releases with the client, and limit your liability to the fee.

## Using the Claude Code skill

Open Claude Code in this repo and type:

```text
/model-retirement path/to/client/repo
```

or ask in plain words, for example "help me move this client's AI feature off a model that's being retired". Claude follows `.claude/skills/model-retirement/SKILL.md`: it scans, explains the findings, helps you change the code on a branch, builds the test set and runner, runs the comparison and drafts the report. It stops for your approval before anything that touches client systems or costs money.

## The sample

`samples/` is a complete, **fictional** job for your portfolio. Acme Home Goods is not a real company, and the model names, providers, dates, prices and results are made up. The comparison comes from the mock runner, so say so if a prospect asks.

| File | What it shows |
|---|---|
| `acme_support_app/` | A tiny support app in Python and TypeScript, before the change. It uses models from two fictional providers through settings, environment variables, a YAML file and an old script |
| `sample_retirements.csv` | A fictional retirement list for that app |
| `scan_output/model_scan.md` and `.csv` | The scan: 12 references in 9 files, 6 retired or retiring soon |
| `compare/` | Test set (10 cases), both runner configs, canned mock answers, the grader's CSV, and the results: `comparison.xlsx` and `comparison_raw.jsonl` |
| `sample_report.md` and `.docx` | The finished client report |

Before you show it to anyone, put your name in `samples/sample_report.md` (it says "[Your name]" twice), then rebuild the Word file:

```sh
cd kits/model-retirement/samples
python ../scripts/md_to_docx.py sample_report.md sample_report.docx --footer "Fictional sample report"
```

To rebuild the whole sample from scratch:

```sh
cd kits/model-retirement
python3 scripts/scan_models.py samples/acme_support_app --retirements samples/sample_retirements.csv \
    --out-dir samples/scan_output --today 2026-10-07
cd samples/compare
python ../../scripts/compare_runs.py --tests test_set.jsonl --old runner_old.json --new runner_new.json \
    --out comparison.xlsx --grades grades.csv
cd ..
python ../scripts/md_to_docx.py sample_report.md sample_report.docx --footer "Fictional sample report"
```
