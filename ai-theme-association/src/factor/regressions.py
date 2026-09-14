"""Per-stock AI betas.

  r_it - rf = a + b_MKT*MKT + b_SMB*SMB + b_HML*HML + b_RMW*RMW + b_CMA*CMA
              + b_MOM*MOM + g*SECTOR_orth + d*AIF_orth + e

d is the AI beta. Newey-West (HAC, 5 lags).

Sector control is the company's own sector ETF, itself orthogonalized against
MKT + styles first so it does not absorb market beta.

RUN THE SANITY GATE BEFORE READING ANYTHING ELSE (config/ai_basket.yaml):
NVDA strongly positive, PG and WM indistinguishable from zero. If it fails the
factor is broken — report that rather than shipping betas you do not believe.

Also produce 126-day ROLLING betas. A single full-sample beta cannot be reconciled
against a time-varying semantic index, and it cannot feed the Task 7 lead-lag design.

Report VIFs. NVDA will be ugly on MOM/XLK/AIF simultaneously — that is a finding,
not an embarrassment. Note that d is "loading on the AI-specific residual", not
"total AI sensitivity".
"""
from __future__ import annotations
import pandas as pd


def run(returns: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """Per ticker: alpha, all betas, HAC standard errors, t-stats, R^2, VIFs."""
    raise NotImplementedError


def rolling_beta(returns: pd.Series, factors: pd.DataFrame, window: int = 126) -> pd.Series:
    raise NotImplementedError


def sanity_gate(results: pd.DataFrame) -> dict:
    """Returns pass/fail per gate name with the actual numbers. Print whatever it says."""
    raise NotImplementedError


def sp500_null_distribution(factors: pd.DataFrame) -> pd.DataFrame:
    """Optional: same regression across ~500 names, giving a real null distribution
    for 'indistinguishable from zero' and true percentile ranks for the 9.

    Uses current index membership, so it is survivorship-affected. Use it ONLY for
    the null distribution, never for a return claim. Say so.
    """
    raise NotImplementedError


if __name__ == "__main__":
    run(None, None)
