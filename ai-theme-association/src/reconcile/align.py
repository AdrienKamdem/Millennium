"""Put the semantic score and the AI beta on a comparable footing.

You cannot compare a raw sentiment index to a raw beta. Cross-sectional z-scores
or percentile ranks per period. If the S&P 500 expansion was run, z against that
cross-section rather than against 8 peers.
"""
from __future__ import annotations
import pandas as pd


def align(aia: pd.DataFrame, betas: pd.DataFrame, trailing_months: int = 6) -> pd.DataFrame:
    """Per ticker: semantic_z, beta_z, beta_se, gap = semantic_z - beta_z."""
    raise NotImplementedError


def rank_correlation(aligned: pd.DataFrame, n_boot: int = 10000) -> dict:
    """Spearman rho with a bootstrap CI.

    DESCRIPTIVE ONLY. At n=9 the interval will span or nearly span zero — report it
    that way. A bare rho without the CI is the trap the brief is setting.
    """
    raise NotImplementedError
