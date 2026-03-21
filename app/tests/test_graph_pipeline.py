from modules.graph.cycle_detector import detect_cycle
from modules.graph.graph_engine import SkillGraph
from modules.graph.phase_assigner import assign_phases
from modules.graph.pruning_engine import prune_sequence
from modules.graph.subgraph_extractor import extract_subgraph
from modules.graph.topological_sort import topo_sort
from modules.pathway.pathway_builder import build_pathway
from modules.pathway.response_builder import build_pathway_response


def _graph() -> SkillGraph:
    return SkillGraph(
        nodes={"python", "sql", "statistics", "machine learning", "deep learning"},
        edges=[
            ("python", "machine learning"),
            ("sql", "machine learning"),
            ("statistics", "machine learning"),
            ("machine learning", "deep learning"),
        ],
    )


def test_cycle_detector_no_cycle() -> None:
    has_cycle, path = detect_cycle(_graph())
    assert has_cycle is False
    assert path == []


def test_extract_subgraph_and_toposort() -> None:
    nodes, edges = extract_subgraph(_graph(), ["deep learning"])
    order = topo_sort(nodes, edges)

    assert "deep learning" in order
    assert order.index("machine learning") < order.index("deep learning")


def test_prune_and_phase_assign() -> None:
    order = ["python", "sql", "statistics", "machine learning", "deep learning"]
    pruned = prune_sequence(order, {"python", "sql"})
    phases = assign_phases(pruned, phase_size=2)

    assert pruned == ["statistics", "machine learning", "deep learning"]
    assert len(phases) == 2


def test_build_pathway_and_response() -> None:
    pathway = build_pathway(
        missing_skills=["deep learning"],
        candidate_skills={"python", "sql"},
        graph=_graph(),
    )
    response = build_pathway_response(pathway)

    assert response["meta"]["total_items"] >= 1
    assert response["meta"]["total_phases"] >= 1
    assert isinstance(response["phases"], list)
    flattened = [item for phase in response["phases"] for item in phase["items"]]
    assert flattened
    assert all("score" in item for item in flattened)
