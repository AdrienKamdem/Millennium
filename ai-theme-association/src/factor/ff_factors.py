"""Fama-French 5 + Momentum, daily, from the Kenneth French Data Library.

Values are in PERCENT. Divide by 100 before joining to returns or every beta is
100x wrong — and it will not look obviously wrong, which is why it bites.
"""
from __future__ import annotations
import pandas as pd


def load(start: str, end: str) -> pd.DataFrame:
    """Columns: Mkt-RF, SMB, HML, RMW, CMA, MOM, RF. Decimal, not percent."""
    raise NotImplementedError


if __name__ == "__main__":
    load("", "")
