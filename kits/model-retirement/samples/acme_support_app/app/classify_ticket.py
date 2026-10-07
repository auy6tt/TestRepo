"""Tag each new ticket with one category.

FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
"""
import anthropic

from app.config import CLASSIFIER_MODEL

client = anthropic.Anthropic()  # reads the API key from the environment

CATEGORIES = ["delivery", "damaged item", "refund", "account", "other"]


def classify_ticket(ticket_text: str) -> str:
    message = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=10,
        temperature=0.0,
        system="Reply with exactly one category from this list: " + ", ".join(CATEGORIES),
        messages=[{"role": "user", "content": ticket_text}],
    )
    label = message.content[0].text.strip().lower()
    return label if label in CATEGORIES else "other"
