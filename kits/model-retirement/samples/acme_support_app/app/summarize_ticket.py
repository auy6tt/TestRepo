"""Summarize a customer support ticket for the agent who picks it up.

FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
"""
from openai import OpenAI

client = OpenAI()  # reads the API key from the environment

SYSTEM_PROMPT = (
    "You summarize customer support tickets for Acme Home Goods agents. "
    "Write 2-3 sentences. Include the order number, the problem, "
    "and what the customer wants."
)


def summarize_ticket(ticket_text: str) -> str:
    response = client.chat.completions.create(
        model="old-model-v1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ticket_text},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content
