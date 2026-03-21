import pytest
from pydantic import ValidationError

from modules.graph.graph_engine import GraphDiagnostics, SkillGraph
from modules.pathway.pathway_builder import build_pathway
from modules.pathway.response_builder import build_pathway_response
from schemas.pathway import PathwayResponse


def _acyclic_graph() -> SkillGraph:
    return SkillGraph(
        nodes={"python", "sql", "ml", "deep"},
        edges=[("python", "ml"), ("sql", "ml"), ("ml", "deep")],
    )


def _cyclic_graph() -> SkillGraph:
    return SkillGraph(
        nodes={"a", "b", "c"},
        edges=[("a", "b"), ("b", "c"), ("c", "a")],
    )


def test_build_pathway_raises_for_cycle() -> None:
    with pytest.raises(ValueError, match="Graph contains cycle"):
        build_pathway(missing_skills=["a"], graph=_cyclic_graph())


def test_build_pathway_returns_empty_when_all_met() -> None:
    result = build_pathway(
        missing_skills=["ml"],
        candidate_skills={"python", "sql", "ml"},
        graph=_acyclic_graph(),
    )
    assert result["ordered"] == []
    assert result["phases"] == []
    assert result["meta"]["total_items"] == 0
    assert result["meta"]["total_phases"] == 0
    assert result["meta"]["reason_code"] == "empty_target_set"


def test_build_pathway_ignores_unknown_targets() -> None:
    result = build_pathway(
        missing_skills=["unknown", "deep"],
        candidate_skills={"python"},
        graph=_acyclic_graph(),
    )

    assert "deep" in result["ordered"]
    assert "unknown" not in result["ordered"]


def test_build_pathway_is_deterministic() -> None:
    first = build_pathway(
        missing_skills=["deep", "ml"],
        candidate_skills={"python"},
        graph=_acyclic_graph(),
    )
    second = build_pathway(
        missing_skills=["ml", "deep"],
        candidate_skills={"python"},
        graph=_acyclic_graph(),
    )
    assert first == second


def test_response_builder_global_order_increment() -> None:
    response = build_pathway_response(
        {
            "phases": [
                {
                    "phase": 1,
                    "title": "Phase 1",
                    "skills": [
                        {"skill": "python", "score": 0.8, "prereq_count": 0},
                        {"skill": "sql", "score": 0.6, "prereq_count": 1},
                    ],
                },
                {
                    "phase": 2,
                    "title": "Phase 2",
                    "skills": [{"skill": "ml", "score": 0.7, "prereq_count": 2}],
                },
            ],
            "meta": {"total_items": 3, "total_phases": 2},
        }
    )
    flattened = [item for phase in response["phases"] for item in phase["items"]]
    assert [item["order"] for item in flattened] == [1, 2, 3]
    assert all(0.0 <= item["score"] <= 1.0 for item in flattened)


def test_pathway_schema_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        PathwayResponse(
            phases=[],
            meta={"total_items": 0, "total_phases": 0},
            unexpected=True,
        )


def test_build_pathway_empty_targets_reason_code() -> None:
    result = build_pathway(missing_skills=[], graph=_acyclic_graph())
    assert result["meta"]["reason_code"] == "empty_target_set"


def test_build_pathway_scoring_unavailable_reason_code(monkeypatch) -> None:
    import modules.pathway.pathway_builder as builder

    def _raise_scoring(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(builder, "score_pathway_items", _raise_scoring)

    result = build_pathway(
        missing_skills=["deep"],
        candidate_skills={"python"},
        graph=_acyclic_graph(),
    )

    assert result["meta"]["reason_code"] == "scoring_unavailable"


def test_build_pathway_includes_graph_diagnostics(monkeypatch) -> None:
    import modules.pathway.pathway_builder as builder

    diagnostics = GraphDiagnostics(
        version="v1",
        duplicate_edges=[("a", "b")],
        self_loops=[],
        unknown_edges=[("x", "y")],
        orphan_nodes=["solo"],
    )

    monkeypatch.setattr(builder, "load_graph_with_diagnostics", lambda: (_acyclic_graph(), diagnostics))

    result = build_pathway(
        missing_skills=["deep"],
        candidate_skills={"python"},
    )

    assert result["meta"]["graph_diagnostics"] == {
        "version": "v1",
        "duplicate_edges_count": 1,
        "self_loops_count": 0,
        "unknown_edges_count": 1,
        "orphan_nodes_count": 1,
    }


def test_response_builder_includes_graph_diagnostics_in_meta() -> None:
    response = build_pathway_response(
        {
            "phases": [
                {
                    "phase": 1,
                    "title": "Phase 1",
                    "skills": [
                        {"skill": "python", "score": 0.8, "prereq_count": 0},
                    ],
                }
            ],
            "meta": {
                "total_items": 1,
                "total_phases": 1,
                "reason_code": "ok",
                "graph_diagnostics": {
                    "version": "v1",
                    "duplicate_edges_count": 0,
                    "self_loops_count": 0,
                    "unknown_edges_count": 0,
                    "orphan_nodes_count": 0,
                },
            },
        }
    )

    assert response["meta"]["graph_diagnostics"]["version"] == "v1"
    assert response["meta"]["graph_diagnostics"]["unknown_edges_count"] == 0
