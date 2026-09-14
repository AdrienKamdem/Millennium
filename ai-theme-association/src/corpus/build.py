"""Assemble the corpus and produce the coverage-bias report (Task 1).

The coverage report is not a box-tick: the thin-coverage problem it exposes is the
stated reason for the shrinkage step in index/salience.py. Make that link explicit
in the write-up — it shows the bias analysis changed a design decision.

FREEZE THE CORPUS once this is run. A corpus that keeps growing is the standard
way this case study fails; the brief warns corpus work will eat 40-50% of the time.
"""
from __future__ import annotations
import pandas as pd


def build() -> pd.DataFrame:
    """Fetch all sources, dedupe, write data/processed/corpus.parquet."""
    raise NotImplementedError


def coverage_report(corpus: pd.DataFrame) -> pd.DataFrame:
    """Docs by company x source x quarter. Feeds the heatmap and the bias paragraph."""
    raise NotImplementedError


if __name__ == "__main__":
    build()
