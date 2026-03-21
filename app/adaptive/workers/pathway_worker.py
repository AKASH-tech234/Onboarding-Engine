"""
app/workers/pathway_worker.py

In-memory pathway worker for local integration testing.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from pathlib import Path
import importlib.util
import sys

try:
    from app.adaptive.modules.ingestion.gap_analyzer import analyze_gaps
    from app.adaptive.modules.pathway.pathway_builder import build_pathway
    from app.adaptive.modules.pathway.response_builder import build_response
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.modules.ingestion.gap_analyzer import analyze_gaps
    from app.adaptive.modules.pathway.pathway_builder import build_pathway
    from app.adaptive.modules.pathway.response_builder import build_response

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


def enqueue_pathway_task(
    payload: Mapping[str, Any],
    *,
    job_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    return job_queue.enqueue_task(
        "pathway",
        payload={"job_id": job_id, "request": dict(payload)},
        metadata=metadata,
    )


def run_once() -> dict[str, Any] | None:
    task = job_queue.dequeue_task(task_type="pathway")
    if task is None:
        return None
    return process_task(task.payload)


def process_task(payload: Mapping[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, Mapping):
        raise ValueError("Pathway task payload must include a mapping 'request'.")

    job_id = payload.get("job_id")
    if isinstance(job_id, str):
        job_manager.update_job(
            job_id,
            status="running",
            stage="worker_pathway",
            message="Pathway worker started",
            percent=30,
        )

    try:
        candidate = _coerce_mapping(request.get("candidate_profile"))
        requirement = _coerce_mapping(
            request.get("requirement_profile", request.get("job_profile"))
        )
        options = _coerce_mapping(request.get("options"))

        gap_result = analyze_gaps(
            {
                "candidate_profile": candidate,
                "requirement_profile": requirement,
            }
        )
        pathway_result = build_pathway(
            gap_result,
            role=_str_or_none(options.get("role")),
            graph_version=_str_or_default(options.get("graph_version"), "v1"),
            learning_mode=_str_or_default(options.get("learning_mode"), "deep_learning"),
            time_budget_days=_to_int_or_none(options.get("time_budget_days")),
            max_days_per_phase=_to_int_or_default(options.get("max_days_per_phase"), 7),
            max_items_per_phase=_to_int_or_default(options.get("max_items_per_phase"), 5),
            group_by_domain=bool(options.get("group_by_domain", True)),
        )
        response = build_response(pathway_result, include_metadata=True)

        if isinstance(job_id, str):
            job_manager.update_job(
                job_id,
                status="completed",
                stage="completed",
                message="Pathway worker completed",
                percent=100,
                result=response,
            )

        return {
            "ok": True,
            "job_id": job_id,
            "result": response,
        }

    except Exception as error:
        if isinstance(job_id, str):
            job_manager.update_job(
                job_id,
                status="failed",
                stage="failed",
                message="Pathway worker failed",
                percent=100,
                error=str(error),
            )
        return {"ok": False, "job_id": job_id, "error": str(error)}


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _str_or_default(value: Any, default: str) -> str:
    text = _str_or_none(value)
    return text if text is not None else default


def _to_int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = ["enqueue_pathway_task", "run_once", "process_task"]


