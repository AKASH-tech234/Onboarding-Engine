"""
app/db/repositories/pathway_repo.py

Repository for pathway payloads, phases, and items.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4
from collections.abc import Mapping, Sequence

try:
    from app.adaptive.db.supabase_client import get_client
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.db.supabase_client import get_client


_LOCK = Lock()
_PATHWAYS: dict[str, dict[str, Any]] = {}
_PHASES: dict[str, list[dict[str, Any]]] = {}
_ITEMS: dict[str, list[dict[str, Any]]] = {}


def save_pathway(payload: Mapping[str, Any], *, pathway_id: str | None = None) -> dict[str, Any]:
    resolved_id = pathway_id or _id_from(payload, keys=("pathway_id", "id"))
    now = _utc_now()
    row = {
        **dict(payload),
        "pathway_id": resolved_id,
        "id": resolved_id,
        "updated_at": now,
        "created_at": payload.get("created_at", now),
    }
    with _LOCK:
        _PATHWAYS[resolved_id] = row

    _try_db_insert("pathways", row)
    return dict(row)


def get_pathway(pathway_id: str) -> dict[str, Any] | None:
    with _LOCK:
        row = _PATHWAYS.get(pathway_id)
        if row is None:
            return None
        output = dict(row)
        output["phases"] = [dict(item) for item in _PHASES.get(pathway_id, [])]
        output["items"] = [dict(item) for item in _ITEMS.get(pathway_id, [])]
        return output


def save_phases(pathway_id: str, phases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for phase in phases:
        phase_number = int(phase.get("phase_number", len(normalized) + 1))
        normalized.append(
            {
                **dict(phase),
                "pathway_id": pathway_id,
                "phase_number": phase_number,
                "updated_at": _utc_now(),
            }
        )

    with _LOCK:
        _PHASES[pathway_id] = normalized

    _try_db_insert("pathway_phases", {"pathway_id": pathway_id, "phases": normalized})
    return [dict(item) for item in normalized]


def save_items(pathway_id: str, items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        normalized.append(
            {
                **dict(item),
                "pathway_id": pathway_id,
                "sort_index": int(item.get("sort_index", index)),
                "updated_at": _utc_now(),
            }
        )

    with _LOCK:
        _ITEMS[pathway_id] = normalized

    _try_db_insert("pathway_items", {"pathway_id": pathway_id, "items": normalized})
    return [dict(item) for item in normalized]


def reset_for_tests() -> None:
    with _LOCK:
        _PATHWAYS.clear()
        _PHASES.clear()
        _ITEMS.clear()


def _id_from(payload: Mapping[str, Any], *, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return str(uuid4())


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


__all__ = [
    "save_pathway",
    "get_pathway",
    "save_phases",
    "save_items",
    "reset_for_tests",
]


