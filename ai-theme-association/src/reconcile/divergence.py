"""Divergence analysis. The core judgment test.

Text measures what is SAID. Beta measures what is PAID FOR. Every gap is one of
three things, and the deliverable is saying which:

  1. MISPRICING        — real AI exposure the market has not priced (or over-priced).
  2. MISSING CHANNEL   — exposure is real and priced, but travels through text the
                         corpus never saw.
  3. MEASUREMENT       — the classifier, corpus, or factor is broken.

Each divergence needs a SPECIFIC, FALSIFIABLE test, not a story. Candidate
hypotheses below are priors from the design phase — CHECK RESULTS AGAINST THEM,
do not fit to them, and drop any the data does not support.

  CAT  (high beta, low semantic) -> missing channel? AI demand via data-centre
       power / backup generation, discussed in industrial trade press and in the
       Energy & Transportation segment, not in AI-tagged news.
       TEST: add VRT/ETN/GEV to CAT's regression; if delta collapses, confirmed.

  ADBE (high salience, negative valence, weak beta) -> the market prices Adobe as
       an AI loser. TEST: show unsigned salience mis-ranks ADBE and S*V fixes it.
       This case is what validates the multiplicative index design.

  INTC (loud narrative, weak beta) -> narrative is aspirational, not revenue-
       realised. TEST: does delta rise after actual accelerator-revenue disclosure?
"""
from __future__ import annotations
import pandas as pd


def largest_gaps(aligned: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    raise NotImplementedError


def test_cat_power_channel(returns: pd.DataFrame, factors: pd.DataFrame) -> dict:
    """Add VRT/ETN/GEV to CAT's regression; report whether the AI beta survives."""
    raise NotImplementedError


def test_signed_vs_unsigned(aia: pd.DataFrame, betas: pd.DataFrame) -> dict:
    """Rank correlation using salience alone vs salience*valence. Does signing help?"""
    raise NotImplementedError
