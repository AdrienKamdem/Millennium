"""Valence: is AI good or bad FOR THIS COMPANY.

Doc-weighted mean of valence_ai over SUBSTANTIVE AI documents only. Shrunk toward
zero, not toward the peer mean — absent evidence the honest prior is "no
directional view", not "whatever the peer group thinks".
"""
from __future__ import annotations
import pandas as pd


def raw_valence(classified: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def shrink(valence: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    raise NotImplementedError
