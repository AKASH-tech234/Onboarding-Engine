"""Deterministic proficiency scoring from normalized skill signals."""

from __future__ import annotations


def _to_level(score: float) -> str:
	if score < 0.4:
		return "beginner"
	if score <= 0.7:
		return "intermediate"
	return "advanced"


def compute_proficiency(skills: dict) -> dict:
	if not isinstance(skills, dict):
		raise ValueError("skills must be a dictionary")

	result: dict = {}
	for name in sorted(skills.keys()):
		payload = skills[name]
		if not isinstance(payload, dict):
			raise ValueError(f"Skill payload for '{name}' must be an object")

		signals = payload.get("signals")
		if not isinstance(signals, dict):
			raise ValueError(f"signals for '{name}' must be an object")

		listed_value = 1.0 if bool(payload.get("listed", False)) else 0.0
		frequency = float(signals.get("frequency", 0.0))
		duration = float(signals.get("duration", 0.0))
		recency = float(signals.get("recency", 0.0))

		score = (
			0.2 * listed_value
			+ 0.3 * frequency
			+ 0.3 * duration
			+ 0.2 * recency
		)

		score = round(max(0.0, min(score, 1.0)), 4)

		updated = dict(payload)
		updated["score"] = score
		updated["level"] = _to_level(score)
		result[name] = updated

	return result
