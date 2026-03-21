from modules.scoring.pathway_scoring import score_pathway_items, stable_rank


def test_score_pathway_items_bounded_and_deterministic() -> None:
    ordered = ["python", "sql", "ml"]
    prereq_counts = {"python": 0, "sql": 1, "ml": 2}

    first = score_pathway_items(ordered, prereq_counts)
    second = score_pathway_items(ordered, prereq_counts)

    assert first == second
    for value in first.values():
        assert 0.0 <= value <= 1.0


def test_score_pathway_items_prioritizes_dependency_signal() -> None:
    ordered = ["a", "b"]
    prereq_counts = {"a": 5, "b": 0}

    scored = score_pathway_items(ordered, prereq_counts)
    assert scored["a"] > scored["b"]


def test_stable_rank_uses_score_prereq_then_name() -> None:
    items = [
        {"skill": "zeta", "score": 0.5, "prereq_count": 1},
        {"skill": "alpha", "score": 0.5, "prereq_count": 1},
        {"skill": "beta", "score": 0.7, "prereq_count": 0},
    ]

    ranked = stable_rank(items)
    assert [item["skill"] for item in ranked] == ["beta", "alpha", "zeta"]
