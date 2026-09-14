"""Tier 2: LLM classification + aspect sentiment, in ONE structured call.

Combining the two halves token cost — document that as a deliberate decision.

Cost levers, all three worth using and worth saying you used:
  - Batch API: 50% off, and nothing here is latency-sensitive.
  - Prompt caching on the taxonomy rubric (fixed ~1.5k-token prefix on every call).
    Verify it is working via usage.cache_read_input_tokens; if that is zero across
    repeated calls, something is invalidating the prefix.
  - Haiku for the bulk pass, Sonnet only for the ambiguous band and for
    transcript/filing passages where context matters.

Every call goes through utils.tokenlog.logged().
"""
from __future__ import annotations
import pandas as pd


def build_prompt(doc: dict, company: str) -> list[dict]:
    """Rubric (cached prefix) + document (volatile suffix). Order matters for caching."""
    raise NotImplementedError


def classify_batch(docs: pd.DataFrame, model: str, task: str) -> pd.DataFrame:
    """Submit as a Batch API job; poll; key results by custom_id, never by position.

    Returns: ai_relevance, ai_role, materiality, valence_ai, confidence, evidence_span.
    """
    raise NotImplementedError


def classify_cascade(docs: pd.DataFrame) -> pd.DataFrame:
    """Haiku over everything, then Sonnet over the ambiguous band. Adds `model_used`."""
    raise NotImplementedError
