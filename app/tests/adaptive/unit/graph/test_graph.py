"""Unit tests for graph modules."""

from __future__ import annotations

import unittest
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[5]

import app.adaptive.modules.graph.graph_engine as graph_engine
from app.adaptive.modules.graph.topological_sort import CycleError, topological_sort
from app.adaptive.utils.errors import GraphLoadError


class TestGraphEngine(unittest.TestCase):
    """Starter tests for graph loading and basic traversal helpers."""

    def setUp(self) -> None:
        graph_engine.reset_for_tests()

    def test_load_from_dict_and_query_relationships(self) -> None:
        graph_engine.load_graph_from_dict(
            {
                "version": "v1",
                "nodes": [
                    {"id": "linux", "label": "Linux", "domain": "ops", "base_effort_days": 3, "difficulty": 2},
                    {"id": "docker", "label": "Docker", "domain": "ops", "base_effort_days": 4, "difficulty": 3},
                    {"id": "kubernetes", "label": "Kubernetes", "domain": "ops", "base_effort_days": 6, "difficulty": 4},
                ],
                "edges": [
                    {"from": "linux", "to": "docker", "importance": "mandatory", "weight": 1.0},
                    {"from": "docker", "to": "kubernetes", "importance": "mandatory", "weight": 1.0},
                ],
            }
        )

        self.assertEqual(graph_engine.get_prerequisites("docker"), ["linux"])
        self.assertEqual(graph_engine.get_dependents("docker"), ["kubernetes"])
        self.assertEqual(graph_engine.get_all_ancestors("kubernetes"), {"linux", "docker"})
        self.assertEqual(graph_engine.get_all_descendants("linux"), {"docker", "kubernetes"})

    def test_load_graph_accepts_empty_file_as_empty_graph(self) -> None:
        temp_dir = PROJECT_ROOT / "tests" / ".tmp_graph_engine"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            base_graph = temp_dir / "base_graph.v1.json"
            base_graph.write_text("", encoding="utf-8")

            engine = graph_engine.load_graph(version="v1", graph_data_dir=temp_dir)
            self.assertTrue(engine.is_loaded())
            self.assertEqual(engine.get_node_count(), 0)
            self.assertEqual(engine.get_edge_count(), 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_invalid_edges_raise_graph_load_error(self) -> None:
        with self.assertRaises(GraphLoadError):
            graph_engine.load_graph_from_dict(
                {
                    "version": "v1",
                    "nodes": [
                        {"id": "a", "label": "A", "domain": "general", "base_effort_days": 1, "difficulty": 1},
                    ],
                    "edges": [
                        {"from": "a", "to": "missing", "importance": "mandatory", "weight": 1.0},
                    ],
                }
            )


class TestTopologicalSort(unittest.TestCase):
    """Starter tests for Kahn-style topological sorting."""

    def test_topological_sort_orders_prerequisites_first(self) -> None:
        graph = {
            "linux": ["docker"],
            "docker": ["kubernetes"],
            "kubernetes": [],
        }

        order = topological_sort(graph)
        self.assertLess(order.index("linux"), order.index("docker"))
        self.assertLess(order.index("docker"), order.index("kubernetes"))

    def test_topological_sort_raises_on_cycle(self) -> None:
        cyclic_graph = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        }

        with self.assertRaises(CycleError):
            topological_sort(cyclic_graph)


if __name__ == "__main__":
    unittest.main()
