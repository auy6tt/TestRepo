# Model reference scan: acme_support_app

- **Scan date:** 2026-10-07 (warning window: 90 days)
- **Retirement list:** `sample_retirements.csv` (4 model IDs)
- **Files scanned:** 10
- **References found:** 12 in 9 files
- **By status:** RETIRED: 1, RETIRING SOON: 5, SCHEDULED: 5, NOT IN LIST: 1

> This scan is a helper, not a guarantee. Read the code around every hit, and ask the client about model names set in hosting dashboards, databases or other repos.

## 1. Needs action now

Already retired, or retiring within 90 days.

| Status | Where | Model | Retires | Time left | Replacement | Parameters |
|---|---|---|---|---|---|---|
| **RETIRED** | `scripts/backfill_tags.py:10` | `old-model-v0` | 2026-03-31 | retired 190 days ago | `new-model-v2` | temperature=1.0 |
| **RETIRING SOON** | `.env.example:5` | `old-model-v1` | 2026-12-01 | 55 days | `new-model-v2` | - |
| **RETIRING SOON** | `app/summarize_ticket.py:18` | `old-model-v1` | 2026-12-01 | 55 days | `new-model-v2` | temperature=0.3, max_tokens=300 |
| **RETIRING SOON** | `config/settings.yaml:5` | `old-model-v1` | 2026-12-01 | 55 days | `new-model-v2` | temperature=0.3, max_tokens=300 |
| **RETIRING SOON** | `web/src/replyDraft.ts:7` | `old-model-v1` | 2026-12-01 | 55 days | `new-model-v2` | - |
| **RETIRING SOON** | `web/src/replyDraft.ts:11` | `REPLY_MODEL` = old-model-v1 (web/src/replyDraft.ts:7) | 2026-12-01 | 55 days | `new-model-v2` | temperature=0.7, top_p=0.95, max_tokens=400 |

## 2. Everything else to check

SCHEDULED = retires later. CHECK VALUE = the model name comes from a variable or setting the scan could not resolve. NOT IN LIST = no retirement entry; check the provider's page, because a missing entry does not prove the model is safe.

| Status | Where | Model | Retires | How it is set | Call type |
|---|---|---|---|---|---|
| SCHEDULED | `.env.example:4` | `old-small-v1` | 2027-01-15 | env file | Environment file |
| SCHEDULED | `app/classify_ticket.py:16` | `CLASSIFIER_MODEL` = old-small-v1 (.env.example:4); old-small-v1 (app/config.py:9) | 2027-01-15 | variable | Messages API call (Anthropic-style SDK) |
| SCHEDULED | `app/config.py:9` | `old-small-v1` | 2027-01-15 | env var + default in code | Environment variable read |
| SCHEDULED | `app/config.py:12` | `old-embed-v1` | 2027-04-30 | hard-coded | Constant or variable |
| SCHEDULED | `app/search_index.py:13` | `EMBEDDING_MODEL` = old-embed-v1 (app/config.py:12) | 2027-04-30 | variable | Embeddings call |
| NOT IN LIST | `web/src/chatWidget.js:9` | `partner-chat-model-x` | - | hard-coded | Vercel AI SDK call |

## 3. All references

| # | Status | File | Line | Model | How it is set | Call type | Parameters | Confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | RETIRED | `scripts/backfill_tags.py` | 10 | `old-model-v0` | hard-coded | Legacy ChatCompletion call (OpenAI SDK before v1) | temperature=1.0 | high |
| 2 | RETIRING SOON | `.env.example` | 5 | `old-model-v1` | env file | Environment file | - | high |
| 3 | RETIRING SOON | `app/summarize_ticket.py` | 18 | `old-model-v1` | hard-coded | Chat Completions call (OpenAI-style SDK) | temperature=0.3, max_tokens=300 | high |
| 4 | RETIRING SOON | `config/settings.yaml` | 5 | `old-model-v1` | config file | Config file | temperature=0.3, max_tokens=300 | high |
| 5 | RETIRING SOON | `web/src/replyDraft.ts` | 7 | `old-model-v1` | env var + default in code | Environment variable read | - | high |
| 6 | RETIRING SOON | `web/src/replyDraft.ts` | 11 | `REPLY_MODEL` = old-model-v1 (web/src/replyDraft.ts:7) | variable | Chat Completions call (OpenAI-style SDK) | temperature=0.7, top_p=0.95, max_tokens=400 | high |
| 7 | SCHEDULED | `.env.example` | 4 | `old-small-v1` | env file | Environment file | - | high |
| 8 | SCHEDULED | `app/classify_ticket.py` | 16 | `CLASSIFIER_MODEL` = old-small-v1 (.env.example:4); old-small-v1 (app/config.py:9) | variable | Messages API call (Anthropic-style SDK) | max_tokens=10, temperature=0.0 | high |
| 9 | SCHEDULED | `app/config.py` | 9 | `old-small-v1` | env var + default in code | Environment variable read | - | high |
| 10 | SCHEDULED | `app/config.py` | 12 | `old-embed-v1` | hard-coded | Constant or variable | - | high |
| 11 | SCHEDULED | `app/search_index.py` | 13 | `EMBEDDING_MODEL` = old-embed-v1 (app/config.py:12) | variable | Embeddings call | - | high |
| 12 | NOT IN LIST | `web/src/chatWidget.js` | 9 | `partner-chat-model-x` | hard-coded | Vercel AI SDK call | temperature=0.5, maxTokens=256 | high |

## 4. Environment variables to confirm with the client

These model names are read from environment variables. Ask the client for the real values in staging and production (hosting dashboard, secrets manager, CI settings).

| Variable | Read in | Default in code | Value in an env file in the repo |
|---|---|---|---|
| `CLASSIFIER_MODEL` | `app/config.py:9` | `old-small-v1` | `old-small-v1` in `.env.example` |
| `REPLY_MODEL` | `web/src/replyDraft.ts:7` | `old-model-v1` | `old-model-v1` in `.env.example` |

## 5. Low-confidence matches (probably not AI models)

None.

## Next steps

1. Open every row in sections 1 and 2 and confirm it is a real model call.
2. Confirm each retirement date and replacement on the provider's official page (the `source_url` column in the CSV). Note the date you checked.
3. Ask the client for the values of the environment variables in section 4.
4. Search for anything the scan cannot see: model names stored in a database, set in a no-code tool or hosting dashboard, or used in other repos and scheduled jobs.
5. Note the parameters next to each call. New models may reject some of them or need different values.
