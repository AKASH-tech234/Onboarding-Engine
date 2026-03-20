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

	sample_input = {
		"skills": ["Python", "React"],
		"projects": [
			{
				"name": "Chat App",
				"description": "Built using Node.js and Socket.io",
			}
		],
		"experience": [
			{
				"role": "Backend Intern",
				"description": "Worked on Python Django APIs",
				"duration": "Jan 2023 - Jun 2023",
			}
		],
	}

	result = run_pipeline(sample_input)
	print(result)
