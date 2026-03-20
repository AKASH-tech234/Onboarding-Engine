"""
app/utils/hash_utils.py

Deterministic hashing helpers for cache keys and idempotency keys.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from collections.abc import Mapping, Sequence


def stable_hash(value: Any, *, length: int = 16) -> str:
    """
    Return a deterministic hex digest for arbitrary JSON-serializable content.
    """
    canonical = canonical_json(value)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if length <= 0:
        return digest
    return digest[:length]


def canonical_json(value: Any) -> str:
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def make_cache_key(namespace: str, value: Any, *, length: int = 16) -> str:
    safe_namespace = namespace.strip().lower().replace(" ", "_") or "default"
    return f"{safe_namespace}:{stable_hash(value, length=length)}"


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalize(item) for item in value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump())
    if hasattr(value, "dict"):
        return _normalize(value.dict())
    if hasattr(value, "__dict__"):
        return _normalize(vars(value))
    return str(value)


__all__ = ["stable_hash", "canonical_json", "make_cache_key"]
