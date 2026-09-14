"""Disk cache for network responses, keyed by request hash.

Every external fetch goes through here. Two reasons:

1. `make all` becomes reproducible offline. A reviewer can regenerate every figure
   from the committed cache without a network connection or an API key.
2. A harvest that dies halfway costs nothing. Re-running resumes rather than
   restarting, which matters when the GDELT sweep is 405 sequential calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

import requests

log = logging.getLogger(__name__)

CACHE_ROOT = Path(__file__).resolve().parents[2] / "data" / "raw"


def _key(url: str, params: dict | None) -> str:
    """Stable hash of a request. Params are sorted so dict ordering cannot change the key."""
    blob = url + json.dumps(params or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def cached_get(
    source: str,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    *,
    parse: str = "json",
    min_interval: float = 0.0,
    force: bool = False,
) -> Any:
    """GET `url`, returning the cached response if one exists.

    Args:
        source: subdirectory under data/raw/ — one per upstream (gdelt, edgar, ...).
        parse: "json" or "text".
        min_interval: seconds to sleep after a live fetch. Use to respect rate limits
            (SEC caps at 10 req/s; be far more conservative with GDELT, which
            publishes no limit and will simply stop answering).
        force: bypass the cache and refetch.

    Returns:
        Parsed response body.
    """
    path = CACHE_ROOT / source / f"{_key(url, params)}.{'json' if parse == 'json' else 'txt'}"

    if path.exists() and not force:
        text = path.read_text()
        return json.loads(text) if parse == "json" else text

    log.info("fetch %s %s", url, params or "")
    resp = requests.get(url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text)

    if min_interval:
        time.sleep(min_interval)

    return resp.json() if parse == "json" else resp.text


def cached_call(source: str, key: str, fn: Callable[[], Any], *, force: bool = False) -> Any:
    """Cache an arbitrary expensive call (e.g. a BigQuery extract) under an explicit key."""
    path = CACHE_ROOT / source / f"{key}.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    result = fn()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result))
    return result
