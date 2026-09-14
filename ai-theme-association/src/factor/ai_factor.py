"""AI factor construction. Central structural call of Part 2.

AIF-1 (primary): long AI pure-plays, short XLK, then orthogonalized against
MKT/SMB/HML/RMW/CMA/MOM and XLK. Reading "pure-plays minus tech sector" pre-empts
the objection that the factor is just tech beta.

  HARD CONSTRAINT: none of the 9 test names in any leg. Including NVDA and then
  reading NVDA's beta off the result is mechanically circular.

  Report the first-stage R^2. If orthogonalization strips 85% of the variance, say
  so — betas are then read off a thin residual and the standard errors should
  reflect it. Honesty beats a large coefficient.

AIF-2 (robustness): a thematic ETF, AND TAKE IT APART. The brief says examine what
your ingredient is actually made of. Pull holdings, correlate against XLK and SPY,
regress on MKT + XLK. A high R^2 means the ETF is largely a mega-cap tech
repackage with little independent variance — that negative result, used as the
stated reason for preferring AIF-1, is worth more than any coefficient.

AIF-3 (optional): first PC of pure-play residuals after removing MKT + XLK. No
hand-picked weights, so it partially defuses look-ahead. Convergent validity if it
correlates ~0.8 with AIF-1.

Circularity: all three are PRICE-derived, not text-derived. That is what keeps
Part 1 and Part 2 independent instruments and makes the reconciliation meaningful.
State it as the explicit reason a text-intensity factor was rejected.
"""
from __future__ import annotations
import pandas as pd


def build_aif1(prices: pd.DataFrame, point_in_time: bool = False) -> pd.Series:
    """Equal-weighted long basket minus XLK. point_in_time gates entry on first
    filing disclosing material AI revenue, +1 quarter lag."""
    raise NotImplementedError


def orthogonalize(factor: pd.Series, controls: pd.DataFrame) -> tuple[pd.Series, float]:
    """Residualise against controls. Returns (residual, first_stage_r2)."""
    raise NotImplementedError


def teardown_etf(etf: str = "AIQ") -> dict:
    """Holdings, correlation vs XLK/SPY, R^2 on MKT+XLK. The 'examine your ingredient' check."""
    raise NotImplementedError


if __name__ == "__main__":
    build_aif1(None)
