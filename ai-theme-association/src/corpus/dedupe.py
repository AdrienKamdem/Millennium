"""Deduplication. The brief asks for this logic explicitly — write it down.

1. Canonicalise URLs (strip UTM/query params, resolve redirects).
2. Exact hash on canonical URL.
3. Near-duplicate titles: normalise, TF-IDF cosine > 0.90 within a +/-3 day window.
4. Cross-source: an IR release and the news report OF that release are DIFFERENT
   documents (primary vs secondary). Keep both, tag them, weight them differently.

One wire story republished by 12 outlets collapses to one document — but retain
n_republications rather than discarding it. Republication count is itself a
salience signal.
"""
from __future__ import annotations
import pandas as pd


def canonicalise_url(url: str) -> str:
    raise NotImplementedError


def dedupe(docs: pd.DataFrame, threshold: float = 0.90, window_days: int = 3) -> pd.DataFrame:
    """Returns the deduped frame with an added n_republications column."""
    raise NotImplementedError
