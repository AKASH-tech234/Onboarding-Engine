from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, HTTPException, Query, Request
from starlette.middleware.base import BaseHTTPMiddleware

from pipeline.resume_pipeline import run_pipeline
from schemas.final_result import FinalResultEnvelope
from schemas.request import ParseRequest, ResumeInput, jd_to_pipeline_input, payload_to_pipeline_input
from utils.logger import get_logger


logger = get_logger("server")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()

        logger.info("REQ id=%s method=%s path=%s", request_id, request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.error(
                "REQ_FAIL id=%s method=%s path=%s duration_ms=%.2f error=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                exc.__class__.__name__,
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000.0
        logger.info(
            "RES id=%s method=%s path=%s status=%d duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


app = FastAPI(title="Deterministic Resume Parsing Engine")
app.add_middleware(RequestLoggingMiddleware)


def _resolve_options(
    payload: ParseRequest | ResumeInput,
    include_pathway: bool | None,
    pathway_phase_size: int | None,
    scoring_profile: str | None,
) -> tuple[bool, int, str]:
    body_options = payload.options if isinstance(payload, ParseRequest) else None
    resolved_include_pathway = (
        include_pathway
        if include_pathway is not None
        else (body_options.include_pathway if body_options is not None else False)
    )
    resolved_phase_size = (
        pathway_phase_size
        if pathway_phase_size is not None
        else (body_options.pathway_phase_size if body_options is not None else 3)
    )
    resolved_scoring_profile = (
        scoring_profile.strip()
        if isinstance(scoring_profile, str)
        else (body_options.scoring_profile if body_options is not None else "default")
    )
    return resolved_include_pathway, resolved_phase_size, resolved_scoring_profile


def _execute_pipeline(
    payload: ParseRequest | ResumeInput,
    include_pathway: bool | None,
    pathway_phase_size: int | None,
    scoring_profile: str | None,
) -> dict:
    resolved_include_pathway, resolved_phase_size, resolved_scoring_profile = _resolve_options(
        payload,
        include_pathway,
        pathway_phase_size,
        scoring_profile,
    )

    phase_input = payload_to_pipeline_input(payload)
    if isinstance(payload, ParseRequest):
        jd_input = jd_to_pipeline_input(payload.jd)
        return run_pipeline(
            phase_input,
            jd_data=jd_input,
            include_pathway=resolved_include_pathway,
            pathway_phase_size=resolved_phase_size,
            scoring_profile=resolved_scoring_profile,
        )

    return run_pipeline(
        phase_input,
        include_pathway=resolved_include_pathway,
        pathway_phase_size=resolved_phase_size,
        scoring_profile=resolved_scoring_profile,
    )


@app.post("/parse-resume")
def parse_resume(
    payload: ParseRequest | ResumeInput,
    include_pathway: bool | None = Query(default=None),
    pathway_phase_size: int | None = Query(default=None, ge=1, le=50),
    scoring_profile: str | None = Query(default=None, min_length=1, max_length=64),
) -> dict:
    try:
        result = _execute_pipeline(payload, include_pathway, pathway_phase_size, scoring_profile)
        return {"parsed": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/final-result", response_model=FinalResultEnvelope)
def final_result(
    payload: ParseRequest | ResumeInput,
    include_pathway: bool | None = Query(default=None),
    pathway_phase_size: int | None = Query(default=None, ge=1, le=50),
    scoring_profile: str | None = Query(default=None, min_length=1, max_length=64),
) -> FinalResultEnvelope:
    try:
        result = _execute_pipeline(payload, include_pathway, pathway_phase_size, scoring_profile)
        return FinalResultEnvelope(parsed=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    sample = {
        "skills": ["Python"],
        "projects": [
            {"name": "Chat", "description": "Built using WebSocket"}
        ],
        "experience": [],
    }

    result = run_pipeline(sample)
    print(result)
