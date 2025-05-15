import json
import os
import time
from typing import Any, Optional

CACHE_FILE = "brave_search_cache.json"
CACHE_TTL = 86400  # 24 ore in secondi

def _load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_cached_result(query: str) -> Optional[Any]:
    cache = _load_cache()
    entry = cache.get(query)
    if entry:
        timestamp, result = entry
        if time.time() - timestamp < CACHE_TTL:
            return result
    return None

def set_cached_result(query: str, result: Any):
    cache = _load_cache()
    cache[query] = [time.time(), result]
    _save_cache(cache)
