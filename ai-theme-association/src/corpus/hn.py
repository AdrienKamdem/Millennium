"""Hacker News via Algolia. Free, no key, full archive.

Covers the 'developer/social chatter' source category. Rich for
NVDA/INTC/DELL/ADBE/TEAM and near-empty for PG/WM — that asymmetry IS a
coverage-bias finding. Report it; do not quietly drop the source.
"""
from __future__ import annotations
import pandas as pd


def fetch(query: str, start: str, end: str) -> pd.DataFrame:
    raise NotImplementedError
