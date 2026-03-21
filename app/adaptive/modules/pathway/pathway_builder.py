"""
app/modules/pathway/pathway_builder.py

Orchestrates the dependency-aware pathway pipeline:
gap analysis -> subgraph -> topological sort -> pruning -> phase assignment -> scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from collections.abc import Mapping, Sequence

try:
    from app.adaptive.modules.graph import graph_engine
    from app.adaptive.modules.graph import phase_assigner, pruning_engine, subgraph_extractor, topological_sort
    from app.adaptive.modules.graph.models import CandidateSkillLevel, LearningMode, Phase, PrunedItem
    from app.adaptive.modules.scoring import scoring_engine
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.modules.graph import graph_engine, phase_assigner, pruning_engine, subgraph_extractor, topological_sort
    from app.adaptive.modules.graph.models import CandidateSkillLevel, LearningMode, Phase, PrunedItem
    from app.adaptive.modules.scoring import scoring_engine


class PathwayBuilderError(RuntimeError):
    """Raised when pathway orchestration cannot continue safely."""


@dataclass(frozen=True)
class PathwayItemResult:
    skill_id: str
    label: str
    domain: str
    phase_number: int
    proficiency_status: str
    current_proficiency: float
    required_proficiency: float
    gap_delta: float
    base_effort_days: int
    adjusted_effort_days: int
    composite_score: float
    unlock_count: int
    resources: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PathwayPhaseResult:
    phase_number: int
    focus_domain: str
    total_effort_days: int
    min_critical_level: int
    max_critical_level: int
    items: list[PathwayItemResult] = field(default_factory=list)


@dataclass(frozen=True)
class PathwayResult:
    candidate_id: str | None
    job_id: str | None
    pathway_type: str
    phases: list[PathwayPhaseResult]
    unresolved_ids: list[str]
    pruned_ids: list[str]
    trimmed_ids: list[str]
    phase_validation: dict[str, Any]
    total_effort_days: int
    total_items: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_items(self) -> list[PathwayItemResult]:
        items: list[PathwayItemResult] = []
        for phase in self.phases:
            items.extend(phase.items)
        return items


@dataclass(frozen=True)
class _GapState:
    candidate_id: str | None
    job_id: str | None
    pathway_type: str
    gap_skill_ids: list[str]
    met_skill_ids: list[str]
    candidate_levels: list[CandidateSkillLevel]
    per_skill_gap: dict[str, float]
    warnings: list[str]


def build_pathway(
    gap_analysis: Any,
    *,
    role: str | None = None,
    graph_version: str = "v1",
    time_budget_days: int | None = None,
    learning_mode: LearningMode | str = LearningMode.DEEP_LEARNING,
    max_days_per_phase: int = 7,
    max_items_per_phase: int = 5,
    group_by_domain: bool = True,
    importance_threshold: float = 0.0,
    include_staged_nodes: bool = True,
) -> PathwayResult:
    """
    Build a phased pathway from gap analysis output.

    Supports both:
    - dict output from current ingestion.gap_analyzer
    - GapAnalysis-like object with `.items`, `.missing`, `.weak`, `.strong`
    """
    state = _extract_gap_state(gap_analysis)
    mode = _coerce_learning_mode(learning_mode)

    if not state.gap_skill_ids:
        return _empty_result(state, mode=mode, graph_version=graph_version)

    _ensure_graph_loaded(graph_version=graph_version)

    subgraph = subgraph_extractor.extract_subgraph(
        state.gap_skill_ids,
        importance_threshold=importance_threshold,
        include_staged_nodes=include_staged_nodes,
        met_skill_ids=state.met_skill_ids,
    )

    if not subgraph.nodes:
        return _empty_result(
            state,
            mode=mode,
            graph_version=graph_engine.get_version() or graph_version,
            unresolved_ids=subgraph.unresolved_ids,
        )

    adjacency = _build_adjacency(subgraph.nodes.keys(), subgraph.edges)
    try:
        topo_order = topological_sort.topological_sort(adjacency)
    except Exception as error:
        raise PathwayBuilderError(f"Failed to topologically sort subgraph: {error}") from error

    pre_scores = _build_scores(
        skill_ids=topo_order,
        state=state,
        role=role,
        effort_override=None,
        within_ids=topo_order,
    )

    prune_result = pruning_engine.prune_and_compress(
        topo_order=topo_order,
        candidate_levels=state.candidate_levels,
        time_budget_days=time_budget_days,
        scores=pre_scores,
        learning_mode=mode,
    )

    retained_ids = [item.skill_id for item in prune_result.items]
    retained_edges = subgraph_extractor.get_edges_within_set(retained_ids) if retained_ids else []
    phases: list[Phase] = []
    phase_validation: dict[str, Any] = {"valid": True, "violations": []}
    final_scores: dict[str, float] = {}

    if retained_ids:
        phases = phase_assigner.assign_phases(
            items=prune_result.items,
            edges=retained_edges,
            max_days_per_phase=max_days_per_phase,
            max_items_per_phase=max_items_per_phase,
            group_by_domain=group_by_domain,
            learning_mode=mode,
        )
        validation = phase_assigner.validate_phase_order(phases, retained_edges)
        phase_validation = {"valid": validation.valid, "violations": validation.violations}

        effort_override = {item.skill_id: item.adjusted_effort_days for item in prune_result.items}
        final_scores = _build_scores(
            skill_ids=retained_ids,
            state=state,
            role=role,
            effort_override=effort_override,
            within_ids=retained_ids,
        )

    phase_results = _build_phase_results(
        phases=phases,
        pruned_items=prune_result.items,
        final_scores=final_scores,
        within_ids=retained_ids,
    )

    total_items = sum(len(phase.items) for phase in phase_results)
    total_effort_days = sum(phase.total_effort_days for phase in phase_results)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph_version": graph_engine.get_version() or graph_version,
        "learning_mode": mode.value,
        "role": role,
        "input_gap_count": len(state.gap_skill_ids),
        "retained_count": len(retained_ids),
        "warnings": state.warnings,
    }

    return PathwayResult(
        candidate_id=state.candidate_id,
        job_id=state.job_id,
        pathway_type=state.pathway_type,
        phases=phase_results,
        unresolved_ids=subgraph.unresolved_ids,
        pruned_ids=prune_result.pruned_ids,
        trimmed_ids=prune_result.trimmed_ids,
        phase_validation=phase_validation,
        total_effort_days=total_effort_days,
        total_items=total_items,
        metadata=metadata,
    )


def _extract_gap_state(gap_analysis: Any) -> _GapState:
    if isinstance(gap_analysis, Mapping):
        return _extract_from_mapping(gap_analysis)
    return _extract_from_object(gap_analysis)


def _extract_from_mapping(data: Mapping[str, Any]) -> _GapState:
    candidate_id = _str_or_none(data.get("candidate_id"))
    job_id = _str_or_none(data.get("job_id"))
    pathway_type = _str_or_none(data.get("pathway_type")) or "targeted"

    missing = _coerce_list(data.get("missing"))
    weak = _coerce_list(data.get("weak"))
    strong = _coerce_list(data.get("strong"))

    gap_skill_ids: list[str] = []
    met_skill_ids: list[str] = []
    warnings: list[str] = []
    level_map: dict[str, CandidateSkillLevel] = {}
    per_skill_gap: dict[str, float] = {}

    for bucket_name, records in (("missing", missing), ("weak", weak), ("strong", strong)):
        for raw in records:
            if not isinstance(raw, Mapping):
                continue

            skill_id = _normalize_skill_id(
                raw.get("canonical_id") or raw.get("name") or raw.get("label")
            )
            if not skill_id:
                warnings.append(f"Skipped record in '{bucket_name}' due to missing skill id")
                continue

            candidate = _to_float(
                raw.get("effective_candidate", raw.get("candidate_level", raw.get("candidate_score", 0.0))),
                0.0,
            )
            required = _to_float(
                raw.get("effective_required", raw.get("required_level", raw.get("required_score", 0.0))),
                0.0,
            )

            level_map[skill_id] = CandidateSkillLevel(
                canonical_id=skill_id,
                candidate_level=_clamp01(candidate),
                required_level=_clamp01(required),
            )
            per_skill_gap[skill_id] = max(0.0, _clamp01(required) - _clamp01(candidate))

            if bucket_name in {"missing", "weak"} and skill_id not in gap_skill_ids:
                gap_skill_ids.append(skill_id)
            if bucket_name == "strong" and skill_id not in met_skill_ids:
                met_skill_ids.append(skill_id)

    return _GapState(
        candidate_id=candidate_id,
        job_id=job_id,
        pathway_type=pathway_type,
        gap_skill_ids=gap_skill_ids,
        met_skill_ids=met_skill_ids,
        candidate_levels=list(level_map.values()),
        per_skill_gap=per_skill_gap,
        warnings=warnings,
    )


def _extract_from_object(obj: Any) -> _GapState:
    candidate_id = _str_or_none(getattr(obj, "candidate_id", None))
    job_id = _str_or_none(getattr(obj, "job_id", None))
    pathway_type = _str_or_none(getattr(obj, "pathway_type", None)) or "targeted"

    records = _coerce_list(getattr(obj, "items", []))
    missing_records = _coerce_list(getattr(obj, "missing", []))
    weak_records = _coerce_list(getattr(obj, "weak", []))
    strong_records = _coerce_list(getattr(obj, "strong", []))

    missing_ids = {_normalize_skill_id(getattr(item, "canonical_id", "")) for item in missing_records}
    weak_ids = {_normalize_skill_id(getattr(item, "canonical_id", "")) for item in weak_records}
    strong_ids = {_normalize_skill_id(getattr(item, "canonical_id", "")) for item in strong_records}

    gap_skill_ids: list[str] = []
    met_skill_ids: list[str] = []
    level_map: dict[str, CandidateSkillLevel] = {}
    per_skill_gap: dict[str, float] = {}

    for item in records:
        skill_id = _normalize_skill_id(getattr(item, "canonical_id", "") or getattr(item, "label", ""))
        if not skill_id:
            continue

        candidate = _to_float(getattr(item, "effective_candidate", 0.0), 0.0)
        required = _to_float(getattr(item, "effective_required", 0.0), 0.0)

        level_map[skill_id] = CandidateSkillLevel(
            canonical_id=skill_id,
            candidate_level=_clamp01(candidate),
            required_level=_clamp01(required),
        )
        per_skill_gap[skill_id] = max(0.0, _clamp01(required) - _clamp01(candidate))

        if skill_id in missing_ids or skill_id in weak_ids:
            if skill_id not in gap_skill_ids:
                gap_skill_ids.append(skill_id)
        if skill_id in strong_ids and skill_id not in met_skill_ids:
            met_skill_ids.append(skill_id)

    return _GapState(
        candidate_id=candidate_id,
        job_id=job_id,
        pathway_type=pathway_type,
        gap_skill_ids=gap_skill_ids,
        met_skill_ids=met_skill_ids,
        candidate_levels=list(level_map.values()),
        per_skill_gap=per_skill_gap,
        warnings=[],
    )


def _build_adjacency(node_ids: Sequence[str], edges: Sequence[object]) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    node_set = set(node_ids)

    for edge in edges:
        from_id = getattr(edge, "from_id", None)
        to_id = getattr(edge, "to_id", None)
        if from_id in node_set and to_id in node_set:
            adjacency[from_id].append(to_id)

    for node_id in adjacency:
        adjacency[node_id] = sorted(set(adjacency[node_id]))

    return adjacency


def _build_scores(
    *,
    skill_ids: Sequence[str],
    state: _GapState,
    role: str | None,
    effort_override: Mapping[str, int] | None,
    within_ids: Sequence[str],
) -> dict[str, float]:
    scores: dict[str, float] = {}
    within_list = list(within_ids)
    level_lookup = {level.canonical_id: level for level in state.candidate_levels}

    for skill_id in skill_ids:
        level = level_lookup.get(skill_id)
        gap = state.per_skill_gap.get(skill_id, 0.0)
        if level is not None:
            gap = max(0.0, level.required_level - level.candidate_level)

        node = graph_engine.resolve_node(skill_id)
        base_effort = node.base_effort_days if node is not None else 1
        effort_days = effort_override.get(skill_id, base_effort) if effort_override else base_effort
        unlock_count = subgraph_extractor.get_unlock_count(skill_id, within_ids=within_list)

        scores[skill_id] = scoring_engine.score_skill(
            gap=gap,
            unlock_count=unlock_count,
            effort_days=effort_days,
            role=role,
        )

    return scores


def _build_phase_results(
    *,
    phases: Sequence[Phase],
    pruned_items: Sequence[PrunedItem],
    final_scores: Mapping[str, float],
    within_ids: Sequence[str],
) -> list[PathwayPhaseResult]:
    item_lookup = {item.skill_id: item for item in pruned_items}
    within_list = list(within_ids)
    phase_results: list[PathwayPhaseResult] = []

    for phase in phases:
        items: list[PathwayItemResult] = []
        for skill_id in phase.skill_ids:
            item = item_lookup.get(skill_id)
            if item is None:
                continue

            items.append(
                PathwayItemResult(
                    skill_id=item.skill_id,
                    label=item.skill_label,
                    domain=item.domain,
                    phase_number=phase.phase_number,
                    proficiency_status=str(item.proficiency_status.value),
                    current_proficiency=round(item.current_proficiency, 4),
                    required_proficiency=round(item.required_proficiency, 4),
                    gap_delta=round(item.delta, 4),
                    base_effort_days=item.base_effort_days,
                    adjusted_effort_days=item.adjusted_effort_days,
                    composite_score=round(final_scores.get(item.skill_id, 0.0), 4),
                    unlock_count=subgraph_extractor.get_unlock_count(item.skill_id, within_ids=within_list),
                    resources=[],
                    notes=[],
                )
            )

        phase_results.append(
            PathwayPhaseResult(
                phase_number=phase.phase_number,
                focus_domain=phase.focus_domain,
                total_effort_days=phase.total_effort_days,
                min_critical_level=phase.min_critical_level,
                max_critical_level=phase.max_critical_level,
                items=items,
            )
        )

    return phase_results


def _empty_result(
    state: _GapState,
    *,
    mode: LearningMode,
    graph_version: str,
    unresolved_ids: list[str] | None = None,
) -> PathwayResult:
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph_version": graph_engine.get_version() or graph_version,
        "learning_mode": mode.value,
        "input_gap_count": len(state.gap_skill_ids),
        "retained_count": 0,
        "warnings": state.warnings,
    }
    return PathwayResult(
        candidate_id=state.candidate_id,
        job_id=state.job_id,
        pathway_type=state.pathway_type,
        phases=[],
        unresolved_ids=sorted(set(unresolved_ids or [])),
        pruned_ids=[],
        trimmed_ids=[],
        phase_validation={"valid": True, "violations": []},
        total_effort_days=0,
        total_items=0,
        metadata=metadata,
    )


def _ensure_graph_loaded(*, graph_version: str) -> None:
    if graph_engine.is_loaded():
        return
    try:
        graph_engine.load_graph(version=graph_version)
    except Exception as error:
        raise PathwayBuilderError(
            f"Unable to load graph version '{graph_version}': {error}"
        ) from error


def _coerce_learning_mode(value: LearningMode | str) -> LearningMode:
    if isinstance(value, LearningMode):
        return value
    normalized = str(value).strip().lower()
    if normalized == LearningMode.FAST_TRACK.value:
        return LearningMode.FAST_TRACK
    return LearningMode.DEEP_LEARNING


def _normalize_skill_id(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().lower().split())


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


__all__ = [
    "PathwayBuilderError",
    "PathwayItemResult",
    "PathwayPhaseResult",
    "PathwayResult",
    "build_pathway",
]


