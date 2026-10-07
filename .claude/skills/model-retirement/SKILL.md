---
name: model-retirement
description: Rescue a client's AI feature before its model version is retired. Scans a codebase for every AI model reference and its parameters, checks them against a retirement list, moves the code to the successor model on a branch, re-tunes prompts, runs old vs new side by side on a test set, and writes the before/after client report. Use when the user mentions a model deprecation, retirement or shutdown, an AI provider's deprecation email, migrating an app to a newer model, or the model-retirement kit.
argument-hint: "[path-to-client-repo]"
---

# Model retirement rescue

Kit: `${CLAUDE_PROJECT_DIR}/kits/model-retirement` (called KIT below). KIT/README.md has the full process, price guide, checklist and risks. KIT/samples/ is a finished fictional job; match its structure and tone.

Client repo: `$ARGUMENTS`. If that is empty, ask for the path or repository. Clone a repository into `WORK/repo` (see Setup).

## Rules that apply to every step

1. **No model names, IDs or dates from memory.** Retirement dates and replacements come only from the provider's official deprecations page. Fetch it if you can reach it; otherwise ask the user to open it and paste the text. Show the rows you extracted and get a yes before saving. Record `source_url` and "checked YYYY-MM-DD" in `notes`. Keep the kit's own files free of real model names: real names belong only in client work files and in `KIT/data/retirements.csv`.
2. **Client code changes happen on a new branch only.** Never commit to the main branch, merge, deploy, or change production settings. Ask before creating the branch, pushing it, or opening a pull request.
3. **Client keys stay with the client.** Test calls use the client's own staging API key, set in an environment variable whose name goes in `api_key_env`. Never ask for a key in chat, never write one to a file, never print environment variable values. Never run the client's system or test calls through the user's own Claude subscription.
4. **Real API calls cost the client money.** Always run `--dry-run` first, show the plan and the rough maximum cost, and get the user's explicit OK before running with `--yes`. Offer the client the exact command if they prefer to run it themselves.
5. **Client data stays private.** Test inputs must have names, emails, phone numbers and addresses removed. Keep client files (their code, scans, test sets, configs, results, reports) only in `clients/<client-name>/` at the repo root, which git ignores. Never write them anywhere else in this repo (it may be public), and never commit them. Never present invented data as real customer data.
6. **Never create training or fine-tuning data for other models** from model outputs. The test set is for testing only.
7. **If a retirement date has already passed**, switch to the emergency path at the end of this file.

## Setup

Set up the kit's Python once per session. The scanner needs only Python 3; the comparison and report scripts need packages.

```sh
test -x /tmp/mr-venv/bin/python || bash ${CLAUDE_PROJECT_DIR}/kits/setup.sh model-retirement
```

- `bash kits/setup.sh --list` shows this kit's Python: `/tmp/mr-venv/bin/python` (PY below). Run every script with PY, never a bare `python`. If `kits/setup.sh` is missing or fails, run `python3 -m venv /tmp/mr-venv && /tmp/mr-venv/bin/pip install -q -r ${CLAUDE_PROJECT_DIR}/kits/model-retirement/requirements.txt`.
- Client work lives in `${CLAUDE_PROJECT_DIR}/clients/<client-name>/` (git ignores `clients/`), with the client's code in `repo/` and subfolders `scan/` and `compare/`. Call it WORK below. Suggest the user makes WORK a private Git repo of its own and pushes it, because the cloud container is temporary.

## Process

### 1. Scope and quote

- If the client hasn't answered the scoping questions, fill `KIT/templates/scoping_questionnaire.md` for the user to send.
- Draft the quote from `KIT/templates/fixed_price_offer.md` using the price guide in KIT/README.md (estimates): $300–800 per feature, $1,500–4,000 per app with a reusable test set. Tell the user to check them against their market.

### 2. Retirement list

- Read `KIT/data/retirements.csv`. If it only has the fake row `example-model-2023`, fill it first (rule 1). One row per model ID per platform (Azure, Bedrock and Google Cloud set their own dates), dates as YYYY-MM-DD, empty date if none is announced. Delete the fake row.
- Use a per-client copy (`WORK/retirements.csv`) when the client's providers differ.

### 3. Scan

```sh
/tmp/mr-venv/bin/python ${CLAUDE_PROJECT_DIR}/kits/model-retirement/scripts/scan_models.py <client-repo> --retirements <list.csv> --out-dir WORK/scan
```

- Read `WORK/scan/model_scan.md`. Open every row of sections 1 and 2 in the code and confirm it is a real model call.
- Look for misses: grep the repo for each retiring model ID, plus wrapper functions, config loaders, infrastructure files and scheduled jobs.
- Collect questions for the client: real values of the environment variables in section 4 (hosting settings override code defaults), model names set in dashboards, databases, no-code tools or other repos.
- Tell the user, in plain words: which features use which models, what retires when, the parameters each call sends, and the open questions.

### 4. Plan the change

- For each retiring model, take the replacement from the list. Ask the user to check the provider's migration notes for parameter changes. Mark anything you suspect but have not seen in official notes as "to verify". Typical issues: a renamed output-limit setting, limits on temperature or top_p, removed features, different token counting.
- Agree the scope. Flag embeddings (need re-indexing) and fine-tuned models (need rebuilding) as separate jobs.

### 5. Change the code on a branch

- After the user agrees, create a branch such as `model-update-YYYY-MM` in the client repo.
- Put each model name in one place (a config value or an environment variable). Keep the old model selectable by a setting until its retirement date, for rollback.
- Fix the parameters the new model rejects. Update `.env.example`, never real `.env` files or secrets.
- Re-run the scan on the branch: nothing in scope should still be flagged. Run the client's own tests and linters if they exist.

### 6. Build the test set

- Turn the client's real examples (personal details removed) into `WORK/compare/test_set.jsonl`. Format: `KIT/templates/test_set_template.jsonl`. Aim for 20–50 cases per feature, including hard ones.
- Add checks where they are clear: `must_include`, `must_not_include`, `expect_json`, `max_chars`. Put notes for the grader in `expected`.
- If the client has no examples, write clearly labelled synthetic cases and say so in the report.

### 7. Compare old and new

- Copy `KIT/templates/runner_config_template.json` to `WORK/compare/runner_old.json` and `runner_new.json`. Set `name`, `model`, `params`, prompts (per feature in `features` if needed), prices from the provider's pricing page (confirmed by the user) and `api_key_env`. Remove the `_help` notes.
- Runner: copy `client_api_run` from `KIT/scripts/runners.py` into `WORK/compare/client_runner.py` (add `import os` and `from runners import RunnerSetupError`), fill in the marked block, and set `"runner": "client_runner.py:client_api_run"`. Prefer calling the client's own function (example C in the stub) so the real code path is tested. Never edit the kit's copy for a client.
- Check the setup with `"runner": "mock"` first if useful, then:

```sh
/tmp/mr-venv/bin/python ${CLAUDE_PROJECT_DIR}/kits/model-retirement/scripts/compare_runs.py --tests WORK/compare/test_set.jsonl \
  --old WORK/compare/runner_old.json --new WORK/compare/runner_new.json \
  --out WORK/compare/comparison.xlsx --dry-run
```

- If the dry run prints a PROBLEM or WARNING (the template's model, prices of 0, both sides the same), fix the configs first.
- Real run: only with the user's OK (rule 4), with the client's staging key set in the environment, while the old model still works. Add `--yes`; start with `--limit 3`.
- Read the results: errors (often a rejected parameter), failed checks, big length or token changes, low similarity. Summarize them for the user with case IDs.

### 8. Re-tune the prompts

- Change the new prompt or settings in `runner_new.json` and make the same change on the code branch. Re-run. Two or three rounds is normal. Keep a short log of each change and why; it goes in the report.

### 9. Grading

- The client's reviewer grades each case in the yellow columns of `comparison.xlsx` (Preferred: old/new/same; New OK?: yes/no), or in a CSV (`id,preferred,new_ok,notes`). Don't grade on the client's behalf. You may suggest grades, clearly labelled as suggestions.
- To merge a grades CSV, re-build the workbook from the saved answers with `--from-raw`. It calls no model and costs nothing. Use the same test set and runner configs as the graded run:

```sh
/tmp/mr-venv/bin/python ${CLAUDE_PROJECT_DIR}/kits/model-retirement/scripts/compare_runs.py --tests WORK/compare/test_set.jsonl \
  --old WORK/compare/runner_old.json --new WORK/compare/runner_new.json \
  --from-raw WORK/compare/comparison_raw.jsonl --grades WORK/compare/grades.csv --out WORK/compare/comparison_graded.xlsx
```

- Never re-run with the client runner and `--yes` just to add grades. That calls the paid API again, makes new answers, puts the grades next to answers the reviewer never saw, and overwrites `comparison_raw.jsonl`.

### 10. Report and handover

- Copy `KIT/templates/client_report_template.md` to `WORK/report.md` and fill it from `model_scan.md`, the Summary sheet, the branch diff, the prompt log and the grades. Plain English, short sentences, numbers checked against the workbook.
- Convert it: `/tmp/mr-venv/bin/python ${CLAUDE_PROJECT_DIR}/kits/model-retirement/scripts/md_to_docx.py WORK/report.md WORK/report.docx --footer "Prepared for <client>"`
- Handover list: pull request link, `report.docx`, `comparison.xlsx` (or `comparison_graded.xlsx`), `model_scan.md`, the test set, the re-run command, release and rollback steps, and the next retirement dates from the scan.

## Emergency path: the date has already passed

1. Confirm the cause in the client's logs (for example "model not found" or "deprecated" errors).
2. Make the smallest safe fix on a branch: the replacement model and any parameters it rejects. The client releases it through their normal process, with written approval.
3. Test after the fix. If old answers exist in logs, save them as JSONL (`id`, `output`) and compare with `"runner": "recorded"` and `"recorded_outputs": "<file>"`.
4. In the report, state what could and could not be tested, and that the provider's retirement caused the outage. Suggest the urgent rate from the price guide.

## Scan statuses

RETIRED (date passed) · RETIRING SOON (within 90 days) · SCHEDULED (later) · LISTED (NO DATE) · CHECK VALUE (name comes from a variable or setting the scan could not resolve; find the real value) · NOT IN LIST (no entry in the list; this does not prove the model is safe).
