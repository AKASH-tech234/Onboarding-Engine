"""Deterministic pathway orchestration from missing skills."""

from __future__ import annotations

from modules.graph.cycle_detector import detect_cycle
from modules.graph.graph_engine import GraphDiagnostics, SkillGraph, load_graph_with_diagnostics
from modules.graph.phase_assigner import assign_phases
from modules.graph.pruning_engine import prune_sequence
from modules.graph.subgraph_extractor import extract_subgraph
from modules.graph.topological_sort import topo_sort
from modules.scoring.pathway_scoring import score_pathway_items
from modules.utils.logger import get_logger


logger = get_logger("pathway")

PATHWAY_REASON_OK = "ok"
PATHWAY_REASON_CYCLE_DETECTED = "cycle_detected"
PATHWAY_REASON_GRAPH_MISSING = "graph_missing"
PATHWAY_REASON_EMPTY_TARGET_SET = "empty_target_set"
PATHWAY_REASON_SCORING_UNAVAILABLE = "scoring_unavailable"


def _empty_pathway(reason_code: str) -> dict:
    return {
        "ordered": [],
        "phases": [],
        "meta": {
            "total_items": 0,
            "total_phases": 0,
            "reason_code": reason_code,
        },
    }


def _serialize_graph_diagnostics(diagnostics: GraphDiagnostics | None) -> dict | None:
    if diagnostics is None:
        return None
    return {
        "version": diagnostics.version,
        "duplicate_edges_count": len(diagnostics.duplicate_edges),
        "self_loops_count": len(diagnostics.self_loops),
        "unknown_edges_count": len(diagnostics.unknown_edges),
        "orphan_nodes_count": len(diagnostics.orphan_nodes),
    }


def build_pathway(
    missing_skills: list[str],
    candidate_skills: set[str] | None = None,
    graph: SkillGraph | None = None,
    phase_size: int = 3,
) -> dict:
    normalized_missing = sorted({str(item).strip().lower() for item in missing_skills if str(item).strip()})
    if not normalized_missing:
        return _empty_pathway(PATHWAY_REASON_EMPTY_TARGET_SET)

    diagnostics: GraphDiagnostics | None = None
    try:
        if graph is None:
            active_graph, diagnostics = load_graph_with_diagnostics()
        else:
            active_graph = graph
    except ValueError as exc:
        raise ValueError(f"{PATHWAY_REASON_GRAPH_MISSING}: {exc}") from exc

    if diagnostics is not None and (
        diagnostics.duplicate_edges
        or diagnostics.self_loops
        or diagnostics.unknown_edges
        or diagnostics.orphan_nodes
    ):
        logger.warning(
            "Graph diagnostics anomalies: dup=%d self_loops=%d unknown=%d orphans=%d",
            len(diagnostics.duplicate_edges),
            len(diagnostics.self_loops),
            len(diagnostics.unknown_edges),
            len(diagnostics.orphan_nodes),
        )

    has_cycle, cycle_path = detect_cycle(active_graph)
    if has_cycle:
        raise ValueError(
            f"{PATHWAY_REASON_CYCLE_DETECTED}: Graph contains cycle: {' -> '.join(cycle_path)}"
        )

    nodes, edges = extract_subgraph(active_graph, normalized_missing)
    logger.debug("Pathway subgraph nodes=%d edges=%d", len(nodes), len(edges))

    ordered = topo_sort(nodes, edges)
    pruned = prune_sequence(ordered, candidate_skills or set())
    if not pruned:
        return _empty_pathway(PATHWAY_REASON_EMPTY_TARGET_SET)

    prereq_counts = {skill: len(active_graph.prerequisites_of(skill)) for skill in pruned}
    reason_code = PATHWAY_REASON_OK
    try:
        score_map = score_pathway_items(pruned, prereq_counts)
    except Exception:
        logger.warning("Pathway scoring unavailable; falling back to zero scores")
        score_map = {skill: 0.0 for skill in pruned}
        reason_code = PATHWAY_REASON_SCORING_UNAVAILABLE

    phases_raw = assign_phases(pruned, phase_size=phase_size)

    phases: list[dict] = []
    for phase in phases_raw:
        phase_skills: list[dict] = []
        for skill in phase.get("skills", []):
            phase_skills.append(
                {
                    "skill": skill,
                    "score": score_map.get(skill, 0.0),
                    "prereq_count": prereq_counts.get(skill, 0),
                }
            )
        phases.append(
            {
                "phase": phase.get("phase"),
                "title": phase.get("title"),
                "skills": phase_skills,
            }
        )

    return {
        "ordered": pruned,
        "phases": phases,
        "meta": {
            "total_items": len(pruned),
            "total_phases": len(phases),
            "reason_code": reason_code,
            "graph_diagnostics": _serialize_graph_diagnostics(diagnostics),
        },
    }
