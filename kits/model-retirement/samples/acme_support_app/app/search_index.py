"""Build the search index of help articles that the reply drafter uses.

FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
"""
from openai import OpenAI

from app.config import EMBEDDING_MODEL

client = OpenAI()


def embed_articles(articles: list[str]) -> list[list[float]]:
    result = client.embeddings.create(model=EMBEDDING_MODEL, input=articles)
    return [item.embedding for item in result.data]
