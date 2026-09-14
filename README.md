# Millennium TMT Case Study — Design Draft v1

> **Compliance banner.** This plan file is the only artefact produced in the Bloomberg environment.
> Everything downstream — repo, data fetching, API calls, commits, the deck — happens on a personal
> machine, personal GitHub, personal internet. Copy this file off and delete the local copy.
> Claude's role from here is **reviewer and planner only**, against your personal repo.

---

## Context

You have a final-round take-home for Millennium's TMT trading group. They scope it at **~2 days of
work**; you have a week of evenings plus a weekend. The graded artefacts are a **4–6 slide findings
deck** (what a PM reads) and a **GitHub repo** (how you work). They say explicitly that they are not
grading precision — they are grading *structured reasoning under uncertainty*, *where you chose to
spend your time*, and *whether you documented your shortcuts*.

The single most important framing sentence in the brief:

> *"Where the two methods disagree, the disagreement is the interesting result — treat it as signal,
> not as a bug to be smoothed away."*

This is not a data-engineering test with a numerical answer. It is a judgment test wearing a
data-engineering costume. Plan accordingly.

---

## Part A — The problem in plain words

You are building **two independent instruments** that both try to answer one question:
*"How much of an AI company is this?"* Then you compare their readings and explain the gaps.

**Instrument 1 — the text instrument (Part 1).**
Read a large pile of public text about 9 companies. For each company, each month, measure two things:

- **Salience** — what *share* of the talk about this company is genuinely about AI? (Share, not count:
  NVDA gets 50× the coverage of WM, so raw counts measure market cap, not AI-ness.)
- **Valence** — when people talk about AI in connection with this company, is it *good news for this
  company*? Note the subtlety: an article can be enthusiastic about AI and simultaneously bearish on
  Adobe, because generative AI threatens Adobe's moat. Document-level sentiment gets this exactly
  backwards, which is why they insist on **aspect-based** sentiment.

Combine into one **AI-Association Index** per company per month.

**Instrument 2 — the market instrument (Part 2).**
Build a return series that represents "the AI theme was in favour today." Then, for each of the 9
stocks, regress its daily returns on the usual risk factors (market, size, value, momentum,
profitability, investment) **plus its sector** **plus** your AI factor. The coefficient on the AI
factor is that company's **AI beta** — how much the *market* treats it as an AI play, in dollars,
independent of the fact that it's a tech stock.

**Part 3 — reconciliation.**
Put both on the same scale (z-scores), scatter them, and interrogate the outliers. Text measures
*what is said*. Beta measures *what is paid for*. Every gap is one of three things, and your job is
to say which:

1. **A mispricing** — the market hasn't priced a real AI exposure yet (or has over-priced one).
2. **A transmission channel you failed to instrument** — the exposure is real and priced, but it
   travels through text your corpus never saw.
3. **A measurement failure** — your classifier, your corpus, or your factor is broken.

That three-way triage is the strongest thing you can put in the deck. Almost every candidate will
produce a scatter plot. Very few will assign each divergence to one of those three buckets and say
how they'd test it.

### Why *these* 9 names

The universe is not random. It is a designed spectrum, and recognising that is itself a signal:

| Ticker | Expected role in the test |
|---|---|
| **NVDA** | Pure play. Sanity check — must load strongly positive on the AI factor. If it doesn't, your factor is broken. |
| **MU**, **DELL** | AI infrastructure beneficiaries (HBM, AI servers). Should score high on both instruments. |
| **INTC** | Loud AI *narrative*, weak AI *revenue*. Likely high salience, mixed valence, weak beta. A divergence candidate. |
| **ADBE** | The **negative-valence** case. Huge AI salience, but the story is "AI eats Adobe's moat." Tests whether your index is signed. |
| **TEAM** | SaaS with both an AI narrative and AI-displacement fear (seat-based pricing vs. agents). |
| **CAT** | **The planted divergence.** Near-zero AI text, but plausibly a real AI beta via data-centre power/gensets. Tests whether you notice a channel your corpus can't see. |
| **PG**, **WM** | Null controls. Both instruments should read ~zero. If they don't, something leaked. |

Build your narrative around ADBE (signed index), CAT (missing channel), and PG/WM (nulls that
validate the whole apparatus). Those three stories carry the deck.

---

## Part B — What they're actually asking for, task by task

| # | Task | What they want to see | Time |
|---|---|---|---|
| 1 | Corpus | Not volume — **coverage accounting**. Docs by company × source × quarter, dedup logic written down, and an honest paragraph on who is over/under-covered and how that biases the score. | 5–6 h |
| 2 | AI-relevance classification | A **cascade** (cheap filter → embeddings → LLM), a taxonomy you refined rather than copied, and **the documents your classifier gets wrong**, shown. They said this twice. | 3 h |
| 3 | Aspect sentiment | Sentiment about **AI's impact on this company**, not about the document's mood. Plus an honest limitations paragraph. | (merged into 2) |
| 4 | The index | The **central structural call of Part 1**. Salience × valence, volume-controlled, shrunk for thin coverage, indexed to a baseline, comparable both across companies *and* over time. | 2 h |
| 5 | Factor model | The **central structural call of Part 2**. Construct an AI factor, **look inside your ingredient**, orthogonalize it, run controlled regressions, read betas, guard look-ahead / multicollinearity / circularity. | 3 h |
| 6 | Reconciliation | Scatter + rank correlation *with a "this is descriptive, n=9" caveat* + 2–3 divergences each with a **falsifiable** hypothesis. Core judgment test. | 2 h |
| 7 | Lead–lag | **Design only.** A causal mechanism per signal (not "AI adoption") and an honest power calculation. Implementation is explicitly *not* expected. | 1 h |
| 8 | Sources + scaling memo | Every source tagged Primary/Secondary/Inferred. Half-page memo: what breaks first at 2,000 names, and which choices only work *because* n=9. | 1.5 h |

**Where the marks concentrate:** Tasks 4, 5, 6. Tasks 1 and 2 are the *cost*; tasks 4–6 are the
*product*. Do not let corpus engineering eat the reconciliation.

---

## Part C — The design

### C.0 Universe & window

9 tickers, **Jan 2023 → Sep 2026** (~45 months). Monthly periods for the index (with a quarterly
version as a robustness check — monthly is thin for WM/PG/TEAM). Daily returns for the factor model.

Corpus target **~3,000–4,000 documents**, which the brief calls acceptable. Do not chase 5k.

---

### C.1 Corpus (Task 1) — and the one thing that can sink this

**The #1 execution risk is historical news access.** Most free news APIs only serve the last 30 days
to 12 months. Your window starts Jan 2023. Before writing any pipeline code, spend **45 minutes on
day 1 probing which sources actually return January-2023 results.** Everything else in the schedule
depends on the answer. Write the probe results into the sources log — the probe itself is
documentable evidence of source triangulation, which is literally Task 1.

**Tier 1 — guaranteed, build these first (Primary, free, no auth headaches):**

| Source | What you get | Category | Notes |
|---|---|---|---|
| **SEC EDGAR** (`data.sec.gov` submissions + `efts.sec.gov` full-text search) | 10-K / 10-Q / 8-K for all 9. Extract Item 1, 1A, 7. | **Primary** | 100% reliable. Just needs a `User-Agent` header. Never rate-limit yourself out — 10 req/s cap. |
| **8-K Exhibit 99.1** | Quarterly earnings press releases, every name, every quarter, guaranteed. | **Primary** | The reliable substitute for transcripts. ~135 docs. |
| **Company IR newsroom / RSS** | Press releases. ~50–150 per name. | **Primary** | 9 bespoke scrapers, but small and stable. |
| **Hacker News Algolia API** (`hn.algolia.com/api/v1/search_by_date`) | Full archive, free, no key. Developer/social chatter. | **Secondary** | 30 minutes of work, ticks the "developer chatter" box in the brief. Good for NVDA/INTC/DELL/ADBE/TEAM, useless for PG/WM — which is itself a coverage-bias finding worth reporting. |

**Tier 2 — the news backbone, probe before committing:**

- **GDELT 2.0 DOC API** (`api.gdeltproject.org/api/v2/doc/doc`) — free, no key, headlines + URL +
  domain + date + tone. Query per company per month (9 × 45 = 405 calls, `maxrecords=250`).
  *Probe first:* the DOC API's reliable historical depth varies. Fire one query for
  `startdatetime=20230101000000&enddatetime=20230201000000` and see what comes back.
- **Fallback if GDELT DOC is shallow: GDELT on BigQuery.** `gdelt-bq.gdeltv2.gkg_partitioned`,
  filtered on `V2Organizations` and date-partitioned, selecting only the 4 columns you need.
  BigQuery's free tier is 1 TB/month; a tightly-projected, partition-pruned query over 45 months
  should fit if you run it **once** and cache to parquet. Test with `--dry_run` first to see the
  bytes-scanned estimate *before* you run it. This is the robust answer and worth the extra hour.
- **Secondary fallbacks:** Finnhub `/company-news` free tier (~1 yr history — use for the recent
  window only), Alpha Vantage `NEWS_SENTIMENT` (has `time_from`, free tier is rate-crippled at ~25
  req/day, premium ~$50/mo). Wayback Machine CDX over IR index pages if all else fails.

**Deduplication logic** (write this down explicitly — they ask):
1. Canonicalise URLs (strip UTM/query params, resolve redirects).
2. Exact-hash on canonical URL.
3. Near-duplicate on titles: normalise (lowercase, strip punctuation/stopwords), then TF-IDF cosine
   > 0.90 within a ±3-day window. One wire story republished by 12 outlets collapses to one doc,
   with a `n_republications` field retained — republication count is itself a salience signal, so
   keep it rather than throwing it away.
4. Cross-source dedup: an IR press release and the news report of it are *different* documents
   (Primary vs Secondary) — keep both, tag them, and weight them differently in the index.

**Coverage-bias section** (a table + a heatmap + one honest paragraph):
- Docs per company × source × quarter.
- Named biases: NVDA over-covered ~10:1 vs WM; GDELT is English/US-skewed; HN covers only the
  developer-facing names; TEAM as an Australian-founded, US-listed name may be thin in US wires.
- **How it distorts:** salience is a *share*, so volume differences largely cancel in the numerator
  and denominator — but thin months produce high-variance shares. That is exactly what the shrinkage
  step in §C.3 exists to fix. Say this connection out loud; it shows the bias analysis actually
  changed a design decision rather than being a box-tick.

---

### C.1b Earnings transcripts — the trade-off you asked me to lay out

Transcripts are the highest-value text in the whole corpus: **management's own AI framing, plus the
analyst Q&A where someone asks "how much AI revenue, actually?"** That Q&A exchange is where the
honest signal lives. They are also the hardest free thing to get. Three routes:

**Route A — Scrape Motley Fool (free)**
- *Pros:* full archive back to 2023; covers all 9 names; clean speaker-tagged HTML; verbatim, so it
  counts as primary text (secondary host). Zero cost.
- *Cons:* URLs are unpredictable slugs, so you need their sitemap or search index to enumerate them.
  Bot protection has tightened, so expect Cloudflare friction. **Realistic cost: 2–4 hours, with a
  non-trivial chance of a dead end.** Also against their ToS — fine for a private case study, but
  you should note in the sources log that a production version would license this.
- *Verdict:* the classic time sink. If you take this route, **hard-timebox it to 60 minutes.**

**Route B — Buy a transcript API (~£20–40 of the £100)**
- Financial Modeling Prep, API Ninjas, and similar serve transcripts as clean JSON by
  ticker/quarter/year. Roughly **15 minutes of integration** versus 2–4 hours of scraping.
- *Check the current free tier before paying* — several offer enough trial calls to grab 135
  transcripts, in which case you pay nothing.
- The brief **invites this**: *"Any remaining budget may optionally be spent on higher-quality data
  sources (e.g. managed earnings-transcript APIs)."* Buying the data and spending the saved 3 hours
  on the reconciliation is precisely the resource-allocation judgment they say they are grading.
  Write one line in the sources log: *"Bought transcripts rather than spend 3h on a fragile scraper;
  reallocated that time to Task 6."* That line scores points.

**Route C — SEC-only substitute (free, guaranteed)**
- 8-K EX-99.1 earnings releases + 10-K/10-Q MD&A + Item 1A risk factors. Every name, every quarter,
  100% reliable, ~90 minutes to build.
- *What you lose:* the Q&A. Prepared remarks are marketing; Q&A is where AI claims get pressure-tested.
  You also lose the single cleanest salience metric (see below).
- *What you keep:* Item 1A risk factors are a genuinely underrated AI signal — ADBE and TEAM will have
  added AI-as-competitive-threat language, which is **negative-valence primary disclosure**. That is
  a strong, cheap find.

**Recommendation:** Build **C first** (guaranteed, ~90 min, and you need EDGAR plumbing anyway).
Then timebox 60 minutes to B — check free tiers, buy if cheap. Only fall back to A if both fail.

**Why transcripts matter beyond text volume:** *AI-mention density on an earnings call* —
AI-mentioning sentences ÷ total sentences — is the cleanest volume-normalised salience measure you
can construct, because call length is roughly constant across companies and quarters. It needs no
shrinkage, no share-of-coverage normalisation, and no dedup. **Use it as the independent robustness
check on your news-derived salience.** If the two agree, your index is credible; if they diverge,
that's a finding. This is worth a slide on its own and is the single strongest argument for paying
for transcripts.

---

### C.2 Classification + aspect sentiment (Tasks 2 & 3)

**Three-tier cascade** — this *is* the token-efficiency story they asked you to defend:

- **Tier 0 — lexicon prefilter (free).** Curated AI vocabulary: `artificial intelligence`, `LLM`,
  `generative`, `copilot`, `inference`, `accelerator`, `foundation model`, `agentic`, `transformer`,
  `NPU`, `HBM`, `machine learning`, `neural`… **Watch the `AI` substring trap** — use case-sensitive
  word-boundary matching (`\bAI\b`, `A\.I\.`) or you will match "Air", "AIG", "Dubai". Tier 0 *tags
  candidates*; it never decides. Every document stays in the denominator.
- **Tier 1 — local embeddings ($0).** Embed all titles with `bge-small-en-v1.5` or
  `all-MiniLM-L6-v2` via `sentence-transformers`, on CPU. Two jobs: (a) recall documents the lexicon
  missed, (b) **rank documents by AI-likelihood so the LLM budget goes to the ambiguous middle band**
  rather than the obvious top and bottom. Note: Anthropic has no embeddings endpoint — local is both
  free and the right call, and saying so is a documented, justified choice.
- **Tier 2 — LLM ($). Claude Haiku 4.5** (`claude-haiku-4-5`, $1/$5 per MTok) for the bulk pass;
  **Claude Sonnet 5** (`claude-sonnet-5`, $2/$10) for the ambiguous band and all transcript/filing
  passages. Use the **Batch API (50% off)** and **prompt caching** on the taxonomy rubric — the
  rubric is a fixed ~1,500-token prefix reused across every call, so cache it and verify with
  `usage.cache_read_input_tokens`. Both levers together cut the bill roughly 60–70%.

**Refined taxonomy — make it two-dimensional.** The brief gives a flat 5-way list and invites you to
refine it. Flattening is the weaker answer because "partnership announcement" and "positive" are
orthogonal facts. Emit one structured JSON object per document:

```json
{
  "ai_relevance":  "none | incidental | substantive",
  "ai_role":       "A_partnership | B_costcut | C_positive_exposure | D_negative_exposure | E_none",
  "materiality":   "low | medium | high",
  "valence_ai":    -2,
  "confidence":    0.0,
  "evidence_span": "the exact quoted phrase justifying the call"
}
```

Three reasons this schema is stronger than a 5-way label:
1. `ai_relevance` × `ai_role` separates *"is this about AI?"* from *"what kind of AI story is it?"* —
   which is exactly the buzzword-separation the brief asks for. `incidental` **is** the buzzword class.
2. `evidence_span` forces the model to ground its call in the text and makes your error review
   possible — you can see *why* it was wrong, not just *that* it was.
3. Classification and aspect sentiment come back in **one call**, halving token cost. Document that
   as a deliberate cost decision.

**The aspect-sentiment prompt is the crux of Task 3.** The instruction must be roughly:

> *Holding aside the document's overall tone, and judging only from the text provided: does this
> imply AI is a tailwind or a headwind to **this specific company's** revenue, margins, or
> competitive position? −2 = clear headwind … +2 = clear tailwind. 0 if AI is mentioned but the
> impact on this company is not assessable.*

The clause *"judging only from the text provided"* matters — without it the model answers from its
own 2025-era knowledge of who won, which is a **look-ahead leak dressed as sentiment**.

**Validation — the cheap version** (you opted out of the 150-doc hand-label; here's the substitute
that still satisfies *"classification quality on a reviewed sample"*, at ~40 minutes instead of 90):

1. **Cross-model agreement.** Run Haiku *and* Sonnet over the same 250-doc random sample. Report
   Cohen's κ per field and the confusion matrix between them. Disagreement rate is a legitimate
   upper bound on accuracy and costs you almost nothing.
2. **A 40-doc spot review**, stratified by predicted class — enough for indicative precision by
   class, and it produces the error examples they explicitly ask for. 40 docs is ~30 minutes.
3. **A 20-doc buzzword trap set.** Hand-pick documents where "AI" appears only in boilerplate
   (a footer, a conference name, an unrelated product blurb). Report the false-positive rate on it.
   This is the sharpest possible demonstration of buzzword separation, for 15 minutes of work.
4. **The name-masking test — do this, it's the differentiator.** Re-run 100 documents with the
   company name replaced by `[COMPANY]`. If valence scores shift materially, the model was scoring
   its priors about NVDA/INTC rather than the text. Report the correlation between masked and
   unmasked scores. This directly addresses the look-ahead concern they raise in Task 5 and applies
   it to Part 1, where they didn't even ask for it. **Cost: ~20 minutes and a few cents.** Nobody
   else will do this.
5. Show 6–10 misclassifications with a sentence each on *why* the model failed.

State the limitations honestly: LLM valence is not calibrated *across* companies; headline-only
classification lacks context; coverage is survivorship-affected (dead links vanish); κ measures
consistency, not correctness.

---

### C.3 The AI-Association Index (Task 4) — central structural call of Part 1

Three separable components. Report all three, not just the scalar.

Let `c` = company, `t` = month.

**1. Salience** — materiality-weighted AI share of coverage:

```
S_ct = Σ_d [ w_d · m_d · 1(substantive) ] / Σ_d w_d
```

- `w_d` = source weight (Primary disclosure 1.0 > IR release 0.8 > news 0.6 > social 0.3). Document
  the weights and run one sensitivity check with all weights = 1.
- `m_d` = materiality weight (high 1.0 / medium 0.6 / low 0.2).
- Because it's a **share**, volume is controlled by construction. This is the direct answer to
  *"a company mentioned more simply because it is larger should not appear to be improving."*

**2. Shrinkage — the step most candidates will skip.** Thin months (WM, PG, TEAM) produce wildly
noisy shares: 1 AI article out of 3 total is *not* 33% salience. Empirical-Bayes shrink toward the
company's trailing 12-month mean:

```
S̃_ct = λ_ct · S_ct + (1 − λ_ct) · S̄_c,trailing        where  λ_ct = n_ct / (n_ct + k),  k ≈ 10
```

Justify `k` by showing the month-over-month variance of the raw vs. shrunk series. This is the
technically correct fix for the coverage bias you documented in Task 1 — and it visibly *connects*
Task 1 to Task 4, which is worth saying explicitly in the deck.

**3. Valence** — doc-weighted mean of `valence_ai` over **substantive AI documents only**, shrunk
toward 0 (not toward the peer mean — absent evidence, the honest prior is "no directional view").

**4. Combine — multiplicatively, and keep the pair.**

```
AIA_ct = S̃_ct × Ṽ_ct          ("AI-attributable signed attention")
```

Why multiplicative: a company with no AI coverage has no AI association regardless of valence
(S=0 → 0); a company with heavy AI coverage that is all bad news gets a large *negative* score.
That is exactly the semantics the brief describes — *"how strongly — and how positively or
negatively."*

**But always report `(S, V)` alongside the scalar.** Collapsing to one number destroys the ADBE
story (high S, negative V) versus the WM story (low S, V≈0) — both could land near zero. A 2×2 of
salience vs valence with the 9 names plotted is a better slide than a ranked bar chart, and the
*decision to report the vector rather than only the scalar* is itself a judgment signal.

**5. Baseline — and a trap in the brief worth catching.** They ask for a score that is *both*
cross-sectionally comparable *and* comparable over time. Pure per-period z-scoring gives you the
first and destroys the second: every month is mean-zero by construction, so you can never see "the
whole sector's AI intensity rose." Produce **both**:

- **Cross-sectional ranking** — per-period z against the 9-name panel (and against the S&P 500
  sample if you build it). Use this for the current ranking table.
- **Time-comparable level** — *excess salience*: `S̃_ct − S_market,t`, where `S_market,t` is the same
  measure computed over a background corpus. Cheapest way to get it: GDELT's own AI-topic volume
  timeline (`mode=timelinevol`), or the same pipeline run over a 30-name S&P sample. Use this for
  the time-series chart.

Calling out this tension explicitly — *"z-scoring satisfies their cross-sectional requirement but
silently violates their over-time requirement, so I produce both"* — is a cheap, high-visibility
demonstration of reading the brief carefully.

**Deliverables:** small-multiples time series (9 panels, not 9 lines on one axis), and a current
cross-sectional ranking on the trailing 3-month average.

---

### C.4 Factor model (Task 5) — central structural call of Part 2

**Price data.** Daily adjusted returns Jan 2023 → present via `yfinance`, **Stooq as fallback**,
cached to parquet. Validate — they explicitly say endpoint reliability is your problem:
- no gap > 3 trading days,
- row count matches the NYSE calendar,
- flag any `|return| > 25%` and manually confirm against a split/earnings event,
- assert adjusted-close continuity across known splits (NVDA 10:1 in June 2024 — if your NVDA series
  shows a −90% day, your adjustment is broken; this is a real, catchable bug and worth mentioning
  in the README as a validation you ran).

**Controls.** Daily Fama-French 5 + Momentum from the Kenneth French Data Library. Sector control =
the company's own sector ETF excess return (XLK for ADBE/DELL/INTC/MU/NVDA/TEAM, XLI for CAT/WM,
XLP for PG), itself orthogonalized against MKT + the style factors first.

**Build two AI factors and show robustness.**

**AIF-1 (primary) — long-short pure-play basket, sector-neutral:**

```
AIF_raw,t = mean(returns of AI pure-play basket) − return(XLK)
```

- Long leg: AI pure-plays **excluding all 9 test names** — this is essential and easy to get wrong.
  Leaving NVDA in the factor and then reading NVDA's beta off it is mechanically circular.
  Candidates: AVGO, AMD, TSM, ARM, MRVL, ANET, VRT, SMCI, ASML, PLTR.
- Short leg: XLK. So the factor reads "AI pure-plays **minus** the tech sector" — which pre-empts
  the obvious objection that your AI factor is just tech beta.
- **Then orthogonalize:** regress `AIF_raw` on MKT, SMB, HML, RMW, CMA, MOM and XLK excess return;
  keep the residual as `AIF⊥`. Betas read off `AIF⊥` mean "AI exposure *not* explained by market,
  style, or tech sector." Report the R² of that first-stage regression — if it's 0.85, say so, and
  note that the residual is a thin slice of variance. Honesty here beats a big number.

**AIF-2 (robustness) — an ETF, and then take it apart.** Use AIQ or ARTY. The brief says *"examine
what your chosen ingredient is actually made of"* — so actually do it: pull the holdings, show the
weights, show the correlation matrix against XLK and SPY, and regress the ETF on MKT + XLK. You will
very likely find it is largely a mega-cap tech repackage with little independent variance.
**Reporting that finding — and using it as the stated reason you prefer AIF-1 — is worth more than
any regression coefficient in the deck.** It is exactly the "examine your ingredient" instruction,
and it is a *negative* result, which is the kind they said they want.

**AIF-3 (optional, ~20 lines)** — first principal component of pure-play residuals after removing
MKT + XLK. If it correlates ~0.8 with AIF-1, you have convergent validity from a method with no
hand-picking at all. Cheap, and it partially defuses the look-ahead objection.

**The regression:**

```
r_it − r_ft = α_i + β_MKT·MKT + β_SMB·SMB + β_HML·HML + β_RMW·RMW
            + β_CMA·CMA + β_MOM·MOM + γ_i·SECTOR⊥ + δ_i·AIF⊥ + ε_it
```

`δ_i` is the **AI beta**. Newey–West (HAC, 5 lags) standard errors.

**Sanity gate — run this before anything else and report it:** NVDA must be strongly positive and
significant; PG and WM must be statistically indistinguishable from zero. The brief states this test
explicitly. If it fails, your factor is broken — say so in the deck rather than reporting betas you
don't believe. A candidate who reports "my null names weren't null, here's why I think that is" is
more hireable than one who quietly ships it.

**Rolling betas — don't skip this.** A single full-sample beta cannot be reconciled against a
*time-varying* semantic index, and it certainly can't feed the Task 7 lead–lag design. Produce
**126-day rolling `δ_i`** alongside the full-sample estimate.

**The three named hazards, each with a concrete handling:**

- **Look-ahead.** Your pure-play basket is chosen in 2026 knowing who won. Mitigations, in
  increasing order of effort: (a) state the bias plainly; (b) build the **point-in-time variant** —
  a name enters the long leg only after its first 10-K/10-Q disclosing material AI/accelerator
  revenue, with a one-quarter reporting lag; (c) show betas from both and confirm the ranking is
  stable. **(b) is in scope** (see §D) — it directly answers a hazard they name, and "my ranking is
  unchanged under a point-in-time basket" is a strong, short slide.
- **Multicollinearity.** Report VIFs. NVDA will be ugly on MOM/XLK/AIF simultaneously — that is a
  finding, not an embarrassment. Note that orthogonalization already handles the interpretation, and
  that `δ` should be read as "loading on the AI-specific residual," not "total AI sensitivity."
- **Circularity.** AIF-1 is **price-derived, not text-derived**, so Part 1 and Part 2 are genuinely
  independent instruments and the reconciliation is meaningful. State this in one sentence as the
  explicit reason you rejected a text-intensity factor. It's a clean answer to a question they went
  out of their way to plant.

---

### C.5 Reconciliation (Task 6)

- Both sides → cross-sectional z-scores (semantic: trailing-6-month average AIA; market: full-sample
  `δ` with its standard error).
- **Labeled scatter**, x = semantic z, y = AI-beta z, all 9 named, 45° line drawn, error bars on the
  betas. Quadrant labels: *Priced & narrated* / *Narrated, not priced* / *Priced, not narrated* /
  *Neither*.
- **Spearman ρ with a bootstrap CI.** At n=9 the CI will span or nearly span zero. Report it that
  way — *"ρ = 0.6, 95% CI [−0.1, 0.9]; descriptive only"* — exactly as they instruct. Quoting a bare
  ρ without the CI is the trap.
- **Top 3 divergences, each with a falsifiable test.** Draft hypotheses (verify against your actual
  numbers before committing):
  - **CAT — high beta, ~zero semantic.** *Hypothesis:* the AI exposure is real but travels through
    data-centre power and backup generation, discussed in energy/industrial trade press and in CAT's
    Energy & Transportation segment disclosures — text your AI-tagged news corpus never sees.
    *Test:* add VRT/ETN/GEV returns to CAT's regression; if `δ_CAT` collapses, the channel is
    confirmed and this is a **missing-instrument** divergence, not a mispricing. Second test: does
    E&T segment revenue track hyperscaler capex guidance?
  - **ADBE — high salience, negative valence, weak/negative beta.** *Hypothesis:* the market prices
    Adobe as an AI *loser*; salience and beta only reconcile once valence is signed. *Test:* show
    that unsigned salience mis-ranks ADBE and that `S × V` fixes it. **This case validates the
    multiplicative index design** — make that link explicit; it turns a modelling choice into an
    empirical result.
  - **INTC — loud narrative, weak beta.** *Hypothesis:* the narrative is aspirational (Gaudi,
    foundry) rather than revenue-realised, so the market prices execution and government support
    instead. *Test:* does `δ_INTC` rise in windows following actual accelerator-revenue disclosure?
    Does a foundry/geopolitics proxy subsume it?
- Assign each divergence to **mispricing / missing channel / measurement failure**. That framework is
  the headline of the deck.

---

### C.6 Lead–lag design (Task 7) — design only, ~1 hour of writing

- **Left side:** monthly Δ in the shrunk index, decomposed into ΔS and ΔV. Use **innovations, not
  levels** — the residual from an AR(1) on the company's own index. Levels are highly persistent and
  will manufacture spurious lead–lag.
- **Right side:** monthly Δ in rolling `δ`. **Flag the overlapping-window problem:** rolling betas
  from overlapping windows are mechanically autocorrelated, which inflates t-stats. Fix with
  non-overlapping windows, Newey–West at lag ≥ window length, or a Kalman-filtered beta whose
  innovations are clean by construction. Naming this hazard unprompted is a strong signal.
- **Estimator:** panel local projection (Jordà) — `Δδ_{i,t+h}` on `ΔAIA_{i,t}` for h = 0…6 months,
  company fixed effects, **Driscoll–Kraay** SEs (cross-sectional dependence is severe here — every
  one of these names co-moves with the AI theme). **Run the reverse direction too**; the difference
  between the two impulse responses *is* the claim. Text→beta alone proves nothing if beta→text is
  just as strong.
- **Mechanisms, one per signal — specific, not "AI adoption":**
  - *Transcript AI-mention density + management guidance language* → analyst model revisions →
    multiple re-rating. Expected lead: 1–2 quarters.
  - *Supply-chain / customer-order news* (HBM qualification for MU, server ODM orders for DELL) →
    reported revenue → beta. Expected lead: 2–3 quarters.
  - *General news salience* → **expected to LAG price**, because media chases performance.
    Predicting this asymmetry in advance, and designing the test to detect it, is the single most
    credible thing in Task 7.
- **Power — give an actual number.** n=9, T≈45 → 405 observations nominally, but cross-sectional
  correlation among the tech names (ρ≈0.6) and serial correlation in both series cut effective
  observations to perhaps 40–60. At 80% power that supports detecting roughly a **0.4 SD**
  standardised effect and nothing smaller. **So: this design can detect a large lead–lag effect and
  is blind to a modest one, and it cannot distinguish a 1-month lead from a 2-month lead at all.**
  Then state the fix: widen to 200–500 names, and condition on earnings dates (event time) rather
  than calendar time. Being this blunt about what your own design *cannot* do is what they mean by
  "honest about statistical power."

---

### C.7 Sources log + scaling memo (Task 8)

**Sources log** — a CSV: `source | category (Primary/Secondary/Inferred) | access method | date range | n_docs | cost | known limitations`. Include the day-1 probe results — sources you *tested and rejected* belong here too, with the reason.

**Paid sources worth naming** (and *why each would materially help*, not just a list):
AlphaSense / Sentieo (transcripts + broker research full text), RavenPack (point-in-time,
entity-tagged news — fixes the single biggest bias in a GDELT corpus, which is retroactive link
rot), LSEG/Refinitiv news archive, FactSet transcripts, Visible Alpha (segment-level consensus —
would let you run the CAT E&T test properly), S&P Capital IQ.

**Scaling memo (half a page).** Three things, specific, no infrastructure wish-list:

1. **Corpus acquisition breaks first — not inference.** 405 GDELT calls for 9 names becomes ~2,000
   per refresh against a rate-limited endpoint with no SLA, and **entity disambiguation collapses at
   global scale**: "Apple" the company vs. the fruit, ticker `TEAM` vs. the English word, non-Latin
   names, and companies sharing names across jurisdictions. *Change:* licensed entity-tagged feed
   (RavenPack/LSEG) or GDELT GKG's `Organizations` field on BigQuery, resolved against a permanent
   identifier (LEI or PermID), never string matching.
2. **Per-document LLM classification stops being affordable.** 2,000 names × ~300 docs/month ≈
   600k documents/month. *Change:* **distil** — use the LLM once to label ~50k documents, fine-tune
   a small encoder (ModernBERT/DeBERTa) on those labels, and run that at effectively zero marginal
   cost. Reserve the LLM for the ambiguous band and a monthly drift audit (re-label a 500-doc sample,
   track F1 decay, retrain on breach). ~100× cheaper, small accuracy cost on a 3-class problem.
3. **Both normalisations stop being valid.** A 9-name z-score is meaningless across 2,000 global
   names — salience must be normalised **within sector × region × coverage-decile** buckets, or the
   index just measures "is this a US tech company." And per-name OLS betas across 2,000 names
   generate a fat tail of spurious significance — move to shrinkage (James–Stein toward the sector
   mean) or a proper multi-factor risk model.

**Which choices only work because n=9** — list them plainly: hand-picked factor legs; per-name sector
ETF controls; eyeballing divergences; 9-name z-scores; no entity disambiguation; a spot-reviewed
validation sample; bespoke per-company IR scrapers; scraping instead of licensing.

---

## Part D — Stretch items, per your call

| Item | In scope? | Why |
|---|---|---|
| **S&P 500 regression expansion** | **Yes** | Easiest of the three (~2 h: one bulk yfinance download + vectorized regressions) and the highest payoff. It gives the 9 names real percentile ranks and a genuine null distribution for "indistinguishable from zero," which makes the PG/WM sanity check quantitative instead of hand-wavy. Caveat to document: current membership → survivorship bias, so use it only for the null distribution, never for a tradeable claim. |
| **Point-in-time AI factor** | **Yes, lightweight** | ~1.5–2 h. Directly answers a hazard they name. Keep it simple: one entry date per basket name, derived from its first filing disclosing material AI/accelerator revenue, plus a one-quarter lag. Show the two beta rankings side by side. If the day-1 corpus probe goes badly, this is the **first thing to cut** — say so in the write-up. |
| **150-doc hand-labeled eval** | **No** — replaced | Substituted with cross-model κ + 40-doc spot review + 20-doc buzzword trap + name-masking test (§C.2). ~40 min instead of 90, and still satisfies "classification quality on a reviewed sample." State the substitution and the reason in the appendix. |
| **Lead–lag implementation** | **No** | The brief says design-only and that *"a well-reasoned design is worth more than a noisy chart."* Building it would be reading the brief badly. |

---

## Part E — Schedule (~16–18 hours)

The one scheduling insight that matters: **Part 2 is completely independent of Part 1.** Corpus jobs
and LLM batches run for hours unattended. Never sit watching them — the factor model is what you do
while they run.

| Slot | Hours | Work |
|---|---|---|
| **Evening 1** | 2 | Repo skeleton, universe/config. **The 45-min source probe — do this first.** Prices + FF factors downloaded and validated (finish this completely; it never blocks). |
| **Evening 2** | 2 | EDGAR + IR scrapers. Transcript decision (§C.1b). Kick the news harvest off in the background. |
| **Evening 3** | 2 | Dedup, corpus EDA, coverage-bias tables + heatmap. **Freeze the corpus** — no more sourcing after tonight, whatever you have. |
| **Evening 4** | 2 | **All of Part 2**: AI factor construction, the AIQ teardown, orthogonalization, regressions, rolling betas, sanity gate. |
| **Weekend day 1** | 5–6 | Prefilter + embeddings, launch the Batch classification run, then *while it runs*: validation suite (§C.2) and the S&P 500 expansion. Finish with index construction. |
| **Weekend day 2** | 5–6 | Reconciliation + scatter + divergences. Write the deck. Write the lead–lag design, scaling memo, sources log. README + repo tidy. |
| **Evening 5** | 1–2 | Buffer, token log, final read-through. |

**Hard rule: freeze the corpus after evening 3.** The brief warns corpus assembly will eat 40–50% of
the time and that they are grading *where you chose to spend it*. A corpus that keeps growing is the
classic way this case study fails.

---

## Part F — Budget (well inside £100)

| Item | Estimate |
|---|---|
| Embeddings (local `sentence-transformers`) | £0 |
| Haiku 4.5 bulk pass, ~3.5k docs, batched + cached | ~£3–5 |
| Sonnet 5 on the ambiguous band + transcript/filing passages | ~£10–15 |
| Validation runs (cross-model, masking, traps) | ~£2 |
| Transcript API (optional, §C.1b) | £0–30 |
| **Total** | **~£15–50** |

Log every run to `token_log.csv`: `task | model | n_calls | input_tok | output_tok | cached_tok | batch (y/n) | est_cost`. They ask for this explicitly, and it is trivially cheap to instrument if you wrap the client from the first call. Do it on day 1, not retroactively.

---

## Part G — Repo layout

```
ai-theme-association/
  README.md                  # setup + `make all`; polish not expected, clarity is
  Makefile
  requirements.txt
  config/
    universe.yaml            # 9 tickers + sector ETF map
    sources.yaml             # every endpoint, with the day-1 probe results
    taxonomy.yaml            # the classification schema
    ai_basket.yaml           # factor legs + point-in-time entry dates
  src/
    corpus/     gdelt.py  edgar.py  transcripts.py  ir_rss.py  hn.py  dedupe.py
    classify/   prefilter.py  embed.py  llm_classify.py  validate.py  prompts/
    index/      salience.py  valence.py  aia_index.py
    factor/     prices.py  ff_factors.py  ai_factor.py  regressions.py
    reconcile/  align.py  scatter.py  divergence.py
    utils/      cache.py  tokenlog.py
  data/  raw/ interim/ processed/     # gitignored; commit a small sample so it's inspectable
  notebooks/  01_corpus_eda  02_classifier_eval  03_factor  04_reconcile
  outputs/  figures/  tables/
  docs/  findings.pdf  appendix.md  sources_log.csv  scaling_memo.md  token_log.csv
```

Two repo details that read as senior: **cache every network call to disk keyed by request hash** (so
`make all` is idempotent and reviewable offline), and **commit a small sample of `data/processed`**
so a reviewer can see your schema without running anything.

---

## Part H — The deck (4–6 slides, conclusions first)

1. **Headline.** The ranked table — semantic score and AI beta side by side — and your one-sentence
   thesis. No methodology on this slide.
2. **Semantic signal.** The salience × valence 2×2 with all 9 names, plus the time series. One line
   on construction.
3. **Factor-implied exposure.** Beta table with confidence intervals, the NVDA/PG/WM sanity gate, and
   the AIQ teardown finding.
4. **Reconciliation.** The labeled scatter with quadrants and the ρ + CI caveat.
5. **Divergences.** Three cases, each tagged *mispricing / missing channel / measurement failure*,
   each with its falsifiable test.
6. *(optional)* **What I'd do next** — the two highest-value extensions, and what I deliberately
   didn't do and why.

Everything else — classifier diagnostics, regression tables, lead–lag design, sources log, scaling
memo, token log — goes in the appendix. They said not to put it in the main summary.

---

## Part I — Things worth writing down even when they cost you

The brief says a documented shortcut beats hours of undocumented work. Concretely, say these out
loud if they're true:

- "Transcripts are prepared-remarks only / SEC-substituted; I lose the analyst Q&A, which is where
  AI claims get pressure-tested."
- "My AI factor's first-stage R² on market+style+sector is 0.8x, so `δ` is estimated off a thin
  residual and the standard errors reflect that."
- "The pure-play basket is chosen with hindsight; here is the point-in-time variant and here is the
  rank correlation between the two."
- "My null names (PG, WM) came out at δ = x with SE = y. That's [clean / not clean], and here's what
  I think it means."
- "I spent N hours on the corpus and cut X to protect the reconciliation."

A candidate who says these things sounds like someone who has shipped a signal before. A candidate
with a clean-looking deck and no caveats sounds like someone who hasn't looked hard enough.

---

## Verification

Since implementation happens on your personal machine, "verification" here means the checks you
should be able to run and show:

1. `make all` reproduces every figure and table from cached data, offline.
2. **Price validation** passes: no gaps, NYSE row-count match, split continuity (NVDA June 2024).
3. **Factor sanity gate** passes: NVDA `δ` positive and significant; PG and WM within 1 SE of zero.
   Report the result whichever way it comes out.
4. **Classifier validation** produces: cross-model κ, a 40-doc spot-review confusion matrix, the
   buzzword-trap false-positive rate, and the masked-vs-unmasked valence correlation.
5. **Index sanity**: salience sums correctly, shrinkage reduces month-over-month variance, and the
   9-name z-scores are mean-zero per period by construction.
6. `token_log.csv` totals reconcile against your Anthropic Console usage page.

---

## Open questions for you

1. **Transcripts** — §C.1b lays out the three routes. My recommendation is SEC-first, then a
   60-minute timebox on a paid API, and only fall back to scraping. Your call on whether to spend
   the ~£30.
2. **News backbone** — the day-1 probe decides this. If GDELT's DOC API turns out to be shallow for
   early 2023, are you willing to set up a GCP project for the BigQuery fallback? If not, we drop to
   a shorter effective news window (say mid-2024 →) and document the truncation, keeping the full
   Jan-2023 window only for the SEC/IR primary sources. That is a legitimate, documentable shortcut —
   but it's better to decide it deliberately than to discover it at 11pm on the Saturday.
