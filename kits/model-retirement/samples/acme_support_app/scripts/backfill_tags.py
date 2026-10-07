"""One-off script from 2023 that re-tagged old tickets. Nobody runs it any more.

FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
"""
import openai  # old SDK style (before version 1.0)


def retag(ticket_text):
    result = openai.ChatCompletion.create(
        model="old-model-v0",
        messages=[{"role": "user", "content": "Tag this ticket: " + ticket_text}],
        temperature=1.0,
    )
    return result["choices"][0]["message"]["content"]
