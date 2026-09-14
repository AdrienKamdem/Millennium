# AI-Theme Association: From Semantic Signal to Factor Exposure

A two-stage system measuring how strongly — and how positively or negatively — a company is
associated with the AI theme, and whether that semantic association corresponds to a market-priced
AI exposure.

**Universe:** ADBE, CAT, DELL, INTC, MU, NVDA, PG, TEAM, WM
**Window:** Jan 2023 – Sep 2026

- **Part 1** derives a text-based AI-association score per company from public text.
- **Part 2** runs a factor model isolating an AI factor's contribution to each company's returns.
- **Part 3** reconciles the two and interrogates the disagreements.

Findings summary: [`docs/findings.pdf`](docs/findings.pdf) · Full workings: [`docs/appendix.md`](docs/appendix.md)

---

## Setup

```bash
git clone https://github.com/AdrienKamdem/Millennium-Case-Study.git
cd Millennium-Case-Study
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # add ANTHROPIC_API_KEY and a contact email for the SEC User-Agent
```

## Running

```bash
make all          # full pipeline from cache — no network, no API spend
make corpus       # re-fetch and rebuild the text corpus      (~40 min, network)
make classify     # LLM classification + aspect sentiment     (~20 min, ~$X in API)
make index        # build the AI-association index
make factor       # AI factor construction + regressions
make reconcile    # reconciliation, scatter, divergence tables
```

All network calls are cached to disk keyed by request hash, so `make all` is reproducible offline
from the committed cache. Re-fetching is opt-in.

---

## Pipeline

```
corpus  →  classify  →  index  ─┐
                                ├──→  reconcile  →  outputs/
prices  →  ai_factor  →  betas ─┘
```

Parts 1 and 2 are independent by design: the AI factor is **price-derived, not text-derived**, so
the semantic score and the factor-implied beta are genuinely separate instruments. A text-derived
factor would have made the reconciliation circular.

---

## Data sources

Full log with categories, coverage and limitations: [`docs/sources_log.csv`](docs/sources_log.csv).
Summary:

| Source | Category | Coverage |
|---|---|---|
| SEC EDGAR (10-K / 10-Q / 8-K) | Primary | All 9 names, full window |
| 8-K Exhibit 99.1 earnings releases | Primary | All 9 names, quarterly |
| Earnings-call transcripts | Primary (verbatim) | _TBC — see sources log_ |
| Company IR newsrooms | Primary | All 9 names |
| News headlines + metadata | Secondary | _TBC — see sources log_ |
| Hacker News (Algolia API) | Secondary | Developer-facing names only |
| Prices (yfinance / Stooq) | Primary | Daily, full window |
| Fama-French 5 + Momentum | Primary | Kenneth French Data Library, daily |

Sources tested and rejected are recorded in the log with the reason.

---

## Key design decisions

**Salience is a share, not a count.** AI-relevant documents as a proportion of all coverage of that
company, so a company covered more heavily because it is larger does not register as more
AI-associated.

**Thin-coverage shrinkage.** Monthly coverage for the smaller names is sparse enough that raw shares
are dominated by sampling noise. Salience is shrunk toward the company's trailing mean with weight
`n/(n+k)`; valence is shrunk toward zero. Sensitivity to `k` is reported in the appendix.

**The index is signed and reported as a pair.** The headline score is salience × valence, but
`(salience, valence)` is reported alongside it — collapsing to a scalar conflates "little AI
coverage" with "heavy but negative AI coverage," which are different states. Aspect-based sentiment
is conditioned on AI's impact on *this company*, not on the document's overall tone.

**Two normalisations, not one.** Cross-sectional z-scores for the current ranking; excess salience
against a market baseline for the time series. Per-period z-scoring is mean-zero by construction and
cannot show theme-wide drift.

**AI factor = pure-play basket minus tech sector, then orthogonalized** against market, size, value,
profitability, investment and momentum. All nine test names are excluded from the factor legs. An
ETF-based alternative (AIQ) was built as a robustness check and its composition examined; see the
appendix for why the long-short construction was preferred.

**Classification cascade.** Lexicon prefilter → local embeddings (free, CPU) → LLM. The LLM budget is
spent on the ambiguous band rather than uniformly. Classification and aspect sentiment are returned
in a single structured call. Model and token usage per task: [`docs/token_log.csv`](docs/token_log.csv).

---

## Known limitations

- _[Coverage gaps — fill in from the corpus EDA]_
- _[Classifier agreement / error rates — fill in from the validation suite]_
- Rank correlation in the reconciliation is descriptive only. At n=9 the confidence interval is wide
  enough that the comparison is case-based, not statistical.
- The AI factor's pure-play basket is selected with hindsight. A point-in-time variant is reported
  alongside it _[or: was descoped — see appendix]_.
- The S&P 500 cross-section uses current index membership and is therefore survivorship-affected. It
  is used only to give a null distribution for the AI betas, not for any return claim.
- _[Anything you deliberately went shallow on, and why]_

---

## Repo layout

```
config/      universe, sources, taxonomy, factor basket definitions
src/
  corpus/    sourcing, parsing, deduplication
  classify/  prefilter, embeddings, LLM classification, validation
  index/     salience, valence, the AI-association index
  factor/    prices, Fama-French factors, AI factor, regressions
  reconcile/ alignment, scatter, divergence analysis
data/        raw / interim / processed  (cache; a small sample is committed)
notebooks/   01_corpus_eda  02_classifier_eval  03_factor  04_reconcile
outputs/     figures, tables
docs/        findings, appendix, sources log, scaling memo, token log
```
