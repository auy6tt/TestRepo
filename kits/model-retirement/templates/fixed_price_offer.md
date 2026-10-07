# Fixed-price offer: AI model update

*Send after the scoping answers. Replace everything in [brackets]. Keep it short.*

```text
Hi [name],

Thanks for the answers. Here's my fixed-price offer.

The problem
Your [feature] uses [old model], which [provider] retires on [date]. After that date,
requests to it fail and the feature stops working. [Number] other places in your code
use models that retire later; I've listed them so you can plan.

What I'll do
1. Find every place your code uses the old model, including settings and environment variables.
2. Move [feature(s)] to [new model] on a separate branch, and adjust the prompts and settings
   the new model needs.
3. Run old and new side by side on [30] of your real examples (personal details removed),
   in staging, with your own API key, while the old model still works.
4. Send you a short report: what changed, before/after results, cost and speed,
   and how to release and roll back. You keep the test set for the next model change.

Price: $[amount] fixed. 50% to start, 50% when you receive the report and the pull request.
Timeline: [5] working days from repository access and the examples.
Not included: releasing to production, embeddings or fine-tuned models, other apps.
I can quote those separately.

I never need your production passwords. API keys stay in your environment variables.

[Your name]
```

## Price guide

| Job | Price |
|---|---|
| One feature (one prompt, one model call) | $300–800 |
| Whole app, several features, with a reusable test set | $1,500–4,000 |
| Already broken (date has passed), same-week fix | add 50% for urgent work |

## Short version for a gig listing or a post

```text
Is your AI feature about to stop working? AI providers retire old models on fixed dates,
and after that, calls fail. I find every model your code uses, move you to the successor,
and prove it still works with a side-by-side test on your real examples, before the deadline.
Fixed price from $300 per feature. You get a before/after report and a reusable test set.
```
