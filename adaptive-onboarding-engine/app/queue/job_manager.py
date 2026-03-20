"""
app/queue/job_manager.py

In-memory job lifecycle manager for local/dev execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

try:
    from schemas.job_schema import JobResponse, JobStatus, JobProgress
except ImportError:  # pragma: no cover - alternate package root
    from app.schemas.job_schema import JobResponse, JobStatus, JobProgress


@dataclass
class _JobRecord:
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    candidate_id: str | None = None
    job_profile_id: str | None = None
    progress: JobProgress | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


_JOBS: dict[str, _JobRecord] = {}
_LOCK = Lock()


def create_job(
    *,
    candidate_id: str | None = None,
    job_profile_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> JobResponse:
    now = datetime.now(timezone.utc)
    job_id = str(uuid4())
    record = _JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=now,
        updated_at=now,
        candidate_id=candidate_id,
        job_profile_id=job_profile_id,
        metadata=metadata or {},
    )
    with _LOCK:
        _JOBS[job_id] = record
    return _to_schema(record)


def get_job_status(job_id: str) -> JobResponse | None:
    with _LOCK:
        record = _JOBS.get(job_id)
        return _to_schema(record) if record else None


def update_job(
    job_id: str,
    *,
    status: JobStatus | str | None = None,
    stage: str | None = None,
    message: str | None = None,
    percent: int | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> JobResponse | None:
    with _LOCK:
        record = _JOBS.get(job_id)
        if record is None:
            return None

        if status is not None:
            record.status = _coerce_status(status)
        if stage is not None or message is not None or percent is not None:
            progress = record.progress or JobProgress()
            if stage is not None:
                progress.stage = stage
            if message is not None:
                progress.message = message
            if percent is not None:
                progress.percent = max(0, min(100, int(percent)))
            record.progress = progress
        if result is not None:
            record.result = result
        if error is not None:
            record.error = error
        if metadata:
            record.metadata.update(metadata)

        record.updated_at = datetime.now(timezone.utc)
        return _to_schema(record)


def cancel_job(job_id: str) -> JobResponse | None:
    return update_job(
        job_id,
        status=JobStatus.CANCELLED,
        stage="cancelled",
        message="Job was cancelled",
        percent=100,
    )


def list_jobs(*, status: JobStatus | str | None = None) -> list[JobResponse]:
    with _LOCK:
        records = list(_JOBS.values())

    if status is not None:
        target_status = _coerce_status(status)
        records = [record for record in records if record.status == target_status]

    records.sort(key=lambda record: record.updated_at, reverse=True)

    items: list[JobResponse] = []
    for record in records:
        schema = _to_schema(record)
        if schema is not None:
            items.append(schema)
    return items


def get_job_metrics() -> dict[str, Any]:
    with _LOCK:
        records = list(_JOBS.values())

    by_status = {status.value: 0 for status in JobStatus}
    for record in records:
        by_status[record.status.value] += 1

    return {
        "total": len(records),
        "by_status": by_status,
    }


def dispatch_webhook(*, callback_url: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Placeholder webhook dispatcher.

    Returns a local status object so callers can log intent consistently.
    """
    if not callback_url:
        return {"sent": False, "reason": "missing_callback_url"}
    return {"sent": False, "reason": "webhook_not_implemented", "callback_url": callback_url, "payload": payload}


def _coerce_status(status: JobStatus | str) -> JobStatus:
    if isinstance(status, JobStatus):
        return status
    try:
        return JobStatus(str(status).strip().lower())
    except ValueError:
        return JobStatus.FAILED


def _to_schema(record: _JobRecord | None) -> JobResponse | None:
    if record is None:
        return None
    return JobResponse(
        job_id=record.job_id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        candidate_id=record.candidate_id,
        job_profile_id=record.job_profile_id,
        progress=record.progress,
        result=record.result,
        error=record.error,
        trace_id=record.trace_id,
        metadata=record.metadata,
    )


__all__ = [
    "create_job",
    "get_job_status",
    "update_job",
    "cancel_job",
    "list_jobs",
    "get_job_metrics",
    "dispatch_webhook",
]
