from fastapi import FastAPI, HTTPException

from pipeline.resume_pipeline import run_pipeline
from schemas.request import ResumeRequest


app = FastAPI(title="Deterministic Resume Parsing Engine")


@app.post("/parse-resume")
def parse_resume(payload: ResumeRequest) -> dict:
	try:
		result = run_pipeline(payload.dict())
		return {"parsed": result}
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
	from pipeline.resume_pipeline import run_pipeline

	sample = {
		"skills": ["Python"],
		"projects": [
			{"name": "Chat", "description": "Built using WebSocket"}
		],
		"experience": [],
	}

	result = run_pipeline(sample)
	print(result)
