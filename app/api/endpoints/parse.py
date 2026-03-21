from fastapi import APIRouter, Query
from schemas.request import ParseRequest, ResumeInput, jd_to_pipeline_input, payload_to_pipeline_input
from pipeline.resume_pipeline import run_pipeline

router = APIRouter()

@router.post("/parse-resume")
def parse_resume(
    req: ParseRequest | ResumeInput,
    include_pathway: bool | None = Query(default=None),
    pathway_phase_size: int | None = Query(default=None, ge=1, le=50),
    scoring_profile: str | None = Query(default=None, min_length=1, max_length=64),
):
    body_options = req.options if isinstance(req, ParseRequest) else None
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

    phase_input = payload_to_pipeline_input(req)
    if isinstance(req, ParseRequest):
        jd_input = jd_to_pipeline_input(req.jd)
        return {
            "parsed": run_pipeline(
                phase_input,
                jd_data=jd_input,
                include_pathway=resolved_include_pathway,
                pathway_phase_size=resolved_phase_size,
                scoring_profile=resolved_scoring_profile,
            )
        }
    return {
        "parsed": run_pipeline(
            phase_input,
            include_pathway=resolved_include_pathway,
            pathway_phase_size=resolved_phase_size,
            scoring_profile=resolved_scoring_profile,
        )
    }