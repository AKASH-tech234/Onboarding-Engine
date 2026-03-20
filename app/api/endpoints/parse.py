from fastapi import APIRouter
from schemas.request import ResumeRequest
from pipeline.resume_pipeline import run_pipeline

router = APIRouter()

@router.post("/parse-resume")
def parse_resume(req: ResumeRequest):
    return {"parsed": run_pipeline(req.dict())}