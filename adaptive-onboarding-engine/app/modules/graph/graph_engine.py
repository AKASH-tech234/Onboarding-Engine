"""
app/modules/graph/graph_engine.py

Lightweight graph engine backed by adjacency lists.

Features:
- loads `graph_data/base_graph.v1.json`
- builds forward and reverse adjacency lists
- exposes prerequisite and dependent lookups

Edge direction:
  from -> to

This means:
  `to` depends on `from`
  `from` is a prerequisite of `to`
"""

from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from collections import deque
from collections.abc import Mapping
from typing import Any

try:
    from graph.models import Importance, SkillEdge, SkillNode
    from utils.errors import GraphLoadError, GraphNotLoadedError
except ImportError:  # pragma: no cover - alternate package roots
    try:
        from app.modules.graph.models import Importance, SkillEdge, SkillNode
        from app.utils.errors import GraphLoadError, GraphNotLoadedError
    except ImportError:  # pragma: no cover - direct file fallback
        def _load_module(module_name: str, file_path: Path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)
            return module

        _models = _load_module(
            "_graph_models_fallback",
            Path(__file__).resolve().with_name("models.py"),
        )
        _errors = _load_module(
            "_graph_errors_fallback",
            Path(__file__).resolve().parents[2] / "utils" / "errors.py",
        )

        Importance = _models.Importance
        SkillEdge = _models.SkillEdge
        SkillNode = _models.SkillNode
        GraphLoadError = _errors.GraphLoadError
        GraphNotLoadedError = _errors.GraphNotLoadedError


class GraphEngine:
    """Graph loader and adjacency-list query engine."""

    def __init__(self, graph_path: str | Path | None = None) -> None:
        self.graph_path = Path(graph_path) if graph_path is not None else self._default_graph_path()
        self._loaded = False
        self.version: str | None = None
        self.nodes: dict[str, SkillNode] = {}
        self.edges: list[SkillEdge] = []
        self.adjacency_list: dict[str, list[str]] = {}
        self.reverse_adjacency_list: dict[str, list[str]] = {}
        self._outgoing_edges: dict[str, list[SkillEdge]] = {}
        self._incoming_edges: dict[str, list[SkillEdge]] = {}
        self._staged_nodes: dict[str, SkillNode] = {}
        self._staged_edges: list[SkillEdge] = []

    def load_graph(
        self,
        version: str = "v1",
        graph_data_dir: str | Path | None = None,
    ) -> GraphEngine:
        """
        Load graph data from disk.

        By default this reads:
        `adaptive-onboarding-engine/graph_data/base_graph.v1.json`
        """
        path = self._resolve_graph_path(version=version, graph_data_dir=graph_data_dir)

        try:
            raw_text = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise GraphLoadError(f"Graph file not found: {path}") from error

        if not raw_text.strip():
            self.load_from_dict({"version": version, "nodes": [], "edges": []})
            self.graph_path = path
            return self

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as error:
            raise GraphLoadError(f"Graph file is not valid JSON: {error}") from error

        self.load_from_dict(data)
        self.graph_path = path
        return self

    def load_from_dict(self, data: Mapping[str, Any] | None) -> GraphEngine:
        """Load graph data directly from a parsed dictionary."""
        if not isinstance(data, Mapping):
            raise GraphLoadError("Graph data must be a mapping")
        if not isinstance(data.get("version"), str):
            raise GraphLoadError("Graph data must include a string 'version'")
        if not isinstance(data.get("nodes"), list):
            raise GraphLoadError("Graph data must include a 'nodes' list")
        if not isinstance(data.get("edges"), list):
            raise GraphLoadError("Graph data must include an 'edges' list")

        nodes: dict[str, SkillNode] = {}
        adjacency: dict[str, list[str]] = {}
        reverse_adjacency: dict[str, list[str]] = {}
        outgoing_edges: dict[str, list[SkillEdge]] = {}
        incoming_edges: dict[str, list[SkillEdge]] = {}

        for index, raw_node in enumerate(data["nodes"]):
            if not isinstance(raw_node, Mapping):
                raise GraphLoadError(f"Node at index {index} must be an object")

            node_id = raw_node.get("id")
            if not isinstance(node_id, str) or not node_id.strip():
                raise GraphLoadError(f"Node at index {index} is missing a valid 'id'")

            node_id = node_id.strip()
            if node_id in nodes:
                raise GraphLoadError(f"Duplicate node id: '{node_id}'")

            try:
                node = SkillNode(
                    id=node_id,
                    label=str(raw_node.get("label", node_id)),
                    domain=str(raw_node.get("domain", "general")),
                    base_effort_days=int(raw_node.get("base_effort_days", 3)),
                    difficulty=int(raw_node.get("difficulty", 3)),
                    tags=tuple(raw_node.get("tags", [])),
                    source=str(raw_node.get("source", "curated")),
                )
            except (TypeError, ValueError) as error:
                raise GraphLoadError(f"Invalid node '{node_id}': {error}") from error

            nodes[node_id] = node
            adjacency[node_id] = []
            reverse_adjacency[node_id] = []
            outgoing_edges[node_id] = []
            incoming_edges[node_id] = []

        edges: list[SkillEdge] = []
        seen_edges: set[tuple[str, str]] = set()

        for index, raw_edge in enumerate(data["edges"]):
            if not isinstance(raw_edge, Mapping):
                raise GraphLoadError(f"Edge at index {index} must be an object")

            from_id = raw_edge.get("from")
            to_id = raw_edge.get("to")

            if not isinstance(from_id, str) or not from_id.strip():
                raise GraphLoadError(f"Edge at index {index} is missing a valid 'from'")
            if not isinstance(to_id, str) or not to_id.strip():
                raise GraphLoadError(f"Edge at index {index} is missing a valid 'to'")

            from_id = from_id.strip()
            to_id = to_id.strip()

            if from_id not in nodes:
                raise GraphLoadError(f"Edge references unknown source node: '{from_id}'")
            if to_id not in nodes:
                raise GraphLoadError(f"Edge references unknown target node: '{to_id}'")

            edge_key = (from_id, to_id)
            if edge_key in seen_edges:
                raise GraphLoadError(f"Duplicate edge: '{from_id}' -> '{to_id}'")
            seen_edges.add(edge_key)

            importance_value = str(raw_edge.get("importance", Importance.MANDATORY.value))
            try:
                importance = Importance(importance_value)
            except ValueError as error:
                raise GraphLoadError(
                    f"Invalid importance '{importance_value}' on edge '{from_id}' -> '{to_id}'"
                ) from error

            default_weight = 1.0 if importance == Importance.MANDATORY else 0.5
            try:
                weight = float(raw_edge.get("weight", default_weight))
            except (TypeError, ValueError) as error:
                raise GraphLoadError(
                    f"Invalid weight on edge '{from_id}' -> '{to_id}'"
                ) from error

            try:
                edge = SkillEdge(
                    from_id=from_id,
                    to_id=to_id,
                    importance=importance,
                    weight=weight,
                )
            except ValueError as error:
                raise GraphLoadError(f"Invalid edge '{from_id}' -> '{to_id}': {error}") from error

            edges.append(edge)
            adjacency[from_id].append(to_id)
            reverse_adjacency[to_id].append(from_id)
            outgoing_edges[from_id].append(edge)
            incoming_edges[to_id].append(edge)

        for node_id in adjacency:
            adjacency[node_id].sort()
            reverse_adjacency[node_id].sort()
            outgoing_edges[node_id].sort(key=lambda edge: edge.to_id)
            incoming_edges[node_id].sort(key=lambda edge: edge.from_id)

        self.version = data["version"]
        self.nodes = nodes
        self.edges = edges
        self.adjacency_list = adjacency
        self.reverse_adjacency_list = reverse_adjacency
        self._outgoing_edges = outgoing_edges
        self._incoming_edges = incoming_edges
        self._loaded = True
        return self

    def is_loaded(self) -> bool:
        return self._loaded

    def get_prerequisites(self, skill: str) -> list[str]:
        """Return direct prerequisites of a skill."""
        self._ensure_loaded()
        return list(self.reverse_adjacency_list.get(skill, []))

    def get_dependents(self, skill: str) -> list[str]:
        """Return direct dependents of a skill."""
        self._ensure_loaded()
        return list(self.adjacency_list.get(skill, []))

    def get_predecessor_ids(self, skill: str) -> list[str]:
        return self.get_prerequisites(skill)

    def get_successor_ids(self, skill: str) -> list[str]:
        return self.get_dependents(skill)

    def get_predecessor_edges(self, skill: str) -> list[SkillEdge]:
        self._ensure_loaded()
        return list(self._incoming_edges.get(skill, []))

    def get_successor_edges(self, skill: str) -> list[SkillEdge]:
        self._ensure_loaded()
        return list(self._outgoing_edges.get(skill, []))

    def get_node(self, skill: str) -> SkillNode | None:
        self._ensure_loaded()
        return self.nodes.get(skill)

    def resolve_node(self, skill: str) -> SkillNode | None:
        self._ensure_loaded()
        return self.nodes.get(skill) or self._staged_nodes.get(skill)

    def has_node(self, skill: str) -> bool:
        self._ensure_loaded()
        return skill in self.nodes

    def get_node_ids(self) -> list[str]:
        self._ensure_loaded()
        return list(self.nodes.keys())

    def get_node_count(self) -> int:
        self._ensure_loaded()
        return len(self.nodes)

    def get_edge_count(self) -> int:
        self._ensure_loaded()
        return len(self.edges)

    def get_version(self) -> str | None:
        return self.version

    def get_all_ancestors(self, skill: str) -> set[str]:
        """Return all transitive prerequisites of a skill."""
        self._ensure_loaded()
        return self._traverse(start=skill, graph=self.reverse_adjacency_list)

    def get_all_descendants(self, skill: str) -> set[str]:
        """Return all transitive dependents of a skill."""
        self._ensure_loaded()
        return self._traverse(start=skill, graph=self.adjacency_list)

    def get_metadata(self) -> dict[str, Any]:
        self._ensure_loaded()
        domains = sorted({node.domain for node in self.nodes.values()})
        return {
            "version": self.version,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "domains": domains,
            "graph_path": str(self.graph_path),
        }

    def stage_node(self, node: SkillNode, edges: list[SkillEdge] | None = None) -> None:
        self._staged_nodes[node.id] = node
        if edges:
            self._staged_edges.extend(edges)

    def get_staged_node(self, skill: str) -> SkillNode | None:
        return self._staged_nodes.get(skill)

    def get_staged_predecessor_edges(self, skill: str) -> list[SkillEdge]:
        return [edge for edge in self._staged_edges if edge.to_id == skill]

    def reset(self) -> None:
        self._loaded = False
        self.version = None
        self.nodes = {}
        self.edges = []
        self.adjacency_list = {}
        self.reverse_adjacency_list = {}
        self._outgoing_edges = {}
        self._incoming_edges = {}
        self._staged_nodes = {}
        self._staged_edges = []

    @staticmethod
    def _default_graph_path() -> Path:
        return Path(__file__).resolve().parents[3] / "graph_data" / "base_graph.v1.json"

    def _resolve_graph_path(
        self,
        version: str,
        graph_data_dir: str | Path | None,
    ) -> Path:
        if graph_data_dir is None:
            if version == "v1":
                return self._default_graph_path()
            return self._default_graph_path().with_name(f"base_graph.{version}.json")

        return Path(graph_data_dir) / f"base_graph.{version}.json"

    def _ensure_loaded(self) -> None:
        if not self.is_loaded():
            raise GraphNotLoadedError("Graph not loaded. Call load_graph() first.")

    @staticmethod
    def _traverse(start: str, graph: Mapping[str, list[str]]) -> set[str]:
        if start not in graph:
            return set()

        visited: set[str] = set()
        queue = deque(graph[start])

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(graph.get(node, []))

        return visited


_ENGINE = GraphEngine()


def load_graph(version: str = "v1", graph_data_dir: str | Path | None = None) -> GraphEngine:
    return _ENGINE.load_graph(version=version, graph_data_dir=graph_data_dir)


def load_graph_from_dict(data: Mapping[str, Any] | None) -> GraphEngine:
    return _ENGINE.load_from_dict(data)


def is_loaded() -> bool:
    return _ENGINE.is_loaded()


def get_version() -> str | None:
    return _ENGINE.get_version()


def get_node(skill: str) -> SkillNode | None:
    return _ENGINE.get_node(skill)


def resolve_node(skill: str) -> SkillNode | None:
    return _ENGINE.resolve_node(skill)


def has_node(skill: str) -> bool:
    return _ENGINE.has_node(skill)


def get_node_ids() -> list[str]:
    return _ENGINE.get_node_ids()


def get_node_count() -> int:
    return _ENGINE.get_node_count()


def get_edge_count() -> int:
    return _ENGINE.get_edge_count()


def get_prerequisites(skill: str) -> list[str]:
    return _ENGINE.get_prerequisites(skill)


def get_dependents(skill: str) -> list[str]:
    return _ENGINE.get_dependents(skill)


def get_predecessor_ids(skill: str) -> list[str]:
    return _ENGINE.get_predecessor_ids(skill)


def get_successor_ids(skill: str) -> list[str]:
    return _ENGINE.get_successor_ids(skill)


def get_predecessor_edges(skill: str) -> list[SkillEdge]:
    return _ENGINE.get_predecessor_edges(skill)


def get_successor_edges(skill: str) -> list[SkillEdge]:
    return _ENGINE.get_successor_edges(skill)


def get_all_ancestors(skill: str) -> set[str]:
    return _ENGINE.get_all_ancestors(skill)


def get_all_descendants(skill: str) -> set[str]:
    return _ENGINE.get_all_descendants(skill)


def get_staged_node(skill: str) -> SkillNode | None:
    return _ENGINE.get_staged_node(skill)


def get_staged_predecessor_edges(skill: str) -> list[SkillEdge]:
    return _ENGINE.get_staged_predecessor_edges(skill)


def stage_node(node: SkillNode, edges: list[SkillEdge] | None = None) -> None:
    _ENGINE.stage_node(node, edges)


def get_metadata() -> dict[str, Any]:
    return _ENGINE.get_metadata()


def reset_for_tests() -> None:
    _ENGINE.reset()


__all__ = [
    "GraphEngine",
    "SkillNode",
    "SkillEdge",
    "load_graph",
    "load_graph_from_dict",
    "get_prerequisites",
    "get_dependents",
]
