import pytest
from pydantic import ValidationError

from src.core.enums import NodeType, Stage
from src.core.research import ExpansionCandidate, ExperimentPlan, HypothesisSpec
from src.core.tree import AgenticTree


def test_research_contracts_bind_plan_to_hypothesis():
    hypothesis = HypothesisSpec.from_statement(
        "Regularização melhora a generalização fora da amostra", "accuracy"
    )
    plan = ExperimentPlan.build(
        hypothesis_id=hypothesis.hypothesis_id,
        decision_key="regularization.reference",
        description="Comparar regularização com a configuração de referência",
        parameters={"c": 1.0, "seeds": [11, 23]},
    )

    candidate = ExpansionCandidate(hypothesis=hypothesis, plan=plan)

    assert candidate.plan.hypothesis_id == candidate.hypothesis.hypothesis_id
    with pytest.raises(ValidationError, match="divergentes"):
        ExpansionCandidate(
            hypothesis=hypothesis,
            plan=plan.model_copy(update={"hypothesis_id": "h-00000000"}),
        )


def test_plan_rejects_non_json_parameters():
    hypothesis = HypothesisSpec.from_statement(
        "Uma decisão declarada produz resultado mensurável", "accuracy"
    )
    with pytest.raises(ValidationError, match="serializáveis"):
        ExperimentPlan.build(
            hypothesis_id=hypothesis.hypothesis_id,
            decision_key="invalid.parameter",
            description="Plano com parâmetro não reproduzível",
            parameters={"callback": object()},
        )


def test_root_expansion_produces_distinct_bounded_decisions():
    tree = AgenticTree.new(
        "objective.example.yaml", max_depth=2, max_branching=2
    )
    root = tree.nodes[tree.frontier[0]]

    child_ids = tree.expand(root, k=99)
    children = [tree.nodes[child_id] for child_id in child_ids]

    assert len(children) == 2
    assert len({child.hypothesis.hypothesis_id for child in children}) == 2
    assert len({child.experiment_plan.decision_key for child in children}) == 2
    assert all(child.depth == 1 for child in children)
    assert all(child.stage is Stage.TUNING for child in children)
    assert all(child.type is NodeType.HYPERPARAM for child in children)
    assert root.id not in tree.frontier


def test_duplicate_expansion_candidates_are_rejected():
    tree = AgenticTree.new("objective.example.yaml")
    root = tree.nodes[tree.frontier[0]]
    candidate = tree._objective_candidates()[0]

    with pytest.raises(ValueError, match="duplicadas"):
        tree.expand(root, candidates=[candidate, candidate])


def test_depth_limit_marks_terminal_node_without_new_frontier_entries():
    tree = AgenticTree.new(
        "objective.example.yaml", max_depth=1, max_branching=2
    )
    root = tree.nodes[tree.frontier[0]]
    child = tree.nodes[tree.expand(root, k=1)[0]]

    assert tree.expand(child, k=2) == []
    assert child.meta["terminal_reason"] == "max_depth"
    assert child.depth == 1


def test_tree_roundtrip_preserves_structured_decision_and_limits(tmp_path):
    tree = AgenticTree.new(
        "objective.example.yaml",
        artifact_root=str(tmp_path / "artifacts"),
        max_depth=2,
        max_branching=1,
    )
    root = tree.nodes[tree.frontier[0]]
    original = tree.nodes[tree.expand(root, k=2)[0]]
    checkpoint = tmp_path / "tree.json"

    tree.save_json(checkpoint)
    restored = AgenticTree.load_json(checkpoint)
    recovered = restored.nodes[original.id]

    assert restored.max_depth == 2
    assert restored.max_branching == 1
    assert recovered.hypothesis == original.hypothesis
    assert recovered.experiment_plan == original.experiment_plan
    assert recovered.depth == 1


def test_select_does_not_resurrect_completed_nodes():
    tree = AgenticTree.new("objective.example.yaml")
    root = tree.nodes[tree.frontier[0]]
    tree.frontier.clear()

    with pytest.raises(RuntimeError, match="fronteira"):
        tree.select()

    assert root.id in tree.nodes
