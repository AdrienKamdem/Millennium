# Classification + aspect-sentiment prompt (v1)

Version this file. When the rubric changes, bump to v2 and keep v1 — the appendix
should be able to say which prompt produced which numbers.

This text is the CACHED PREFIX on every call. Keep it byte-stable; any edit
invalidates the cache for the whole run. Put the per-document content strictly
after it.

---

## System

You are classifying a single document for its relevance to the AI theme in
relation to one specific company, and scoring the direction of AI's impact on
that company.

Judge **only from the text provided**. Do not use anything you know about the
company from outside this document. [This clause matters: without it the model
answers from its own knowledge of who won, which is a look-ahead leak dressed as
sentiment. The name-masking test in validate.py checks whether it worked.]

[Insert the taxonomy from config/taxonomy.yaml here — ai_relevance, ai_role,
materiality, valence_ai — with the full anchor definitions, not just the labels.]

Key distinction for `valence_ai`: score AI's impact **on this company**, not the
document's overall tone and not whether AI in general sounds promising. Coverage
can be enthusiastic about generative AI while being bearish on the company,
because the same technology threatens its business. Those are different signs.

Return JSON only, conforming to the schema. `evidence_span` must be an exact quote
from the document — if you cannot quote something that justifies the call, the
answer is `ai_relevance: none`.

## User

Company: {company_name} ({ticker})
Date: {date}
Source type: {source_category}

---
{text}
---
