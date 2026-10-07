# AI model update report: Acme support helper

**Prepared for:** Acme Home Goods · **Prepared by:** [Your name] · **Date:** 2026-10-09 · **Version:** 1.0

> FICTIONAL SAMPLE for a portfolio. Acme Home Goods is not a real company. The model names, providers, dates, prices and results are made up, and the answers come from a simulated (mock) run.

<!-- Put your name in "Prepared by" above and at the end, then rebuild the Word file:
python ../scripts/md_to_docx.py sample_report.md sample_report.docx --footer "Fictional sample report" -->

## 1. Summary

Your ticket summarizer and reply drafter both use old-model-v1, which Provider A retires on 1 December 2026. After that date both features would stop working. We moved them to new-model-v2, adjusted both prompts, and compared old and new answers on 10 real examples. The new version is ready to release from the branch `model-update-2026-10`.

| | Before | After |
|---|---|---|
| Model | old-model-v1 | new-model-v2 |
| Retirement date | 1 December 2026 | none announced |
| Automatic checks passed | 9 of 10 | 10 of 10 |
| Typical response time | 1.9 seconds | 1.1 seconds |
| Estimated cost per 1,000 requests | $0.26 | $0.24 |

**Human review:** the new answer was as good as or better than the old one in 9 of 10 cases, and acceptable in 10 of 10.

**What you need to do:** review and merge pull request #42 before 20 November, change one hosting setting (`REPLY_MODEL`), then release. Section 7 has the steps.

## 2. Scope

- **Included:** the ticket summarizer (`app/summarize_ticket.py`) and the reply drafter (`web/src/replyDraft.ts`), both on old-model-v1. Also the unused 2023 script `scripts/backfill_tags.py`, deleted with your agreement.
- **Not included:** the ticket classifier, the help-article search index and the website chat widget. Their models retire later or have no date. See section 8.
- **Where we worked:** branch `model-update-2026-10` in the `acme-support-helper` repository. Tests ran in staging with your staging API key. Nothing was changed in production.

## 3. What we found

We scanned 10 files and found 12 places where an AI model is chosen. 6 of them use a model that is already retired or retires within 90 days.

| Where | Model | Retires | What we did |
|---|---|---|---|
| `app/summarize_ticket.py` line 18 | old-model-v1 | 1 Dec 2026 | Moved to new-model-v2 |
| `web/src/replyDraft.ts` line 7 (default for `REPLY_MODEL`) | old-model-v1 | 1 Dec 2026 | Moved to new-model-v2 |
| `REPLY_MODEL` in `.env.example` and in your hosting settings | old-model-v1 | 1 Dec 2026 | Updated the example. **You change the hosting setting** (section 7) |
| `config/settings.yaml` line 5 | old-model-v1 | 1 Dec 2026 | Removed. The code never read this setting |
| `scripts/backfill_tags.py` line 10 | old-model-v0 | Already retired (31 Mar 2026) | Deleted. Unused since 2023 |
| `app/classify_ticket.py` (via `CLASSIFIER_MODEL`) | old-small-v1 | 15 Jan 2027 | Not in scope, see section 8 |
| `app/search_index.py` (via `EMBEDDING_MODEL`) | old-embed-v1 | 30 Apr 2027 | Not in scope, see section 8 |
| `web/src/chatWidget.js` line 9 | partner-chat-model-x | None announced | No change. Check again in January |

The retirement dates come from Provider A's and Provider B's official deprecations pages, checked on 7 October 2026. Providers sometimes move dates, so we will check again on 1 November.

## 4. What we changed

| File | Before | After | Why |
|---|---|---|---|
| `app/summarize_ticket.py` | old-model-v1, typed into the code | new-model-v2, read from `SUMMARY_MODEL` in `app/config.py` | The old model retires. The model name now lives in one place |
| `app/summarize_ticket.py` | One-line prompt | Prompt with three rules (below) | The new model added greetings and bullet points |
| `web/src/replyDraft.ts` | Default old-model-v1, with `top_p` 0.95 | Default new-model-v2, no `top_p` | The old model retires. The new model rejects `temperature` and `top_p` together |
| `web/src/replyDraft.ts` | Prompt | Prompt with a word limit and a fixed sign-off | Shorter replies, and no promises the policy does not make |
| `config/settings.yaml` | Model setting old-model-v1 | Setting removed | The code never read it |
| `scripts/backfill_tags.py` | Whole file | Deleted | Unused, and its model is already retired |
| `.env.example` | `REPLY_MODEL` = old-model-v1 | `REPLY_MODEL` = new-model-v2 | Matches the new default |

**Prompt changes:** in a first trial run with the old prompts, the new model started 4 of 6 summaries with a greeting, used bullet points, and once left out the order number. The summarizer prompt now asks for 2 or 3 plain sentences with no greeting or bullet points, tells it to copy the order number exactly, and asks for any date the customer mentions. The reply prompt now limits replies to 120 words, rules out promising delivery dates, and fixes the sign-off.

**Settings changes:** removed `top_p` from the reply drafter, because new-model-v2 does not accept it together with `temperature`. Temperature is unchanged: 0.3 for summaries, 0.7 for replies.

## 5. Test results

- **Test set:** 10 examples (6 summaries, 4 replies) based on September tickets, with names, emails and addresses changed. It comes with this report, so you can re-use it for the next model change.
- **Method:** each example went through the old setup (old-model-v1, current prompts) and the new setup (new-model-v2, new prompts) with the same input. Your support lead read every pair and graded it.

| Result | Count |
|---|---|
| New answer better | 3 |
| About the same | 6 |
| Old answer better, new still acceptable | 1 |
| New answer not acceptable | 0 |

**What we noticed:**

- New summaries are 14% shorter (162 characters on average, down from 188) and always include the order number. The old model left it out once (case S04).
- One new summary (case S05) left out the date the return arrived. Your support lead judged it still usable.
- New replies are 17% shorter and no longer promise delivery dates that the delivery policy does not cover (case R01).
- Neither model invented an order number when the customer had none (case S06).

The full side-by-side results are in `comparison.xlsx`.

## 6. Cost and speed

| | Before | After | Change |
|---|---|---|---|
| Typical response time (median) | 1.9 s | 1.1 s | -42% |
| Tokens per request (input / output) | 94 / 55 | 142 / 52 | +52% / -6% |
| Estimated cost per 1,000 requests | $0.26 | $0.24 | -8% |

Input tokens went up for two reasons: the new prompts are longer, and new-model-v2 counts about 11% more tokens for the same text. Its lower prices more than make up for it. At about 12,000 requests a month (6,000 tickets, two features each), the cost stays at roughly $3 a month, so cost is not a concern at your volume. Prices come from the providers' pricing pages on 7 October 2026.

## 7. Release and rollback

1. Review and merge pull request #42 (branch `model-update-2026-10`) into `main`.
2. **Change the hosting setting `REPLY_MODEL` from old-model-v1 to new-model-v2**, in staging and in production. The new default in the code is not enough, because the hosting setting overrides it.
3. Deploy to staging and try 3 real tickets in both the summarizer and the reply drafter.
4. Release to production on a quiet morning, by 20 November, to leave a buffer before the deadline.
5. Watch the error logs and your agents' feedback for 7 days.
6. **Rollback:** revert the merge and set `REPLY_MODEL` back to old-model-v1. This only works until 1 December 2026. After that, the old model no longer answers.

## 8. Risks and recommendations

- **Ticket classifier:** `app/classify_ticket.py` uses old-small-v1 from Provider B, which retires on 15 January 2027. Move it by mid-December in the same way. We can quote this separately.
- **Help-article search:** `app/search_index.py` uses old-embed-v1, which retires on 30 April 2027. A new embedding model means re-processing every stored help article and re-testing search quality. Plan it as its own small project in the first quarter.
- **Website chat widget:** uses partner-chat-model-x. No retirement is announced yet. Check again in January.
- **Hosting settings:** `CLASSIFIER_MODEL` is also set in your hosting settings. You confirmed that production uses old-small-v1.
- **Reminders:** put a reminder in the calendar 90 days before each date above. The scan and this test set can be re-run in minutes.

## 9. Handover

- **Code changes:** pull request #42, branch `model-update-2026-10`
- **Test set:** `test_set.jsonl`, 10 examples
- **How to re-run the comparison:** `python compare_runs.py --tests test_set.jsonl --old runner_old.json --new runner_new.json --out comparison.xlsx`
- **Full scan of model references:** `model_scan.md` (attached)
- **Questions:** [Your name], [your email]
