"""Graph loader and deterministic accessors for skill dependencies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from modules.utils.logger import get_logger


logger = get_logger("graph_engine")


@dataclass(frozen=True)
class GraphDiagnostics:
    version: str
    duplicate_edges: list[tuple[str, str]]
    self_loops: list[tuple[str, str]]
    unknown_edges: list[tuple[str, str]]
    orphan_nodes: list[str]


class SkillGraph:
    def __init__(self, nodes: set[str], edges: list[tuple[str, str]]) -> None:
        self.nodes = set(nodes)
        self.edges = list(edges)
        self.prereq_to_skill: dict[str, set[str]] = {node: set() for node in self.nodes}
        self.skill_to_prereq: dict[str, set[str]] = {node: set() for node in self.nodes}

        for source, target in self.edges:
            if source not in self.nodes or target not in self.nodes:
                continue
            self.prereq_to_skill[source].add(target)
            self.skill_to_prereq[target].add(source)

    def contains(self, skill: str) -> bool:
        return skill in self.nodes

    def prerequisites_of(self, skill: str) -> list[str]:
        return sorted(self.skill_to_prereq.get(skill, set()))


def _default_graph_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "graph_data"


def _default_graph_path(version: str = "v1") -> Path:
    return _default_graph_dir() / f"base_graph.{version}.json"


def _normalize_node_id(value: object) -> str:
    return str(value or "").strip().lower()


def _load_graph_payload(graph_path: Path) -> dict:
    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Graph file not found: {graph_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid graph JSON: {graph_path}") from exc

    if not isinstance(data, dict):
        raise ValueError("Graph payload must be a JSON object")

    raw_nodes = data.get("nodes", [])
    raw_edges = data.get("edges", [])
    if not isinstance(raw_nodes, list):
        raise ValueError("nodes must be a list")
    if not isinstance(raw_edges, list):
        raise ValueError("edges must be a list")

    return data


def load_graph_with_diagnostics(path: str | None = None, version: str = "v1") -> tuple[SkillGraph, GraphDiagnostics]:
    graph_path = Path(path) if path else _default_graph_path(version)
    data = _load_graph_payload(graph_path)

    file_version = str(data.get("version", version)).strip() or version
    raw_nodes = data.get("nodes", [])
    raw_edges = data.get("edges", [])

    nodes = {
        _normalize_node_id(item.get("id"))
        for item in raw_nodes
        if isinstance(item, dict) and _normalize_node_id(item.get("id"))
    }

    edge_counts: dict[tuple[str, str], int] = {}
    self_loops: set[tuple[str, str]] = set()
    unknown_edges: set[tuple[str, str]] = set()
    valid_edges: set[tuple[str, str]] = set()

    for edge in raw_edges:
        if not isinstance(edge, dict):
            continue

        source = _normalize_node_id(edge.get("from"))
        target = _normalize_node_id(edge.get("to"))
        if not source or not target:
            continue

        pair = (source, target)
        edge_counts[pair] = edge_counts.get(pair, 0) + 1

        if source == target:
            self_loops.add(pair)
            continue

        if source not in nodes or target not in nodes:
            unknown_edges.add(pair)
            continue

        valid_edges.add(pair)

    duplicate_edges = sorted([pair for pair, count in edge_counts.items() if count > 1])

    graph = SkillGraph(nodes=nodes, edges=sorted(valid_edges))
    orphan_nodes = sorted(
        [
            node
            for node in graph.nodes
            if not graph.prereq_to_skill.get(node) and not graph.skill_to_prereq.get(node)
        ]
    )

    diagnostics = GraphDiagnostics(
        version=file_version,
        duplicate_edges=duplicate_edges,
        self_loops=sorted(self_loops),
        unknown_edges=sorted(unknown_edges),
        orphan_nodes=orphan_nodes,
    )

    logger.debug(
        "Loaded graph version=%s nodes=%d edges=%d dup=%d self_loops=%d unknown=%d orphans=%d",
        diagnostics.version,
        len(graph.nodes),
        len(graph.edges),
        len(diagnostics.duplicate_edges),
        len(diagnostics.self_loops),
        len(diagnostics.unknown_edges),
        len(diagnostics.orphan_nodes),
    )
    return graph, diagnostics


def load_graph(path: str | None = None, version: str = "v1") -> SkillGraph:
    graph, _ = load_graph_with_diagnostics(path=path, version=version)
    return graph
