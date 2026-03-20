"""
app/db/repositories/resources_repo.py

Resource persistence and lookup repository.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4
from collections.abc import Mapping

try:
    from db.supabase_client import get_client
except ImportError:  # pragma: no cover - alternate package root
    from app.db.supabase_client import get_client


_LOCK = Lock()
_RESOURCES: dict[str, dict[str, Any]] = {}


def upsert_resource(resource: Mapping[str, Any]) -> dict[str, Any]:
    resource_id = _resource_id(resource)
    now = _utc_now()

    row = {
        **dict(resource),
        "id": resource_id,
        "resource_id": resource_id,
        "updated_at": now,
        "created_at": resource.get("created_at", now),
    }

    with _LOCK:
        _RESOURCES[resource_id] = row

    _try_db_insert("resources", row)
    return dict(row)


def get_resources_for_skill(skill_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    normalized_skill = str(skill_id).strip().lower()
    safe_limit = max(1, min(200, int(limit)))

    with _LOCK:
        matches = [
            dict(row)
            for row in _RESOURCES.values()
            if str(row.get("skill_id", "")).strip().lower() == normalized_skill
        ]

    matches.sort(key=lambda row: float(row.get("score", row.get("quality", 0.0))), reverse=True)
    return matches[:safe_limit]


def reset_for_tests() -> None:
    with _LOCK:
        _RESOURCES.clear()


def _resource_id(payload: Mapping[str, Any]) -> str:
    value = payload.get("id", payload.get("resource_id"))
    text = str(value).strip() if value is not None else ""
    return text or str(uuid4())


def _try_db_insert(table_name: str, payload: Mapping[str, Any]) -> None:
    try:
        client = get_client()
        table = _table(client, table_name)
        if table is None:
            return
        result = table.insert(dict(payload))
        execute = getattr(result, "execute", None)
        if callable(execute):
            execute()
    except Exception:
        return


def _table(client: Any, table_name: str):
    if client is None:
        return None
    if hasattr(client, "table"):
        return client.table(table_name)
    if hasattr(client, "from_"):
        return client.from_(table_name)
    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["upsert_resource", "get_resources_for_skill", "reset_for_tests"]
