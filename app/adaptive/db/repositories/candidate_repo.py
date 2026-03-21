"""
app/db/repositories/candidate_repo.py

Candidate persistence repository.
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
_CANDIDATES: dict[str, dict[str, Any]] = {}
_CANDIDATE_SKILLS: dict[str, list[dict[str, Any]]] = {}


def upsert_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _candidate_id(candidate)
    now = _utc_now()

    with _LOCK:
        current = _CANDIDATES.get(candidate_id, {})
        merged = {
            **current,
            **dict(candidate),
            "id": candidate_id,
            "updated_at": now,
            "created_at": current.get("created_at", now),
        }
        _CANDIDATES[candidate_id] = merged

    _try_db_upsert("candidates", merged)
    return dict(merged)


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    with _LOCK:
        candidate = _CANDIDATES.get(candidate_id)
        return dict(candidate) if candidate is not None else None


def upsert_skills(candidate_id: str, skills: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in skills:
        skill = dict(raw)
        label = str(skill.get("name", skill.get("label", skill.get("canonical_id", "")))).strip()
        if not label:
            continue
        canonical = " ".join(label.lower().split())
        if canonical in seen:
            continue
        seen.add(canonical)

        normalized.append(
            {
                **skill,
                "candidate_id": candidate_id,
                "name": label,
                "canonical_id": str(skill.get("canonical_id", canonical)).strip() or canonical,
                "updated_at": _utc_now(),
            }
        )

    with _LOCK:
        _CANDIDATE_SKILLS[candidate_id] = normalized

    _try_db_upsert("candidate_skills", {"candidate_id": candidate_id, "skills": normalized})
    return [dict(item) for item in normalized]


def get_skills(candidate_id: str) -> list[dict[str, Any]]:
    with _LOCK:
        skills = _CANDIDATE_SKILLS.get(candidate_id, [])
        return [dict(item) for item in skills]


def reset_for_tests() -> None:
    with _LOCK:
        _CANDIDATES.clear()
        _CANDIDATE_SKILLS.clear()


def _candidate_id(payload: Mapping[str, Any]) -> str:
    value = payload.get("id", payload.get("candidate_id"))
    text = str(value).strip() if value is not None else ""
    return text or str(uuid4())


def _try_db_upsert(table_name: str, payload: Mapping[str, Any]) -> None:
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
    "upsert_candidate",
    "get_candidate",
    "upsert_skills",
    "get_skills",
    "reset_for_tests",
]


