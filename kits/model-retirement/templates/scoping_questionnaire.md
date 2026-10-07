# Scoping questions: AI model update

*Send this before you quote. Most answers take one line. If they don't know an answer, that's fine: write "not sure" and we'll find out together.*

```text
Hi [name],

To give you a fixed price for keeping your AI features working, I need a few answers.
"Not sure" is a fine answer.

About the features
1. Which features in your product use AI? (for example: chat widget, email drafts, summaries, search)
2. For each one: roughly how many requests a month, and how bad would it be if it stopped for a day?
3. Have you had an email from an AI provider about a model being "deprecated", "retired" or
   "shut down"? If yes, please forward it.

About the code and the setup
4. Where is the code? (GitHub, GitLab, a no-code tool such as Bubble or FlutterFlow, a WordPress plugin, other)
5. Can you give me read access to the repository, and later let me open a pull request on a new branch?
6. Which AI providers do you use, and through what? (directly, or through Azure, AWS Bedrock,
   Google Cloud, OpenRouter, a no-code plugin or similar)
7. Do you have a staging or test environment separate from production?
8. Where are your settings stored? (.env files, hosting dashboard, secrets manager, database)
9. Have you fine-tuned any models, or do you store embeddings (vectors) for search?

About testing
10. Can you share 20 to 50 real examples of what goes into each feature, with names, emails and
    other personal details removed? (I'll use them only to test your feature, and give them back to you.)
11. What does a good answer look like? Who on your side can judge the answers? (about 1 hour of their time)
12. Can you create an API key for staging only, with a spending limit, for these tests?

About timing and release
13. Is there a deadline you know of? (for example the provider's retirement date or a launch)
14. Who reviews and releases code changes on your side?
15. Anything I must not touch? (production database, customer data, certain files)

Thanks! I'll reply with a fixed price and a timeline within [24 hours].
[Your name]
```

## What each answer tells you

- **Q1–2:** the number of features sets the price. High traffic or high risk means more test cases.
- **Q3:** the email usually names the model and the date. Still check the provider's official page.
- **Q4–5:** no repository access means you can't scan. No-code tools need a different approach (check each AI step by hand).
- **Q6:** cloud platforms (Azure, Bedrock, Google Cloud) set their own retirement dates. They can differ from the provider's.
- **Q7:** no staging environment? Quote extra time to set one up, or test with a separate key against copies of the inputs. Never test in production.
- **Q8:** model names in a dashboard or database won't show up in a code scan. Ask for those values.
- **Q9:** fine-tuned models and embeddings are bigger jobs. A new embedding model means re-processing every stored document. Quote them separately.
- **Q10–11:** without real examples and a judge, you can't prove the new model is as good. This is the core of the service.
- **Q12:** tests run on the client's key and the client's bill, never on your own subscription.
- **Q13:** if the date has already passed, it's an emergency fix. See "Post-deadline emergencies" in the README.
