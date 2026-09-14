"""Daily prices with validation. Fully independent of the corpus — bank this first.

The brief says endpoint reliability is your problem. Validate, do not assume:
  - no gap > 3 trading days
  - row count matches the NYSE calendar (exchange_calendars)
  - flag |daily return| > 25% and confirm each against a known event
  - NVDA 10:1 split, June 2024: a -90% day means the adjustment is broken

yfinance gotcha: recent versions default auto_adjust=True, which changes what
Close means. Set it explicitly rather than inheriting the default.
"""
from __future__ import annotations
import pandas as pd


def download(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Adjusted daily returns. Stooq fallback on failure. Cached to parquet."""
    raise NotImplementedError


def validate(prices: pd.DataFrame) -> dict:
    """Returns a dict of check -> pass/fail plus details. PRINT IT; do not swallow."""
    raise NotImplementedError


if __name__ == "__main__":
    download([], "", "")
