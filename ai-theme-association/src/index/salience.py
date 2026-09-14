"""Salience: what SHARE of a company's coverage is genuinely about AI.

    S_ct = sum_d [w_d * m_d * 1(substantive)] / sum_d w_d

A share, not a count — so a company covered more heavily because it is larger does
not register as more AI-associated. This is the direct answer to the brief's
volume-control requirement.

Then shrink. Thin months produce wildly noisy shares (1 AI article out of 3 is not
33% salience), and the smaller names are thin most months:

    lambda = n / (n + k),  S_shrunk = lambda*S + (1-lambda)*S_trailing_mean

Justify k by showing month-over-month variance of raw vs shrunk. This is the
technically correct fix for the coverage bias documented in Task 1 — say so.
"""
from __future__ import annotations
import pandas as pd


def raw_salience(classified: pd.DataFrame) -> pd.DataFrame:
    """Per company per period. Weighted by source and materiality."""
    raise NotImplementedError


def shrink(salience: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    raise NotImplementedError


def transcript_density_check(transcripts: pd.DataFrame) -> pd.DataFrame:
    """Independent, volume-normalised salience from call transcripts.

    Compare against news-derived salience. Agreement validates the index;
    divergence is a finding worth a slide.
    """
    raise NotImplementedError
