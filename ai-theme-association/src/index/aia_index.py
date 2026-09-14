"""The AI-Association Index. Central structural call of Part 1.

    AIA_ct = S_shrunk * V_shrunk        "AI-attributable signed attention"

Multiplicative because a company with no AI coverage has no AI association
regardless of valence (S=0 -> 0), while heavy but negative AI coverage yields a
large NEGATIVE score. That is exactly the brief's "how strongly, and how
positively or negatively".

ALWAYS report the (S, V) pair alongside the scalar. Collapsing loses the
distinction between ADBE (high S, negative V) and WM (low S, V~0) — both land near
zero. The salience-vs-valence 2x2 is a better slide than a ranked bar chart.

Two normalisations, not one. The brief asks for a score that is BOTH
cross-sectionally comparable AND comparable over time; per-period z-scoring gives
the first and destroys the second (every period is mean-zero by construction, so
theme-wide drift becomes invisible). Produce both:
  - cross_sectional_z  -> the current ranking table
  - excess_salience    -> the time series
"""
from __future__ import annotations
import pandas as pd


def build() -> pd.DataFrame:
    """Per company per period: salience, valence, aia, cross_sectional_z, excess_salience."""
    raise NotImplementedError


def cross_sectional_z(aia: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def excess_salience(salience: pd.DataFrame, market_baseline: pd.Series) -> pd.DataFrame:
    """S_ct - S_market_t. Time-comparable level.

    Cheapest baseline: GDELT timelinevol for AI-topic share, or the same pipeline
    over a 30-name S&P sample.
    """
    raise NotImplementedError


def current_ranking(aia: pd.DataFrame, trailing_months: int = 3) -> pd.DataFrame:
    raise NotImplementedError


if __name__ == "__main__":
    build()
