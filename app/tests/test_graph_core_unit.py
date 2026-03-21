import json

import pytest

from modules.graph.cycle_detector import detect_cycle
from modules.graph.graph_engine import SkillGraph, load_graph, load_graph_with_diagnostics
from modules.graph.phase_assigner import assign_phases
from modules.graph.pruning_engine import prune_sequence
from modules.graph.subgraph_extractor import extract_subgraph
from modules.graph.topological_sort import topo_sort


def _write_graph(tmp_path, payload: dict) -> str:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_load_graph_normalizes_and_filters(tmp_path) -> None:
    payload = {
        "nodes": [
            {"id": " Python "},
            {"id": "SQL"},
            {"id": ""},
            {"name": "bad"},
        ],
        "edges": [
            {"from": "Python", "to": "SQL"},
            {"from": "python", "to": "sql"},
            {"from": "SQL", "to": "SQL"},
            {"from": "", "to": "python"},
            {"from": "unknown", "to": "python"},
        ],
    }
    graph = load_graph(_write_graph(tmp_path, payload))

    assert graph.nodes == {"python", "sql"}
    assert graph.edges == [("python", "sql")]
    assert graph.prerequisites_of("sql") == ["python"]


def test_load_graph_with_diagnostics_reports_quality_issues(tmp_path) -> None:
    payload = {
        "version": "v9",
        "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "a", "to": "b"},
            {"from": "B", "to": "B"},
            {"from": "X", "to": "A"},
        ],
    }
    graph, diagnostics = load_graph_with_diagnostics(_write_graph(tmp_path, payload))

    assert graph.edges == [("a", "b")]
    assert diagnostics.version == "v9"
    assert diagnostics.duplicate_edges == [("a", "b")]
    assert diagnostics.self_loops == [("b", "b")]
    assert diagnostics.unknown_edges == [("x", "a")]
    assert diagnostics.orphan_nodes == ["c"]


def test_load_graph_invalid_shape_raises(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_graph(str(path))


def test_load_graph_invalid_json_raises(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not_json}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid graph JSON"):
        load_graph(str(path))


def test_load_graph_missing_file_raises() -> None:
    with pytest.raises(ValueError, match="Graph file not found"):
        load_graph("does-not-exist.json")


def test_load_graph_version_resolution(tmp_path) -> None:
    payload = {
        "version": "v2",
        "nodes": [{"id": "python"}],
        "edges": [],
    }
    path = tmp_path / "base_graph.v2.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    graph = load_graph(path=str(path), version="v2")
    assert graph.nodes == {"python"}


def test_cycle_detector_returns_cycle_path() -> None:
    graph = SkillGraph(
        nodes={"a", "b", "c"},
        edges=[("a", "b"), ("b", "c"), ("c", "a")],
    )
    has_cycle, path = detect_cycle(graph)

    assert has_cycle is True
    assert path[0] == path[-1]
    assert set(path[:-1]) == {"a", "b", "c"}


def test_subgraph_excludes_unrelated_nodes() -> None:
    graph = SkillGraph(
        nodes={"python", "sql", "ml", "deep", "docker"},
        edges=[("python", "ml"), ("sql", "ml"), ("ml", "deep"), ("docker", "deep")],
    )
    nodes, edges = extract_subgraph(graph, ["ml"])

    assert nodes == ["ml", "python", "sql"]
    assert edges == [("python", "ml"), ("sql", "ml")]


def test_topo_sort_is_deterministic() -> None:
    nodes = ["ml", "python", "sql", "deep"]
    edges = [("python", "ml"), ("sql", "ml"), ("ml", "deep")]

    first = topo_sort(nodes, edges)
    second = topo_sort(nodes, edges)
    assert first == second
    assert first.index("ml") < first.index("deep")


def test_topo_sort_raises_on_cycle() -> None:
    with pytest.raises(ValueError, match="cycle"):
        topo_sort(["a", "b"], [("a", "b"), ("b", "a")])


def test_prune_sequence_normalizes_candidate_skills() -> None:
    ordered = ["python", "sql", "ml"]
    assert prune_sequence(ordered, {" Python ", "SQL"}) == ["ml"]


def test_phase_assigner_validates_phase_size() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        assign_phases(["a", "b"], phase_size=0)


def test_phase_assigner_partitions_deterministically() -> None:
    phases = assign_phases(["a", "b", "c", "d", "e"], phase_size=2)
    assert phases == [
        {"phase": 1, "title": "Phase 1", "skills": ["a", "b"]},
        {"phase": 2, "title": "Phase 2", "skills": ["c", "d"]},
        {"phase": 3, "title": "Phase 3", "skills": ["e"]},
    ]
