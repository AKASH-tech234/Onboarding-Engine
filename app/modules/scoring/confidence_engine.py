"""Deterministic confidence scoring from explicit evidence signals."""

from __future__ import annotations

from utils.logger import get_logger


logger = get_logger("confidence")


def compute_confidence(skills: dict) -> dict:
	logger.debug("Confidence input: %s", skills)

	if not isinstance(skills, dict):
		raise ValueError("skills must be a dictionary")

	result: dict = {}
	for name in sorted(skills.keys()):
		payload = skills[name]
		if not isinstance(payload, dict):
			raise ValueError(f"Skill payload for '{name}' must be an object")

		projects = payload.get("projects", 0)
		experience_months = payload.get("experience_months", 0)
		evidence = payload.get("evidence", [])
		listed = payload.get("listed", False)

		if not isinstance(projects, int):
			raise ValueError(f"projects for '{name}' must be an integer")
		if not isinstance(experience_months, int):
			raise ValueError(f"experience_months for '{name}' must be an integer")
		if not isinstance(evidence, list):
			raise ValueError(f"evidence for '{name}' must be a list")
		if not isinstance(listed, bool):
			raise ValueError(f"listed for '{name}' must be a boolean")

		confidence = 0.0
		if projects > 0:
			confidence += 0.4
		if experience_months > 0:
			confidence += 0.4
		has_evidence = any(isinstance(item, str) and item for item in evidence)
		if has_evidence:
			confidence += 0.2
		if listed:
			confidence += 0.2

		updated = dict(payload)
		updated["confidence"] = round(max(0.0, min(confidence, 1.0)), 4)
		if updated["confidence"] == 0:
			logger.warning("Zero confidence skill: %s", name)
		logger.debug("Confidence for %s -> %.2f", name, updated["confidence"])
		result[name] = updated

	logger.debug("Confidence output: %s", result)
	return result
