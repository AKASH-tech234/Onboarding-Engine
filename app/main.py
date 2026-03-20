from fastapi import FastAPI, HTTPException

from pipeline.resume_pipeline import run_pipeline
from schemas.request import ParseRequest, ResumeInput, jd_to_pipeline_input, payload_to_pipeline_input


app = FastAPI(title="Deterministic Resume Parsing Engine")


@app.post("/parse-resume")
def parse_resume(payload: ParseRequest | ResumeInput) -> dict:
	try:
		phase_input = payload_to_pipeline_input(payload)
		if isinstance(payload, ParseRequest):
			jd_input = jd_to_pipeline_input(payload.jd)
			result = run_pipeline(phase_input, jd_data=jd_input)
		else:
			result = run_pipeline(phase_input)
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
