"""Assign deterministic learning phases from an ordered skill list."""

from __future__ import annotations


def assign_phases(ordered_skills: list[str], phase_size: int = 3) -> list[dict]:
    if phase_size <= 0:
        raise ValueError("phase_size must be greater than zero")

    phases: list[dict] = []
    phase_index = 1
    for start in range(0, len(ordered_skills), phase_size):
        chunk = ordered_skills[start : start + phase_size]
        phases.append(
            {
                "phase": phase_index,
                "title": f"Phase {phase_index}",
                "skills": chunk,
            }
        )
        phase_index += 1

    return phases
