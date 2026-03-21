"""
app/queue/job_queue.py

Simple in-memory task queue abstraction.

This is intentionally lightweight for local development and tests.
Production workers can replace this module with Celery/RQ without changing
controller signatures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class QueuedTask:
    task_id: str
    task_type: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


_QUEUE: list[QueuedTask] = []
_LOCK = Lock()


def enqueue_task(
    task_type: str,
    payload: dict[str, Any] | None = None,
    *,
    metadata: dict[str, Any] | None = None,
) -> QueuedTask:
    task = QueuedTask(
        task_id=str(uuid4()),
        task_type=str(task_type).strip() or "unknown",
        payload=payload or {},
        created_at=datetime.now(timezone.utc),
        attempts=0,
        metadata=metadata or {},
    )
    with _LOCK:
        _QUEUE.append(task)
    return task


def dequeue_task(*, task_type: str | None = None) -> QueuedTask | None:
    with _LOCK:
        if not _QUEUE:
            return None

        if task_type is None:
            return _QUEUE.pop(0)

        normalized = task_type.strip().lower()
        for index, task in enumerate(_QUEUE):
            if task.task_type.lower() == normalized:
                return _QUEUE.pop(index)
    return None


def requeue_task(task: QueuedTask, *, reason: str | None = None) -> QueuedTask:
    retried = QueuedTask(
        task_id=task.task_id,
        task_type=task.task_type,
        payload=dict(task.payload),
        created_at=task.created_at,
        attempts=task.attempts + 1,
        metadata={**task.metadata, "requeued_reason": reason} if reason else dict(task.metadata),
    )
    with _LOCK:
        _QUEUE.append(retried)
    return retried


def queue_size(*, task_type: str | None = None) -> int:
    with _LOCK:
        if task_type is None:
            return len(_QUEUE)
        normalized = task_type.strip().lower()
        return sum(1 for task in _QUEUE if task.task_type.lower() == normalized)


def peek_tasks(limit: int = 20) -> list[QueuedTask]:
    safe_limit = max(1, min(500, int(limit)))
    with _LOCK:
        return list(_QUEUE[:safe_limit])


def clear_queue() -> int:
    with _LOCK:
        count = len(_QUEUE)
        _QUEUE.clear()
    return count


__all__ = [
    "QueuedTask",
    "enqueue_task",
    "dequeue_task",
    "requeue_task",
    "queue_size",
    "peek_tasks",
    "clear_queue",
]


