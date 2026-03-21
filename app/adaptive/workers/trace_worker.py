"""
app/workers/trace_worker.py

In-memory reasoning trace worker for local integration testing.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from pathlib import Path
import importlib.util
import sys

try:
    from app.adaptive.queue import job_manager, job_queue  # type: ignore
except Exception:  # pragma: no cover - queue module name conflicts with stdlib
    try:
        from app.adaptive.queue import job_manager, job_queue  # type: ignore
    except Exception:  # pragma: no cover - direct file fallback
        _queue_dir = Path(__file__).resolve().parents[1] / "queue"
        if "_job_manager_fallback" in sys.modules:
            job_manager = sys.modules["_job_manager_fallback"]  # type: ignore
        else:
            _jm_spec = importlib.util.spec_from_file_location(
                "_job_manager_fallback",
                _queue_dir / "job_manager.py",
            )
            _jm_module = importlib.util.module_from_spec(_jm_spec)
            sys.modules["_job_manager_fallback"] = _jm_module
            assert _jm_spec is not None and _jm_spec.loader is not None
            _jm_spec.loader.exec_module(_jm_module)
            job_manager = _jm_module  # type: ignore

        if "_job_queue_fallback" in sys.modules:
            job_queue = sys.modules["_job_queue_fallback"]  # type: ignore
        else:
            _jq_spec = importlib.util.spec_from_file_location(
                "_job_queue_fallback",
                _queue_dir / "job_queue.py",
            )
            _jq_module = importlib.util.module_from_spec(_jq_spec)
            sys.modules["_job_queue_fallback"] = _jq_module
            assert _jq_spec is not None and _jq_spec.loader is not None
            _jq_spec.loader.exec_module(_jq_module)
            job_queue = _jq_module  # type: ignore


def enqueue_trace_task(
    *,
    job_id: str,
    pathway_result: Mapping[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
):
    payload: dict[str, Any] = {"job_id": job_id}
    if pathway_result is not None:
        payload["pathway_result"] = dict(pathway_result)
    return job_queue.enqueue_task("trace", payload=payload, metadata=metadata)


def run_once() -> dict[str, Any] | None:
    task = job_queue.dequeue_task(task_type="trace")
    if task is None:
        return None
    return process_task(task.payload)


def process_task(payload: Mapping[str, Any]) -> dict[str, Any]:
    job_id = payload.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("Trace task payload must include non-empty 'job_id'.")

    job = job_manager.get_job_status(job_id)
    if job is None:
        return {"ok": False, "job_id": job_id, "error": "job_not_found"}

    result = _coerce_mapping(job.result)
    if not result:
        result = _coerce_mapping(payload.get("pathway_result"))

    trace = build_trace(result)
    result["reasoning_trace"] = trace

    updated = job_manager.update_job(
        job_id,
        stage="trace_completed",
        message="Reasoning trace generated",
        percent=100,
        result=result,
    )
    return {
        "ok": updated is not None,
        "job_id": job_id,
        "trace": trace,
    }


def build_trace(pathway_result: Mapping[str, Any]) -> dict[str, Any]:
    summary = _coerce_mapping(pathway_result.get("summary"))
    total_items = int(summary.get("total_items", 0))
    total_phases = int(summary.get("total_phases", 0))
    unresolved_count = int(summary.get("unresolved_count", 0))

    raw_text = (
        f"Generated pathway with {total_items} items across {total_phases} phases. "
        f"Unresolved skills: {unresolved_count}."
    )

    return {
        "candidate_assessment": "Candidate profile has been compared against role requirements.",
        "gap_identification": f"{total_items} learning items prioritized.",
        "course_selection_rationale": "Items were selected by gap size, dependency impact, and effort.",
        "pathway_ordering_logic": "Topological dependency order was preserved across phases.",
        "estimated_time_to_competency": f"Plan spans {summary.get('total_effort_days', 0)} effort days.",
        "raw": raw_text,
    }


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["enqueue_trace_task", "run_once", "process_task", "build_trace"]


