"""Settings for the Acme Home Goods support helper.

FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
Acme Home Goods is not a real company, and every model name here is a placeholder.
"""
import os

# Small, fast model that tags new tickets.
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "old-small-v1")

# Embedding model for the help-article search index.
EMBEDDING_MODEL = "old-embed-v1"
