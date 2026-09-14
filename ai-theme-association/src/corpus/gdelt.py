"""GDELT news harvest.

Design decisions worth being able to defend in an interview:

WEEKLY SLICES, not monthly. The DOC API caps at maxrecords=250. The probe showed
Atlassian -- one of the thinnest names -- returning 62 articles in a single week,
so a monthly slice would hit the cap even for small names, and NVDA would blow
through it many times over. A capped query does not return a random 250; it
returns whatever GDELT ranks first. If that ordering correlates with AI-ness, the
denominator (total coverage) is truncated harder than the numerator (AI coverage),
inflating salience -- and inflating it MORE for high-volume names. That is a bias
differential across the cross-section, which does not cancel in a z-score and
would manufacture exactly the ranking you would naively expect. Weekly slicing
keeps cells under the cap so the question never arises.

6-SECOND SPACING. GDELT enforces 1 request / 5 seconds with HTTP 429. 6s gives
margin. ~196 weeks x 9 names = ~1,760 requests = ~3 hours. Run it overnight.

RESUMABLE. Every slice is cached by request hash, so a crash resumes rather than
restarts. Re-running costs nothing.

    python -m src.corpus.gdelt --sample     # 1 company, 3 weeks -- verify first
    python -m src.corpus.gdelt              # full harvest, ~3 hours
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import logging
import random
import sys
import time
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import requests

from src.utils import config
from src.utils.cache import cached_get

log = logging.getLogger(__name__)

ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
MAXRECORDS = 250
MIN_INTERVAL = 6.0
MAX_RETRIES = 3
FAIL_LIMIT = 5      # consecutive slice failures before aborting

TRACKING = ("utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "fbclid", "gclid", "mc_cid", "mc_eid")


def canonical_url(url: str) -> str:
    """Strip tracking params and fragments so the same article hashes identically."""
    try:
        p = urlsplit(url)
        q = "&".join(kv for kv in p.query.split("&")
                     if kv and kv.split("=")[0].lower() not in TRACKING)
        return urlunsplit((p.scheme, p.netloc, p.path, q, ""))
    except Exception:
        return url


def doc_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:16]


def build_query(aliases: list[str]) -> str:
    """Quoted phrases OR'd together, English only.

    Aliases define the DENOMINATOR of every salience score, so a bad one is far
    more damaging than a missed AI article. See config/universe.yaml for the
    per-name traps: "intel" the common noun, "micron" the unit of length,
    "waste management" the industry phrase.
    """
    quoted = ['"%s"' % a for a in aliases]        # avoid nested f-string quoting (py<=3.11)
    return "(%s) sourcelang:english" % " OR ".join(quoted)


def week_slices(start: str, end: str, per_quarter: int | None = None,
                seed: int = 42) -> list[tuple[dt.date, dt.date]]:
    """All weeks in the window, or a random sample of `per_quarter` weeks per quarter.

    Sampling WEEKS is the right lever, not sampling documents. Harvest cost is per
    REQUEST, not per document: one call returns up to 250 articles and costs the
    same 6s whether you keep 5 of them or all 250. Dropping documents saves nothing;
    dropping weeks cuts the job proportionally.

    Within a sampled week you keep everything, so coverage inside that week is
    complete and the AI share computed over sampled weeks is an unbiased estimate
    of the quarter's share. Fixed seed so the harvest is reproducible.
    """
    d0 = dt.date.fromisoformat(start)
    d1 = min(dt.date.fromisoformat(end), dt.date.today())
    out, cur = [], d0
    while cur < d1:
        nxt = min(cur + dt.timedelta(days=7), d1)
        out.append((cur, nxt))
        cur = nxt
    if not per_quarter:
        return out

    rng = random.Random(seed)
    by_q: dict[tuple[int, int], list] = {}
    for lo, hi in out:
        by_q.setdefault((lo.year, (lo.month - 1) // 3 + 1), []).append((lo, hi))
    sampled = []
    for q in sorted(by_q):
        weeks = by_q[q]
        sampled.extend(sorted(rng.sample(weeks, min(per_quarter, len(weeks)))))
    return sampled


def _stamp(d: dt.date) -> str:
    return d.strftime("%Y%m%d%H%M%S")


def fetch_slice(ticker: str, aliases: list[str], lo: dt.date, hi: dt.date) -> list[dict]:
    """One company, one week. Cached; retries on 429 with backoff."""
    params = {
        "query": build_query(aliases),
        "mode": "ArtList",
        "maxrecords": MAXRECORDS,
        "format": "json",
        "startdatetime": _stamp(lo),
        "enddatetime": _stamp(hi),
    }

    payload = None
    for attempt in range(MAX_RETRIES):
        try:
            payload = cached_get("gdelt", ENDPOINT, params,
                                 parse="json", min_interval=MIN_INTERVAL)
            break
        except (ValueError, requests.HTTPError) as e:
            # GDELT returns its throttle notice as an HTTP 429 with a PLAINTEXT
            # body, so both exception types mean the same thing here.
            code = getattr(getattr(e, "response", None), "status_code", None)
            if isinstance(e, requests.HTTPError) and code not in (429, None, 503):
                log.error("%s %s HTTP %s", ticker, lo, code)
                return None
            wait = min(MIN_INTERVAL * 2 ** attempt, 60)
            log.warning("%s %s throttled (%s), retry in %.0fs", ticker, lo, code or "non-JSON", wait)
            time.sleep(wait)
    if payload is None:
        return None   # None = FAILED (distinct from [] = genuinely no articles)

    arts = payload.get("articles", []) if isinstance(payload, dict) else []
    rows = []
    for a in arts:
        url = a.get("url", "")
        if not url:
            continue
        rows.append({
            "doc_id": doc_id(url),
            "ticker": ticker,
            "date": pd.to_datetime(str(a.get("seendate", "")), errors="coerce", utc=True),
            "title": (a.get("title") or "").strip(),
            "url": canonical_url(url),
            "domain": a.get("domain", ""),
            "country": a.get("sourcecountry", ""),
            "source_category": "news",
            "slice_start": lo.isoformat(),
            # GDELT's own tone: a free second opinion to compare LLM valence
            # against. A large divergence is worth a line in the appendix.
            "gdelt_tone": a.get("tone"),
        })

    if len(arts) >= MAXRECORDS:
        log.warning("%s %s HIT THE %d CAP -- cell truncated", ticker, lo, MAXRECORDS)
    return rows


def harvest(sample: bool = False, weeks_per_quarter: int | None = None) -> pd.DataFrame:
    start, end = config.window()
    companies = config.universe()
    slices = week_slices(start, end, per_quarter=weeks_per_quarter)

    if sample:
        companies = [c for c in companies if c["ticker"] == "TEAM"]
        slices = slices[:3]
        print(f"SAMPLE MODE: {len(companies)} company x {len(slices)} weeks")

    total = len(companies) * len(slices)
    print(f"{total} slices, ~{total * MIN_INTERVAL / 60:.0f} min if nothing cached. "
          f"Cached slices are free.")

    rows, done, capped, consecutive_fail, total_fail = [], 0, 0, 0, 0
    for c in companies:
        got = 0
        for lo, hi in slices:
            batch = fetch_slice(c["ticker"], c["aliases"], lo, hi)

            if batch is None:
                consecutive_fail += 1
                total_fail += 1
                if consecutive_fail >= FAIL_LIMIT:
                    print(f"\nABORTED: {FAIL_LIMIT} consecutive slices failed.")
                    print("GDELT rate-limits per IP. Sustained 429s despite correct spacing")
                    print("usually means a SHARED EGRESS IP (corporate NAT/VPN) that is already")
                    print("over quota. Verify with one request from a different network:")
                    print("  curl -s -o /dev/null -w '%{http_code}\\n' \\")
                    print("    'https://api.gdeltproject.org/api/v2/doc/doc?query=test&mode=ArtList&format=json'")
                    print(f"Cached slices are kept -- rerunning resumes from here. "
                          f"{len(rows):,} rows salvaged so far.")
                    raise SystemExit(2)
                continue

            consecutive_fail = 0
            capped += len(batch) >= MAXRECORDS
            rows.extend(batch)
            got += len(batch)
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{total} slices, {len(rows):,} rows", flush=True)
        print(f"  {c['ticker']:5} {got:6,} articles", flush=True)
    if total_fail:
        print(f"NOTE: {total_fail} slices failed and were skipped -- record this in sources.yaml.")

    df = pd.DataFrame(rows)
    if df.empty:
        print("NO ROWS -- check aliases and the probe result before rerunning.")
        return df

    before = len(df)
    df = df.drop_duplicates(subset=["doc_id", "ticker"])
    print(f"\n{before:,} rows -> {len(df):,} after exact-URL dedup "
          f"(near-duplicate titles handled in dedupe.py)")
    if capped:
        print(f"WARNING: {capped} slices hit the {MAXRECORDS} cap and are truncated. "
              f"Those cells' salience is biased upward -- slice finer or document it.")

    out = "data/processed/gdelt_raw.parquet"
    df.to_parquet(out, index=False)
    print(f"wrote {out}")
    return df


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Articles per company per quarter. Your first look at coverage bias."""
    d = df.dropna(subset=["date"]).copy()
    d["quarter"] = d["date"].dt.to_period("Q")
    return d.pivot_table(index="quarter", columns="ticker", values="doc_id",
                         aggfunc="count", fill_value=0)


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="1 company, 3 weeks")
    ap.add_argument("--weeks-per-quarter", type=int, default=None, metavar="N",
                    help="Randomly sample N weeks per quarter instead of all 13. "
                         "N=4 cuts the job from ~1750 requests to ~540.")
    args = ap.parse_args()

    df = harvest(sample=args.sample, weeks_per_quarter=args.weeks_per_quarter)
    if df.empty:
        return 1
    print("\nArticles per company per quarter:")
    print(coverage(df).to_string())
    print("\nTop domains:")
    print(df["domain"].value_counts().head(12).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
