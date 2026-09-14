"""Tier 0: free lexicon prefilter. Tags candidates; never decides.

Every document stays in the DENOMINATOR — salience is a share of total coverage,
so dropping non-AI docs here would silently inflate every score.

The 'AI' substring trap: match on word boundaries (\\bAI\\b, A\\.I\\.) or you will
hit Air, AIG, Dubai, Shanghai, Mumbai.
"""
from __future__ import annotations
import pandas as pd

AI_TERMS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "large language model", "LLM", "generative AI", "foundation model", "transformer",
    "copilot", "chatbot", "agentic", "inference", "training cluster",
    "GPU", "accelerator", "NPU", "TPU", "HBM", "datacenter GPU",
]


def flag(docs: pd.DataFrame, text_col: str = "title") -> pd.DataFrame:
    """Add `lexicon_hit` (bool) and `lexicon_terms` (list). Does not filter."""
    raise NotImplementedError
