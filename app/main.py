from fastapi import FastAPI, HTTPException

from pipeline.resume_pipeline import run_pipeline
from schemas.request import ParseRequest, ResumeInput, jd_to_pipeline_input, payload_to_pipeline_input

try:
	from adaptive.api.app import create_app as create_adaptive_app
except ImportError:
	from app.adaptive.api.app import create_app as create_adaptive_app

try:
	from adaptive.api.controllers import onboard_controller
except ImportError:
	from app.adaptive.api.controllers import onboard_controller


app = FastAPI(title="Deterministic Resume Parsing Engine")
adaptive_app = create_adaptive_app()
app.mount("/adaptive", adaptive_app)


def _to_onboard_request_payload(parsed: dict) -> dict:
	candidate_skills = parsed.get("candidate_profile", {}).get("skills", [])
	requirement_skills = parsed.get("requirement_profile", {}).get("skills", [])

	return {
		"candidate_profile": {
			"skills": [
				{
					"name": item.get("name"),
					"score": item.get("score"),
					"confidence": item.get("confidence"),
				}
				for item in candidate_skills
				if isinstance(item, dict) and isinstance(item.get("name"), str)
			],
		},
		"requirement_profile": {
			"skills": [
				{
					"name": item.get("name"),
					"score": item.get("score"),
					"confidence": item.get("confidence"),
				}
				for item in requirement_skills
				if isinstance(item, dict) and isinstance(item.get("name"), str)
			],
		},
	}


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


@app.post("/parse-and-onboard")
async def parse_and_onboard(payload: ParseRequest | ResumeInput) -> dict:
	try:
		if not isinstance(payload, ParseRequest):
			raise HTTPException(
				status_code=400,
				detail="parse-and-onboard requires ParseRequest with both resume and jd payload.",
			)

		phase_input = payload_to_pipeline_input(payload)
		jd_input = jd_to_pipeline_input(payload.jd)
		parsed = run_pipeline(phase_input, jd_data=jd_input)

		if "requirement_profile" not in parsed:
			raise HTTPException(
				status_code=400,
				detail="Requirement profile missing from parser output; cannot run adaptive onboarding.",
			)

		onboard_payload = _to_onboard_request_payload(parsed)
		onboard_result = await onboard_controller.onboard(onboard_payload)

		if hasattr(onboard_result, "model_dump"):
			onboard_output = onboard_result.model_dump()
		elif hasattr(onboard_result, "dict"):
			onboard_output = onboard_result.dict()
		else:
			onboard_output = dict(onboard_result)

		return {
			"parsed": parsed,
			"onboarding": onboard_output,
		}
	except HTTPException:
		raise
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
