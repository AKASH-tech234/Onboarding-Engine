"""Deterministic skill mapping from structured resume fields."""

from __future__ import annotations

import re
from collections import defaultdict

from utils.logger import get_logger


VARIANT_TO_CANONICAL = {
	"nodejs": "node.js",
	"node": "node.js",
	"node js": "node.js",
	"py": "python",
}

MONTH_TO_INDEX = {
	"jan": 1,
	"january": 1,
	"feb": 2,
	"february": 2,
	"mar": 3,
	"march": 3,
	"apr": 4,
	"april": 4,
	"may": 5,
	"jun": 6,
	"june": 6,
	"jul": 7,
	"july": 7,
	"aug": 8,
	"august": 8,
	"sep": 9,
	"sept": 9,
	"september": 9,
	"oct": 10,
	"october": 10,
	"nov": 11,
	"november": 11,
	"dec": 12,
	"december": 12,
}

RANGE_PATTERN = re.compile(
	r"^\s*([A-Za-z]{3,9})\s+(\d{4})\s*-\s*([A-Za-z]{3,9})\s+(\d{4})\s*$"
)


logger = get_logger("mapper")


def _empty_skill_record(name: str, listed: bool) -> dict:
	return {
		"name": name,
		"listed": listed,
		"projects": 0,
		"experience_months": 0,
		"evidence": [],
	}


def _normalize_skill_name(skill: str) -> str:
	if not isinstance(skill, str):
		return ""
	normalized = skill.strip().lower()
	if normalized == "":
		return ""
	return VARIANT_TO_CANONICAL.get(normalized, normalized)


def _append_evidence(record: dict, evidence_item: str) -> None:
	if not isinstance(evidence_item, str) or evidence_item == "":
		return
	evidence = record.setdefault("evidence", [])
	if not isinstance(evidence, list):
		record["evidence"] = []
		evidence = record["evidence"]
	if evidence_item not in evidence:
		evidence.append(evidence_item)


def _count_non_overlapping_mentions(text: str, aliases: set[str]) -> int:
	lowered = text.lower()
	claimed = [False] * len(lowered)
	total = 0

	for alias in sorted(aliases, key=len, reverse=True):
		pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])")
		for match in pattern.finditer(lowered):
			start, end = match.span()
			if any(claimed[i] for i in range(start, end)):
				continue
			for i in range(start, end):
				claimed[i] = True
			total += 1

	return total


def _parse_duration_months(duration: str) -> int:
	if not isinstance(duration, str):
		return 0

	match = RANGE_PATTERN.match(duration)
	if not match:
		return 0

	start_month_text, start_year_text, end_month_text, end_year_text = match.groups()

	start_month = MONTH_TO_INDEX.get(start_month_text.lower())
	end_month = MONTH_TO_INDEX.get(end_month_text.lower())
	if start_month is None or end_month is None:
		return 0

	start_year = int(start_year_text)
	end_year = int(end_year_text)
	delta = (end_year - start_year) * 12 + (end_month - start_month) + 1

	if delta < 0:
		return 0
	return delta


def _build_alias_index(listed_skills: list[str]) -> dict[str, set[str]]:
	index: dict[str, set[str]] = defaultdict(set)

	for listed in listed_skills:
		canonical = VARIANT_TO_CANONICAL.get(listed, listed)
		index[canonical].add(canonical)
		index[canonical].add(listed)

	for variant, canonical in VARIANT_TO_CANONICAL.items():
		index[canonical].add(canonical)
		index[canonical].add(variant)

	return index


def map_skills(data: dict) -> dict:
	logger.debug("Mapper input: %s", data)

	listed_skills = data.get("skills", [])
	projects = data.get("projects", [])
	experience = data.get("experience", [])
	skill_sources = data.get("skill_sources", {})
	training_skills = data.get("training_skills", [])
	project_technology_skills = data.get("project_technology_skills", [])
	raw_technical_skills = data.get("technical_skills", {})
	raw_training = data.get("training", {})
	raw_project = data.get("project", {})

	if not isinstance(listed_skills, list):
		raise ValueError("skills must be a list")
	if not isinstance(projects, list):
		raise ValueError("projects must be a list")
	if not isinstance(experience, list):
		raise ValueError("experience must be a list")
	if not isinstance(skill_sources, dict):
		raise ValueError("skill_sources must be a dictionary")
	if not isinstance(training_skills, list):
		raise ValueError("training_skills must be a list")
	if not isinstance(project_technology_skills, list):
		raise ValueError("project_technology_skills must be a list")
	if raw_technical_skills not in ({}, None) and not isinstance(raw_technical_skills, dict):
		raise ValueError("technical_skills must be an object")
	if raw_training not in ({}, None) and not isinstance(raw_training, dict):
		raise ValueError("training must be an object")
	if raw_project not in ({}, None) and not isinstance(raw_project, dict):
		raise ValueError("project must be an object")

	normalized_listed_skills = [_normalize_skill_name(item) for item in listed_skills]
	normalized_listed_skills = [item for item in normalized_listed_skills if item]
	listed_set = set(normalized_listed_skills)
	alias_index = _build_alias_index(normalized_listed_skills)
	result: dict[str, dict] = {}

	for skill in sorted(listed_set):
		result[skill] = _empty_skill_record(skill, listed=True)

	# Attach deterministic evidence for listed skills from structured sources.
	for skill, sources in skill_sources.items():
		normalized_skill = _normalize_skill_name(skill)
		if normalized_skill == "":
			continue

		if normalized_skill not in result:
			result[normalized_skill] = _empty_skill_record(
				normalized_skill,
				listed=normalized_skill in listed_set,
			)

		if isinstance(sources, list):
			for source in sources:
				if isinstance(source, str):
					_append_evidence(result[normalized_skill], source)

	for skill in training_skills:
		normalized_skill = _normalize_skill_name(skill)
		if normalized_skill == "":
			continue
		if normalized_skill not in result:
			result[normalized_skill] = _empty_skill_record(
				normalized_skill,
				listed=normalized_skill in listed_set,
			)
		_append_evidence(result[normalized_skill], "training")

	for skill in project_technology_skills:
		normalized_skill = _normalize_skill_name(skill)
		if normalized_skill == "":
			continue
		if normalized_skill not in result:
			result[normalized_skill] = _empty_skill_record(
				normalized_skill,
				listed=normalized_skill in listed_set,
			)
		_append_evidence(result[normalized_skill], "project.technologies")

	technical_source_map = {
		"programming_languages": "technical_skills.programming_languages",
		"databases": "technical_skills.databases",
		"web_technologies": "technical_skills.web_technologies",
		"tools": "technical_skills.tools",
	}
	if isinstance(raw_technical_skills, dict):
		for key, source in technical_source_map.items():
			items = raw_technical_skills.get(key, [])
			if not isinstance(items, list):
				continue
			for item in items:
				normalized_skill = _normalize_skill_name(item)
				if normalized_skill == "":
					continue
				if normalized_skill not in result:
					result[normalized_skill] = _empty_skill_record(
						normalized_skill,
						listed=normalized_skill in listed_set,
					)
				_append_evidence(result[normalized_skill], source)

	if isinstance(raw_training, dict):
		for key in ("manual_testing", "automation_testing"):
			items = raw_training.get(key, [])
			if not isinstance(items, list):
				continue
			for item in items:
				normalized_skill = _normalize_skill_name(item)
				if normalized_skill == "":
					continue
				if normalized_skill not in result:
					result[normalized_skill] = _empty_skill_record(
						normalized_skill,
						listed=normalized_skill in listed_set,
					)
				_append_evidence(result[normalized_skill], f"training.{key}")

	if isinstance(raw_project, dict):
		project_tech_list = raw_project.get("technologies", [])
		if isinstance(project_tech_list, list):
			for item in project_tech_list:
				normalized_skill = _normalize_skill_name(item)
				if normalized_skill == "":
					continue
				if normalized_skill not in result:
					result[normalized_skill] = _empty_skill_record(
						normalized_skill,
						listed=normalized_skill in listed_set,
					)
				_append_evidence(result[normalized_skill], "project.technologies")

	for project in projects:
		if not isinstance(project, dict):
			continue
		description = project.get("description", "")
		if not isinstance(description, str) or description == "":
			continue

		for canonical in sorted(alias_index.keys()):
			mentions = _count_non_overlapping_mentions(description, alias_index[canonical])
			if mentions <= 0:
				continue

			if canonical not in result:
				result[canonical] = _empty_skill_record(
					canonical,
					listed=canonical in listed_set,
				)

			result[canonical]["projects"] += mentions
			_append_evidence(result[canonical], description)

	for role in experience:
		if not isinstance(role, dict):
			continue

		description = role.get("description", "")
		if not isinstance(description, str) or description == "":
			continue
		months = _parse_duration_months(role.get("duration", ""))

		for canonical in sorted(alias_index.keys()):
			mentions = _count_non_overlapping_mentions(description, alias_index[canonical])
			if mentions <= 0:
				continue

			if canonical not in result:
				result[canonical] = _empty_skill_record(
					canonical,
					listed=canonical in listed_set,
				)

			result[canonical]["experience_months"] += months
			_append_evidence(result[canonical], description)

	for skill_name, payload in result.items():
		if payload.get("listed") and not payload.get("evidence"):
			# Keep evidence non-empty for listed skills even when only provided in flat lists.
			_append_evidence(payload, "skills")
		payload["name"] = skill_name
		if not payload.get("evidence"):
			logger.warning("No evidence for skill: %s", skill_name)
		logger.debug("Evidence for %s: %s", skill_name, payload.get("evidence", []))

	final_result = dict(sorted(result.items(), key=lambda item: item[0]))
	logger.debug("Found %d skills", len(final_result))
	logger.debug("Mapper output: %s", final_result)
	return final_result
