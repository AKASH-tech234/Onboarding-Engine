"""Cycle detection for deterministic DAG validation."""

from __future__ import annotations

from modules.graph.graph_engine import SkillGraph


def detect_cycle(graph: SkillGraph) -> tuple[bool, list[str]]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def _dfs(node: str) -> list[str] | None:
        visiting.add(node)
        stack.append(node)

        for child in sorted(graph.prereq_to_skill.get(node, set())):
            if child in visiting:
                cycle_start = stack.index(child)
                return stack[cycle_start:] + [child]
            if child in visited:
                continue
            found = _dfs(child)
            if found:
                return found

        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(graph.nodes):
        if node in visited:
            continue
        cycle = _dfs(node)
        if cycle:
            return True, cycle

    return False, []
