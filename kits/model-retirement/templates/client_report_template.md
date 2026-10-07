# AI model update report: [FEATURE OR APP NAME]

**Prepared for:** [CLIENT NAME] · **Prepared by:** [YOUR NAME], [YOUR EMAIL] · **Date:** [YYYY-MM-DD] · **Version:** 1.0

<!--
HOW TO USE THIS TEMPLATE (text inside these comment markers does not appear in the Word file)
1. Copy this file into the client's work folder as report.md.
2. Replace everything in [SQUARE BRACKETS]. Delete rows and sections you do not need.
3. Take the numbers from comparison.xlsx (Summary sheet) and the findings from model_scan.md.
4. Write for a busy owner: short sentences, no jargon. Explain any technical word you must use.
5. Convert it: python scripts/md_to_docx.py report.md report.docx --footer "Prepared for [CLIENT NAME]"
6. Open the .docx, read it once more, then send it (or export it as PDF).
-->

## 1. Summary

[Two to four sentences. Example: Your [FEATURE] used [OLD MODEL], which [PROVIDER] retires on [DATE]. After that date the feature would stop working. We moved it to [NEW MODEL], adjusted the prompt, and compared old and new answers on [N] real examples. The new version was as good or better in [X] of [N] cases and is ready to release.]

| | Before | After |
|---|---|---|
| Model | [OLD MODEL] | [NEW MODEL] |
| Retirement date | [DATE] | [DATE, or "none announced"] |
| Automatic checks passed | [X of N] | [Y of N] |
| Typical response time | [X.X seconds] | [Y.Y seconds] |
| Estimated cost per 1,000 requests | [$X.XX] | [$Y.YY] |

**Human review:** the new answer was as good as or better than the old one in [X] of [N] cases, and acceptable in [Y] of [N].

**What you need to do:** [Example: review and merge pull request [NUMBER] before [DATE], then release it. Section 7 has the release and rollback steps.]

## 2. Scope

- **Included:** [features and files, for example the ticket summarizer]
- **Not included:** [for example embeddings, fine-tuned models, other apps]
- **Where we worked:** branch `[BRANCH NAME]` in [REPOSITORY]. Tests ran in [STAGING] with your own API key. Nothing was changed in production.

## 3. What we found

We scanned [N] files and found [N] places where an AI model is chosen. [N] of them use a model that is already retired or retires within 90 days.

| Where | Model | Retires | What we did |
|---|---|---|---|
| [file:line] | [OLD MODEL] | [DATE] | [Moved to NEW MODEL] |
| [file:line] | [MODEL] | [DATE] | [Not in scope, see section 8] |

The retirement dates come from [PROVIDER]'s official deprecations page ([LINK]), checked on [DATE]. Providers sometimes move dates, so check again a month before the deadline.

## 4. What we changed

| File | Before | After | Why |
|---|---|---|---|
| [file] | `[OLD MODEL]` | `[NEW MODEL]` | The old model retires on [DATE] |
| [file] | [old setting] | [new setting] | [Example: the new model does not accept this setting] |

**Prompt changes:** [What changed and why. Example: the new model added greetings and bullet points, so the instructions now ask for plain sentences.]

**Settings changes:** [Example: removed top_p because the new model does not accept it together with temperature.]

## 5. Test results

- **Test set:** [N] examples from [SOURCE, for example real tickets from last month], with names and personal details removed. You keep this test set for the next model change.
- **Method:** each example went through the old setup and the new setup with the same input. [NAME, ROLE] read every pair and graded it.

| Result | Count |
|---|---|
| New answer better | [N] |
| About the same | [N] |
| Old answer better, new still acceptable | [N] |
| New answer not acceptable | [N] |

**What we noticed:**

- [Example: new answers are 15% shorter and always include the order number.]
- [Example: in one case the new answer left out a date. We judged it still acceptable.]

The full side-by-side results are in `comparison.xlsx`.

## 6. Cost and speed

| | Before | After | Change |
|---|---|---|---|
| Typical response time | [X.X s] | [Y.Y s] | [-Z%] |
| Tokens per request (input / output) | [X / Y] | [X / Y] | [+Z% / -Z%] |
| Estimated cost per 1,000 requests | [$X.XX] | [$Y.YY] | [-Z%] |

[One or two sentences on the monthly bill. Example: at about [N] requests a month, this is roughly $[X] a month, [up/down] from $[Y].] Prices come from [PROVIDER]'s pricing page on [DATE]. Newer models can count tokens differently, so compare the real bill after release.

## 7. Release and rollback

1. Review and merge [PULL REQUEST OR BRANCH] into [MAIN BRANCH].
2. Deploy to staging and try [3-5] real requests in each changed feature.
3. Release to production at a quiet time.
4. Watch [error logs, customer complaints, agent feedback] for [7] days.
5. **Rollback:** [revert the merge, or set the model setting back to OLD MODEL]. This only works until [RETIREMENT DATE]. After that, the old model no longer answers.

## 8. Risks and recommendations

- [Other models that retire later. Example: the ticket classifier uses [MODEL], which retires on [DATE]. It can be moved the same way.]
- [Embeddings: a new embedding model means re-processing every stored document. Plan it as its own project.]
- [Put a reminder in the calendar 90 days before the next retirement date. The scan and the test set can be re-run each time.]
- [Anything you could not test, and why.]

## 9. Handover

- **Code changes:** [PULL REQUEST LINK OR BRANCH]
- **Test set:** `[PATH]`, [N] examples. Re-use it for the next model change.
- **How to re-run the comparison:** `[COMMAND]`
- **Full scan of model references:** `model_scan.md` (attached)
- **Questions:** [YOUR NAME], [YOUR EMAIL]
