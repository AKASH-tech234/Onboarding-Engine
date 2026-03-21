"""
app/db/repositories/gap_analysis_repo.py

Gap analysis and job status persistence repository.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4
from collections.abc import Mapping

try:
    from app.adaptive.db.supabase_client import get_client
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.db.supabase_client import get_client


_LOCK = Lock()
_GAP_ANALYSES: dict[str, dict[str, Any]] = {}
_JOBS: dict[str, dict[str, Any]] = {}


def create_gap_analysis(payload: Mapping[str, Any]) -> dict[str, Any]:
    analysis_id = _id_from(payload, keys=("id", "gap_analysis_id"))
    now = _utc_now()

    row = {
        **dict(payload),
        "id": analysis_id,
        "gap_analysis_id": analysis_id,
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK:
        _GAP_ANALYSES[analysis_id] = row

    _try_db_insert("gap_analyses", row)
    return dict(row)


def get_gap_analysis(gap_analysis_id: str) -> dict[str, Any] | None:
    with _LOCK:
        value = _GAP_ANALYSES.get(gap_analysis_id)
        return dict(value) if value is not None else None


def create_job(payload: Mapping[str, Any]) -> dict[str, Any]:
    job_id = _id_from(payload, keys=("job_id", "id"))
    now = _utc_now()
    row = {
        **dict(payload),
        "job_id": job_id,
        "id": job_id,
        "status": str(payload.get("status", "queued")).strip().lower() or "queued",
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK:
        _JOBS[job_id] = row

    _try_db_insert("jobs", row)
    return dict(row)


def update_job_status(
    job_id: str,
    status: str,
    *,
    progress: int | None = None,
    message: str | None = None,
    error: str | None = None,
    result: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    with _LOCK:
        row = _JOBS.get(job_id)
        if row is None:
            return None

        row["status"] = str(status).strip().lower() or row.get("status", "queued")
        row["updated_at"] = _utc_now()
        if progress is not None:
            row["progress"] = max(0, min(100, int(progress)))
        if message is not None:
            row["message"] = message
        if error is not None:
            row["error"] = error
        if result is not None:
            row["result"] = dict(result)
        if metadata:
            merged_metadata = dict(row.get("metadata", {}))
            merged_metadata.update(dict(metadata))
            row["metadata"] = merged_metadata

        snapshot = dict(row)

    _try_db_insert("jobs_status_events", snapshot)
    return snapshot


def get_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        row = _JOBS.get(job_id)
        return dict(row) if row is not None else None


def reset_for_tests() -> None:
    with _LOCK:
        _GAP_ANALYSES.clear()
        _JOBS.clear()


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
    "create_gap_analysis",
    "get_gap_analysis",
    "create_job",
    "update_job_status",
    "get_job",
    "reset_for_tests",
]


