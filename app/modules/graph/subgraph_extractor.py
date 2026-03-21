"""Subgraph extraction for missing/weak target skills."""

from __future__ import annotations

from modules.graph.graph_engine import SkillGraph


def extract_subgraph(graph: SkillGraph, target_skills: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    targets = [skill.strip().lower() for skill in target_skills if isinstance(skill, str) and skill.strip()]
    visited: set[str] = set()

    def _visit(skill: str) -> None:
        if skill in visited or not graph.contains(skill):
            return
        visited.add(skill)
        for parent in graph.prerequisites_of(skill):
            _visit(parent)

    for target in sorted(set(targets)):
        _visit(target)

    nodes = sorted(visited)
    edges = [
        (source, target)
        for source, target in graph.edges
        if source in visited and target in visited
    ]
    return nodes, sorted(edges)
