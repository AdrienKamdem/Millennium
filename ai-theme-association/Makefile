.PHONY: help probe prices corpus classify index factor reconcile all clean-cache

PY := python -m

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

probe:       ## Evening 1: test which sources actually reach Jan 2023. Writes config/sources.yaml.
	$(PY) scripts.probe_sources

prices:      ## Download + validate prices and Fama-French factors. No corpus dependency.
	$(PY) src.factor.prices
	$(PY) src.factor.ff_factors

corpus:      ## Fetch, parse, dedupe the text corpus. Network-heavy; run in background.
	$(PY) src.corpus.build

classify:    ## Prefilter -> embeddings -> LLM classification + aspect sentiment. Costs money.
	$(PY) src.classify.prefilter
	$(PY) src.classify.embed
	$(PY) src.classify.llm_classify

validate:    ## Classifier diagnostics: cross-model agreement, spot review, buzzword trap, name masking.
	$(PY) src.classify.validate

index:       ## Build the AI-association index from classified documents.
	$(PY) src.index.aia_index

factor:      ## Construct the AI factor, orthogonalize, run regressions, read betas.
	$(PY) src.factor.ai_factor
	$(PY) src.factor.regressions

reconcile:   ## Align both signals, scatter, divergence analysis.
	$(PY) src.reconcile.align
	$(PY) src.reconcile.scatter
	$(PY) src.reconcile.divergence

all: prices corpus classify index factor reconcile   ## Full pipeline. Runs from cache; no network needed.

clean-cache: ## Delete cached network responses. You almost never want this.
	rm -rf data/raw/* data/interim/*

edgar:        ## Verify EDGAR retrieval chain (5 min). Run before Tuesday.
	$(PY) scripts.probe_edgar
