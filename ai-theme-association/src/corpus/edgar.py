"""SEC EDGAR. Primary disclosure -- the reliable half of the corpus.

Design decisions:

NO ITEM-BOUNDARY PARSING. The obvious approach is to split 10-Ks into Item 1 /
1A / 7 and analyse those. Item headers are inconsistent across filers and years,
and the regex work is a reliable evening-killer. Instead: take the full filing
text and extract every PARAGRAPH containing an AI keyword. Same signal, none of
the parsing risk, and it degrades gracefully -- a weird filing yields fewer
paragraphs rather than a silent empty Item.

8-K FILTERING BY ITEM CODE, not by scanning for EX-99. Most 8-Ks are not earnings
releases (they cover director changes, debt issuance, etc). Item 2.02 is "Results
of Operations and Financial Condition", so filter on that and you get the earnings
releases directly.

WHY THIS MATTERS BEYOND VOLUME: Item 1A risk-factor language is the strongest
negative-valence signal available anywhere in the corpus. If ADBE or TEAM added
AI-as-competitive-threat language over the window, that is the company itself
disclosing a headwind -- which news coverage systematically softens.

    python -m src.corpus.edgar --sample     # NVDA only
    python -m src.corpus.edgar              # all 9, ~10 min
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
import sys
import warnings

import pandas as pd
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

from src.utils import config
from src.utils.cache import cached_get

log = logging.getLogger(__name__)

SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
MIN_INTERVAL = 0.15          # SEC caps at 10 req/s; stay well under
FORMS = ("10-K", "10-Q", "8-K")
EARNINGS_ITEM = "2.02"       # Results of Operations and Financial Condition

# Word-boundary matching: a bare "AI" substring matches Air, AIG, Dubai, Shanghai.
AI_PATTERN = re.compile(
    r"\b(artificial intelligence|machine learning|deep learning|neural network|"
    r"large language model|generative|foundation model|transformer model|"
    r"inference|accelerator|copilot|agentic|LLM|GPU|NPU|TPU|HBM)\b"
    r"|\bAI\b|\bA\.I\.",
    re.IGNORECASE,
)


def _hdr() -> dict:
    return config.sec_headers()


def _doc_id(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def list_filings(cik: str, since: str, forms: tuple[str, ...] = FORMS) -> pd.DataFrame:
    """Filing index for one company.

    `recent` caps at ~1000 filings; anything older lives in separate files under
    filings.files. For a window starting 2023 `recent` is almost always enough,
    but page through if it is not -- and warn rather than silently truncating.
    """
    data = cached_get("edgar", SUBMISSIONS.format(cik=cik), headers=_hdr(),
                      parse="json", min_interval=MIN_INTERVAL)
    rec = data["filings"]["recent"]
    df = pd.DataFrame({
        "form": rec["form"],
        "filing_date": rec["filingDate"],
        "accession": rec["accessionNumber"],
        "primary_doc": rec["primaryDocument"],
        "items": rec.get("items", [""] * len(rec["form"])),
    })

    oldest = df["filing_date"].min()
    if oldest > since:
        log.warning("CIK %s: 'recent' only reaches %s but window starts %s. "
                    "Page through filings.files for the remainder.", cik, oldest, since)

    return df[(df["filing_date"] >= since) & (df["form"].isin(forms))].reset_index(drop=True)


# Modern filings are inline XBRL: the HTML carries a large machine-readable header
# and hidden fact blocks that are not prose. Left in, they swamp the real text with
# things like "P3Y P5Y 0001045810 iso4217:USD xbrli:shares".
IX_HEADER = re.compile(r"<ix:header.*?</ix:header>", re.IGNORECASE | re.DOTALL)
HIDDEN = re.compile(r"display:\s*none", re.IGNORECASE)


def fetch_text(cik: str, accession: str, document: str) -> str:
    """Download one filing document and strip it to plain text.

    Two things matter here and both were wrong first time round:
      1. Remove the inline-XBRL header and display:none blocks BEFORE parsing.
      2. Join with newlines, not spaces. get_text(" ") collapses every block
         boundary, leaving one giant blob with no paragraph structure to split on.
    """
    url = f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/{document}"
    raw = cached_get("edgar", url, headers=_hdr(), parse="text", min_interval=MIN_INTERVAL)

    raw = IX_HEADER.sub(" ", raw)
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style", "table"]):
        tag.decompose()                      # tables are numeric, never prose
    for tag in soup.find_all(style=HIDDEN):
        tag.decompose()

    text = soup.get_text("\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return re.sub(r"\n{2,}", "\n\n", text)


# Exhibit filenames are filer-specific and do NOT reliably contain "ex-99".
# NVDA names them q2fy27pr.htm / q2fy27cfocommentary.htm. Rather than guess at
# naming conventions, exclude the scaffolding: in a filing already filtered to
# item 2.02 (Results of Operations), whatever .htm remains IS earnings material.
SCAFFOLD = re.compile(
    r"(-index|index-headers|FilingSummary|MetaLinks|^R\d+\.htm|Show\.js|report\.css)",
    re.IGNORECASE)
DOC_EXT = (".htm", ".html")


def find_exhibits(cik: str, accession: str, primary_doc: str) -> list[str]:
    """Candidate exhibit documents inside a filing directory."""
    url = f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/index.json"
    try:
        items = cached_get("edgar", url, headers=_hdr(), parse="json",
                           min_interval=MIN_INTERVAL)["directory"]["item"]
    except Exception as e:
        log.warning("index.json failed for %s: %s", accession, e)
        return []

    out = []
    for name in (i["name"] for i in items):
        if not name.lower().endswith(DOC_EXT):
            continue
        if name == primary_doc or SCAFFOLD.search(name):
            continue
        out.append(name)
    return out


def _is_prose(p: str, min_chars: int) -> bool:
    """Reject XBRL residue, table fragments and numeric noise.

    Filing text is full of things that look like paragraphs but are not sentences.
    A high digit ratio or too few words is a reliable tell.
    """
    if len(p) < min_chars:
        return False
    if len(p.split()) < 30:
        return False
    if sum(c.isdigit() for c in p) / len(p) > 0.15:
        return False
    return p.count(".") >= 1


def extract_ai_paragraphs(text: str, min_chars: int = 200, max_chars: int = 2500) -> list[str]:
    """Every prose paragraph mentioning AI. Replaces Item-boundary parsing."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z])", text) if p.strip()]
    return [p[:max_chars] for p in paras
            if _is_prose(p, min_chars) and AI_PATTERN.search(p)]


def harvest_company(ticker: str, cik: str, since: str) -> list[dict]:
    filings = list_filings(cik, since)
    if filings.empty:
        log.warning("%s: no filings in window", ticker)
        return []

    rows = []
    for _, f in filings.iterrows():
        is_8k = f["form"] == "8-K"
        # Only earnings 8-Ks are worth fetching; the rest are director changes etc.
        if is_8k and EARNINGS_ITEM not in str(f["items"]):
            continue

        if is_8k:
            docs = [(d, "8-K/exhibit") for d in
                    find_exhibits(cik, f["accession"], f["primary_doc"])]
        else:
            docs = [(f["primary_doc"], f["form"])]
        if not docs:
            continue

        paras, subtype, document = [], docs[0][1], docs[0][0]
        for document, subtype in docs:
            try:
                text = fetch_text(cik, f["accession"], document)
            except Exception as e:
                log.warning("%s %s %s: %s", ticker, f["form"], f["filing_date"], e)
                continue
            paras.extend(extract_ai_paragraphs(text))

        for i, p in enumerate(paras):
            rows.append({
                "doc_id": _doc_id(f["accession"] + str(i)),
                "ticker": ticker,
                "date": pd.to_datetime(f["filing_date"], utc=True),
                "title": f"{subtype} {f['filing_date']} para {i + 1}",
                "text": p,
                "url": f"{ARCHIVES}/{int(cik)}/{f['accession'].replace('-', '')}/{document}",
                "domain": "sec.gov",
                "source_category": "sec_filing",
                "form": subtype,
                "n_ai_paragraphs_in_filing": len(paras),
                "filing_chars": len(text),
            })
        log.info("%s %s %s: %d AI paragraphs / %d chars",
                 ticker, subtype, f["filing_date"], len(paras), len(text))
    return rows


def harvest(sample: bool = False) -> pd.DataFrame:
    since, _ = config.window()
    companies = config.universe()
    if sample:
        companies = [c for c in companies if c["ticker"] == "NVDA"]
        print("SAMPLE MODE: NVDA only")

    rows = []
    for c in companies:
        if not c.get("cik"):
            print(f"  {c['ticker']:5} SKIPPED -- no cik in universe.yaml")
            continue
        got = harvest_company(c["ticker"], c["cik"], since)
        rows.extend(got)
        print(f"  {c['ticker']:5} {len(got):5,} AI paragraphs", flush=True)

    df = pd.DataFrame(rows)
    if df.empty:
        print("NO ROWS -- run `make edgar` to diagnose the retrieval chain.")
        return df

    out = "data/processed/edgar_raw.parquet"
    df.to_parquet(out, index=False)
    print(f"\nwrote {out}  ({len(df):,} paragraphs)")
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="NVDA only")
    args = ap.parse_args()

    df = harvest(sample=args.sample)
    if df.empty:
        return 1

    print("\nAI paragraphs by form:")
    print(df["form"].value_counts().to_string())
    print("\nBy company by year:")
    d = df.copy()
    d["year"] = d["date"].dt.year
    print(d.pivot_table(index="year", columns="ticker", values="doc_id",
                        aggfunc="count", fill_value=0).to_string())
    print("\nSample paragraph:")
    print(" ", df.iloc[0]["text"][:400].replace("\n", " "), "...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
