"""
app/cache/normalization_cache.py

Cache for raw-skill -> canonical-skill normalization results.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Any
from collections.abc import Mapping

try:
    from utils.hash_utils import make_cache_key
except ImportError:  # pragma: no cover - alternate package root
    from app.utils.hash_utils import make_cache_key


TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


@dataclass
class _Entry:
    value: dict[str, Any]
    expires_at: float


_LOCK = Lock()
_STORE: dict[str, _Entry] = {}


def get(raw_skill: str) -> dict[str, Any] | None:
    key = _key(raw_skill)
    now = time()
    with _LOCK:
        entry = _STORE.get(key)
        if entry is None:
            return None
        if entry.expires_at < now:
            _STORE.pop(key, None)
            return None
        return dict(entry.value)


def set(raw_skill: str, normalized: Mapping[str, Any], *, ttl_seconds: int = TTL_SECONDS) -> None:
    key = _key(raw_skill)
    expiry = time() + max(1, int(ttl_seconds))
    with _LOCK:
        _STORE[key] = _Entry(value=dict(normalized), expires_at=expiry)


def delete(raw_skill: str) -> bool:
    key = _key(raw_skill)
    with _LOCK:
        return _STORE.pop(key, None) is not None


def clear() -> int:
    with _LOCK:
        count = len(_STORE)
        _STORE.clear()
    return count


def _key(raw_skill: str) -> str:
    return make_cache_key("norm", raw_skill.strip().lower(), length=24)


__all__ = ["get", "set", "delete", "clear", "TTL_SECONDS"]
