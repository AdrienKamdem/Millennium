"""Company IR newsrooms. Primary, promotional, small volume.

Nine bespoke parsers. This is the most cuttable item in the plan — if the schedule
compresses, drop it and say so rather than half-building it.
"""
from __future__ import annotations
import pandas as pd


def fetch(ticker: str) -> pd.DataFrame:
    raise NotImplementedError
