"""Tier 1: local embeddings. Zero API cost, CPU, no Anthropic embeddings endpoint.

Two jobs:
  (a) recall AI-relevant documents the lexicon missed;
  (b) rank documents by AI-likelihood so the LLM budget goes to the AMBIGUOUS
      MIDDLE BAND rather than being spent uniformly on obvious positives and
      obvious negatives.

(b) is the token-efficiency argument the brief asks you to defend.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ANCHORS = {
    "substantive_positive": [
        "company reports AI-driven revenue growth",
        "demand for AI infrastructure lifts orders",
    ],
    "substantive_negative": [
        "generative AI threatens the company's core product",
        "customers cut software budgets to fund AI spending",
    ],
    "buzzword": [
        "company mentions AI in passing at an industry conference",
        "press release boilerplate referencing artificial intelligence",
    ],
}


def embed(texts: list[str], model: str = "BAAI/bge-small-en-v1.5") -> np.ndarray:
    raise NotImplementedError


def score_against_anchors(docs: pd.DataFrame) -> pd.DataFrame:
    """Cosine similarity to each anchor class. Adds ai_likelihood in [0, 1]."""
    raise NotImplementedError
