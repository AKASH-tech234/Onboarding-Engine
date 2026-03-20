from fastapi import APIRouter
from schemas.request import ParseRequest, ResumeInput, jd_to_pipeline_input, payload_to_pipeline_input
from pipeline.resume_pipeline import run_pipeline

router = APIRouter()

@router.post("/parse-resume")
def parse_resume(req: ParseRequest | ResumeInput):
    phase_input = payload_to_pipeline_input(req)
    if isinstance(req, ParseRequest):
        jd_input = jd_to_pipeline_input(req.jd)
        return {"parsed": run_pipeline(phase_input, jd_data=jd_input)}
    return {"parsed": run_pipeline(phase_input)}