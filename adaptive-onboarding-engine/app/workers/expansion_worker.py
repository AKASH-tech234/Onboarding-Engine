"""
app/workers/expansion_worker.py

In-memory graph expansion worker for local integration testing.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from pathlib import Path
import importlib.util
import sys

try:
    from graph import graph_engine
    from graph.models import SkillNode
except ImportError:  # pragma: no cover - alternate package root
    from app.modules.graph import graph_engine
    from app.modules.graph.models import SkillNode

try:
    from queue import job_queue  # type: ignore
except Exception:  # pragma: no cover - queue module name conflicts with stdlib
    try:
        from app.queue import job_queue  # type: ignore
    except Exception:  # pragma: no cover - direct file fallback
        if "_job_queue_fallback" in sys.modules:
            job_queue = sys.modules["_job_queue_fallback"]  # type: ignore
        else:
            _queue_path = Path(__file__).resolve().parents[1] / "queue" / "job_queue.py"
            _spec = importlib.util.spec_from_file_location("_job_queue_fallback", _queue_path)
            _module = importlib.util.module_from_spec(_spec)
            sys.modules["_job_queue_fallback"] = _module
            assert _spec is not None and _spec.loader is not None
            _spec.loader.exec_module(_module)
            job_queue = _module  # type: ignore


def enqueue_expansion_task(
    skill_label: str,
    *,
    domain_hint: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    return job_queue.enqueue_task(
        "expansion",
        payload={"skill_label": skill_label, "domain_hint": domain_hint},
        metadata=metadata,
    )


def run_once() -> dict[str, Any] | None:
    task = job_queue.dequeue_task(task_type="expansion")
    if task is None:
        return None
    return process_task(task.payload)


def process_task(payload: Mapping[str, Any]) -> dict[str, Any]:
    skill_label = str(payload.get("skill_label", "")).strip()
    if not skill_label:
        raise ValueError("Expansion payload must include 'skill_label'.")

    domain = str(payload.get("domain_hint", "general")).strip().lower() or "general"
    skill_id = _canonicalize_skill_id(skill_label)

    if graph_engine.has_node(skill_id):
        return {
            "ok": True,
            "staged": False,
            "skill_id": skill_id,
            "message": "Skill already exists in graph.",
        }

    node = SkillNode(
        id=skill_id,
        label=skill_label,
        domain=domain,
        base_effort_days=3,
        difficulty=3,
        tags=tuple(),
        source="llm_generated",
    )
    graph_engine.stage_node(node, edges=[])

    return {
        "ok": True,
        "staged": True,
        "skill_id": skill_id,
        "domain": domain,
    }


def _canonicalize_skill_id(label: str) -> str:
    return "_".join(" ".join(label.strip().lower().split()).split())


__all__ = ["enqueue_expansion_task", "run_once", "process_task"]
