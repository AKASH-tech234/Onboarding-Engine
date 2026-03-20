"""
app/cache/pathway_cache.py

Cache for generated pathway payloads keyed by analysis/job identifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Any
from collections.abc import Mapping


TTL_SECONDS = 60 * 60  # 1 hour


@dataclass
class _Entry:
    value: dict[str, Any]
    expires_at: float


_LOCK = Lock()
_STORE: dict[str, _Entry] = {}


def get(key: str) -> dict[str, Any] | None:
    cache_key = _normalize_key(key)
    now = time()
    with _LOCK:
        entry = _STORE.get(cache_key)
        if entry is None:
            return None
        if entry.expires_at < now:
            _STORE.pop(cache_key, None)
            return None
        return dict(entry.value)


def set(key: str, pathway: Mapping[str, Any], *, ttl_seconds: int = TTL_SECONDS) -> None:
    cache_key = _normalize_key(key)
    expiry = time() + max(1, int(ttl_seconds))
    with _LOCK:
        _STORE[cache_key] = _Entry(value=dict(pathway), expires_at=expiry)


def delete(key: str) -> bool:
    cache_key = _normalize_key(key)
    with _LOCK:
        return _STORE.pop(cache_key, None) is not None


def clear() -> int:
    with _LOCK:
        count = len(_STORE)
        _STORE.clear()
    return count


def _normalize_key(value: str) -> str:
    text = str(value).strip()
    return text if text else "default"


__all__ = ["get", "set", "delete", "clear", "TTL_SECONDS"]
