"""
app/api/controllers/onboard_controller.py

Controller logic for onboarding endpoints.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from pathlib import Path
import importlib.util
import sys

try:
    from ingestion.gap_analyzer import analyze_gaps
    from pathway.pathway_builder import build_pathway
    from pathway.response_builder import build_preview_response, build_response
except ImportError:  # pragma: no cover - alternate package root
    from app.modules.ingestion.gap_analyzer import analyze_gaps
    from app.modules.pathway.pathway_builder import build_pathway
    from app.modules.pathway.response_builder import build_preview_response, build_response

try:
    from schemas.job_schema import JobResponse, JobStatus
    from schemas.onboard_schema import OnboardPreviewResponse, OnboardRequest
except ImportError:  # pragma: no cover - alternate package root
    from app.schemas.job_schema import JobResponse, JobStatus
    from app.schemas.onboard_schema import OnboardPreviewResponse, OnboardRequest

try:
    from queue import job_manager  # type: ignore
except Exception:  # pragma: no cover - queue module name conflicts with stdlib
    try:
        from app.queue import job_manager  # type: ignore
    except Exception:  # pragma: no cover - direct file fallback
        if "_job_manager_fallback" in sys.modules:
            job_manager = sys.modules["_job_manager_fallback"]  # type: ignore
        else:
            _job_manager_path = Path(__file__).resolve().parents[2] / "queue" / "job_manager.py"
            _spec = importlib.util.spec_from_file_location("_job_manager_fallback", _job_manager_path)
            _module = importlib.util.module_from_spec(_spec)
            sys.modules["_job_manager_fallback"] = _module
            assert _spec is not None and _spec.loader is not None
            _spec.loader.exec_module(_module)
            job_manager = _module  # type: ignore


async def onboard(request: OnboardRequest | Mapping[str, Any]) -> JobResponse:
    """
    Full onboarding pipeline in one controller call.

    Current implementation executes synchronously in-process for local/dev.
    """
    req = _to_onboard_request(request)
    job_profile = req.resolved_job_profile()
    if job_profile is None:
        raise ValueError("Onboard request must include requirement_profile or job_profile.")

    job = job_manager.create_job(
        candidate_id=req.candidate_profile.id,
        job_profile_id=job_profile.id,
        metadata={"source": "onboard_controller"},
    )

    job_manager.update_job(
        job.job_id,
        status=JobStatus.RUNNING,
        stage="gap_analysis",
        message="Computing skill gaps",
        percent=20,
    )

    try:
        gap_result = analyze_gaps(
            {
                "candidate_profile": _dump_model(req.candidate_profile),
                "requirement_profile": _dump_model(job_profile),
            }
        )

        job_manager.update_job(
            job.job_id,
            stage="pathway_building",
            message="Building pathway",
            percent=60,
        )

        pathway = build_pathway(
            gap_result,
            role=req.options.role,
            graph_version=req.options.graph_version,
            learning_mode=req.options.learning_mode,
            time_budget_days=req.options.time_budget_days,
            max_days_per_phase=req.options.max_days_per_phase,
            max_items_per_phase=req.options.max_items_per_phase,
            group_by_domain=req.options.group_by_domain,
        )

        result_payload = build_response(pathway, include_metadata=True)

        final_job = job_manager.update_job(
            job.job_id,
            status=JobStatus.COMPLETED,
            stage="completed",
            message="Pathway generated successfully",
            percent=100,
            result=result_payload,
            metadata={"pathway_type": result_payload.get("pathway_type")},
        )
        if final_job is None:
            raise RuntimeError(f"Job '{job.job_id}' disappeared from job manager")
        return final_job

    except Exception as error:
        failed = job_manager.update_job(
            job.job_id,
            status=JobStatus.FAILED,
            stage="failed",
            message="Onboarding failed",
            percent=100,
            error=str(error),
        )
        if failed is None:
            raise
        return failed


async def preview(request: OnboardRequest | Mapping[str, Any]) -> OnboardPreviewResponse:
    """
    Lightweight preview endpoint for fast UX feedback.
    """
    req = _to_onboard_request(request)
    job_profile = req.resolved_job_profile()
    if job_profile is None:
        raise ValueError("Onboard request must include requirement_profile or job_profile.")

    gap_result = analyze_gaps(
        {
            "candidate_profile": _dump_model(req.candidate_profile),
            "requirement_profile": _dump_model(job_profile),
        }
    )
    pathway = build_pathway(
        gap_result,
        role=req.options.role,
        graph_version=req.options.graph_version,
        learning_mode=req.options.learning_mode,
        time_budget_days=req.options.time_budget_days,
        max_days_per_phase=req.options.max_days_per_phase,
        max_items_per_phase=req.options.max_items_per_phase,
        group_by_domain=req.options.group_by_domain,
    )

    preview_dict = build_preview_response(pathway)
    return OnboardPreviewResponse(
        request_id=req.request_id,
        accepted=True,
        candidate_id=preview_dict.get("candidate_id"),
        job_id=preview_dict.get("job_id"),
        warnings=list(pathway.metadata.get("warnings", [])),
        estimated_gap_count=int(pathway.metadata.get("input_gap_count", 0)),
    )


async def refresh(
    request: OnboardRequest | Mapping[str, Any],
    *,
    previous_job_id: str | None = None,
) -> JobResponse:
    """
    Refresh simply re-runs onboarding with the latest input.
    """
    _ = previous_job_id
    return await onboard(request)


def _to_onboard_request(request: OnboardRequest | Mapping[str, Any]) -> OnboardRequest:
    if isinstance(request, OnboardRequest):
        return request

    payload = dict(request)
    req = _coerce_model(OnboardRequest, payload)

    req.candidate_profile = _coerce_model(
        candidate_type:=type(getattr(req, "candidate_profile", None) or getattr(OnboardRequest, "__annotations__", {}).get("candidate_profile", object)),
        getattr(req, "candidate_profile", payload.get("candidate_profile")),
    )

    resolved_requirement = getattr(req, "requirement_profile", payload.get("requirement_profile"))
    resolved_job = getattr(req, "job_profile", payload.get("job_profile"))
    resolved_options = getattr(req, "options", payload.get("options"))

    job_type = type(resolved_requirement) if resolved_requirement is not None else type(resolved_job) if resolved_job is not None else object
    option_type = type(resolved_options) if resolved_options is not None else object

    if isinstance(resolved_requirement, Mapping):
        req.requirement_profile = _coerce_model(job_type, resolved_requirement)
    if isinstance(resolved_job, Mapping):
        req.job_profile = _coerce_model(job_type, resolved_job)
    if isinstance(resolved_options, Mapping):
        req.options = _coerce_model(option_type, resolved_options)

    # Fallback when model annotations are not available via runtime typing.
    try:
        from schemas.onboard_schema import CandidateInput, JobInput, OptionsInput  # type: ignore
    except Exception:
        try:
            from app.schemas.onboard_schema import CandidateInput, JobInput, OptionsInput  # type: ignore
        except Exception:
            CandidateInput = JobInput = OptionsInput = object  # type: ignore

    if isinstance(getattr(req, "candidate_profile", None), Mapping):
        req.candidate_profile = _coerce_model(CandidateInput, getattr(req, "candidate_profile"))
    if isinstance(getattr(req, "requirement_profile", None), Mapping):
        req.requirement_profile = _coerce_model(JobInput, getattr(req, "requirement_profile"))
    if isinstance(getattr(req, "job_profile", None), Mapping):
        req.job_profile = _coerce_model(JobInput, getattr(req, "job_profile"))
    if isinstance(getattr(req, "options", None), Mapping):
        req.options = _coerce_model(OptionsInput, getattr(req, "options"))

    return req


def _coerce_model(model_type: Any, value: Any) -> Any:
    if value is None:
        return value
    if model_type in (None, object) or isinstance(value, model_type):
        return value
    if hasattr(model_type, "model_validate"):
        return model_type.model_validate(dict(value))
    if hasattr(model_type, "parse_obj"):
        return model_type.parse_obj(dict(value))
    return model_type(**dict(value))


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, Mapping):
        return dict(value)
    return dict(vars(value))


__all__ = ["onboard", "preview", "refresh"]
