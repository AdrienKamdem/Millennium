"""Earnings-call transcripts. Highest-value text in the corpus.

Management's AI framing plus the analyst Q&A where AI revenue claims get
pressure-tested. Route decided in config/sources.yaml; do not let scraping eat an
evening — timebox it.

Beyond text volume, transcripts give the cleanest salience measure available:
AI-mentioning sentences / total sentences on a call. Call length is roughly
constant across companies and quarters, so it is volume-normalised by construction
and needs no shrinkage, no share-of-coverage normalisation and no dedup. Use it as
the INDEPENDENT robustness check on news-derived salience — agreement validates
the index, divergence is a finding.
"""
from __future__ import annotations
import pandas as pd


def fetch(ticker: str, year: int, quarter: int) -> dict | None:
    """One transcript: speaker-tagged prepared remarks + Q&A."""
    raise NotImplementedError


def to_passages(transcript: dict) -> pd.DataFrame:
    """Split into passages. Tag section (prepared|qa) and speaker role (mgmt|analyst).

    Keep the section tag: prepared remarks are marketing, Q&A is adversarial.
    Reporting salience separately for the two is cheap and more honest than pooling.
    """
    raise NotImplementedError


def ai_mention_density(passages: pd.DataFrame) -> float:
    """AI-mentioning sentences / total sentences. The volume-normalised salience proxy."""
    raise NotImplementedError
