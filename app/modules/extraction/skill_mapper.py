"""Deterministic skill mapping from structured resume fields."""

from __future__ import annotations

import re
from collections import defaultdict


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


def _empty_skill_record(name: str, listed: bool) -> dict:
	return {
		"name": name,
		"listed": listed,
		"projects": 0,
		"experience_months": 0,
		"evidence": [],
	}


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
	listed_skills = data.get("skills", [])
	projects = data.get("projects", [])
	experience = data.get("experience", [])

	if not isinstance(listed_skills, list):
		raise ValueError("skills must be a list")
	if not isinstance(projects, list):
		raise ValueError("projects must be a list")
	if not isinstance(experience, list):
		raise ValueError("experience must be a list")

	listed_set = set(listed_skills)
	alias_index = _build_alias_index(listed_skills)
	result: dict[str, dict] = {}

	for skill in sorted(listed_set):
		result[skill] = _empty_skill_record(skill, listed=True)

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
			if description not in result[canonical]["evidence"]:
				result[canonical]["evidence"].append(description)

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
			if description not in result[canonical]["evidence"]:
				result[canonical]["evidence"].append(description)

	return dict(sorted(result.items(), key=lambda item: item[0]))
