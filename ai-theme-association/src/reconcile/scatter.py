"""The reconciliation scatter. The one chart a PM actually reads.

x = semantic z, y = AI-beta z. All 9 labelled, 45-degree line, error bars on betas.
Quadrants: Priced & narrated / Narrated not priced / Priced not narrated / Neither.
"""
from __future__ import annotations
import pandas as pd


def plot(aligned: pd.DataFrame, out: str = "outputs/figures/reconciliation.png") -> None:
    raise NotImplementedError


def salience_valence_2x2(aia: pd.DataFrame, out: str = "outputs/figures/salience_valence.png") -> None:
    """Better than a ranked bar chart: shows WHY two names with similar scalars differ."""
    raise NotImplementedError
