"""
app/cache/graph_cache.py

Cache for extracted/pruned graph slices keyed by role + gap hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Any
from collections.abc import Mapping

try:
    from utils.hash_utils import canonical_json, make_cache_key
except ImportError:  # pragma: no cover - alternate package root
    from app.utils.hash_utils import canonical_json, make_cache_key


TTL_SECONDS = 24 * 60 * 60  # 24h


@dataclass
class _Entry:
    value_json: str
    expires_at: float


_LOCK = Lock()
_STORE: dict[str, _Entry] = {}


def get(role: str | None, gap_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    key = _key(role, gap_payload)
    now = time()
    with _LOCK:
        entry = _STORE.get(key)
        if entry is None:
            return None
        if entry.expires_at < now:
            _STORE.pop(key, None)
            return None
        import json

        return json.loads(entry.value_json)


def set(
    role: str | None,
    gap_payload: Mapping[str, Any],
    graph_payload: Mapping[str, Any],
    *,
    ttl_seconds: int = TTL_SECONDS,
) -> None:
    key = _key(role, gap_payload)
    import json

    payload_json = json.dumps(dict(graph_payload), sort_keys=True, separators=(",", ":"))
    expiry = time() + max(1, int(ttl_seconds))
    with _LOCK:
        _STORE[key] = _Entry(value_json=payload_json, expires_at=expiry)


def delete(role: str | None, gap_payload: Mapping[str, Any]) -> bool:
    key = _key(role, gap_payload)
    with _LOCK:
        return _STORE.pop(key, None) is not None


def clear() -> int:
    with _LOCK:
        count = len(_STORE)
        _STORE.clear()
    return count


def _key(role: str | None, gap_payload: Mapping[str, Any]) -> str:
    role_key = (role or "default").strip().lower() or "default"
    gap_key = make_cache_key("gap", canonical_json(dict(gap_payload)), length=24)
    return f"graph:{role_key}:{gap_key}"


__all__ = ["get", "set", "delete", "clear", "TTL_SECONDS"]
