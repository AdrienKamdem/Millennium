"""Classifier diagnostics. Task 2 asks for quality on a reviewed sample, and for
the documents the classifier gets WRONG — shown, not summarised.

Four checks, ~40 minutes total, substituting for a full hand-labelled set:

1. cross_model_agreement  — Haiku vs Sonnet on the same 250 docs, Cohen's kappa
   per field. Disagreement is a legitimate upper bound on accuracy, nearly free.
2. spot_review            — 40 docs stratified by predicted class. Indicative
   precision, and it produces the error examples.
3. buzzword_trap          — 20 hand-picked docs where 'AI' is pure boilerplate.
   False-positive rate here is the sharpest demonstration of buzzword separation.
4. name_masking           — re-run 100 docs with the company name replaced by
   [COMPANY]. If valence moves materially, the model is scoring its own priors
   about NVDA/INTC rather than the text. That is a look-ahead leak dressed as
   sentiment, and it is the check nobody else will run.

State the limitations: kappa measures consistency, not correctness; LLM valence is
not calibrated across companies; headline-only classification lacks context.
"""
from __future__ import annotations
import pandas as pd


def cross_model_agreement(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    raise NotImplementedError


def spot_review_sample(classified: pd.DataFrame, n: int = 40) -> pd.DataFrame:
    """Stratified by predicted class. Write to docs/ as a CSV you fill in by hand."""
    raise NotImplementedError


def buzzword_trap(classified: pd.DataFrame) -> dict:
    raise NotImplementedError


def name_masking_test(docs: pd.DataFrame, n: int = 100) -> dict:
    """Returns correlation between masked and unmasked valence, plus the movers."""
    raise NotImplementedError
