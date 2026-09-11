from pathlib import Path

import pytest
from pydantic import ValidationError

from src.core.contracts import ComparisonManifest, RunManifest, load_manifest
from src.core.evaluation import (
    CriterionState,
    EvaluationDecision,
    EvaluationRecord,
    load_evaluation,
    write_evaluation,
)
from src.core.tree import AgenticTree
from src.core.variants import ExperimentVariant, policy_for
from src.processes import ats_process
from src.processes.ats_process import ExecutionMode, run_agentic_tree
from src.processes.comparison_process import run_variant_comparison


def _run_fixture(tmp_path: Path, variant: ExperimentVariant, *, max_depth: int = 4):
    tree = AgenticTree.new(
        objective_yaml="objective.example.yaml",
        artifact_root=str(tmp_path / "artifacts"),
        max_depth=max_depth,
        max_branching=3,
    )
    policy = policy_for(variant)
    manifest = RunManifest(
        run_id=f"variant-{variant.value.lower()}",
        objective_path="objective.example.yaml",
        primary_metric=tree.primary_metric,
        variant=variant.value,
        budget=8,
        branching=2,
        effective_branching=policy.effective_branching(2),
        max_depth=max_depth,
        automatic_correction=policy.automatic_correction,
    )
    return tree, manifest


def _execute(tmp_path: Path, variant: ExperimentVariant, *, budget: int, max_depth: int = 4):
    tree, manifest = _run_fixture(tmp_path, variant, max_depth=max_depth)
    run_agentic_tree(
        None,
        tree,
        budget=budget,
        branching=2,
        checkpoint_path=str(tmp_path / "tree.json"),
        mode=ExecutionMode.MOCK,
        sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
        manifest=manifest,
        manifest_path=str(tmp_path / "manifest.json"),
        variant=variant,
    )
    return tree, manifest


def test_evaluation_contract_distinguishes_absence_from_approval():
    with pytest.raises(ValidationError, match="evaluated=false"):
        EvaluationRecord(
            node_id="n1",
            attempt=1,
            evaluator="reviewer",
            decision=EvaluationDecision.NOT_EVALUATED,
            evaluated=True,
            rationale="Reviewer was not actually invoked.",
        )

    with pytest.raises(ValidationError, match="todos os critérios"):
        EvaluationRecord(
            node_id="n1",
            attempt=1,
            evaluator="reviewer",
            decision=EvaluationDecision.APPROVED,
            evaluated=True,
            rationale="A criterion failed despite the nominal decision.",
            criteria={"reproducibility": CriterionState.FAIL},
        )


def test_evaluation_loader_checks_identity_and_declared_evidence(tmp_path):
    evidence = tmp_path / "results.json"
    evidence.write_text("{}")
    path = write_evaluation(
        tmp_path / "review.json",
        EvaluationRecord(
            node_id="n1",
            attempt=1,
            evaluator="reviewer",
            decision=EvaluationDecision.APPROVED,
            evaluated=True,
            rationale="All declared checks passed against the durable result.",
            criteria={"result_contract": CriterionState.PASS},
            evidence_paths=[str(evidence)],
        ),
    )

    assert load_evaluation(path, node_id="n1", attempt=1, evaluator="reviewer").evaluated
    evidence.unlink()
    with pytest.raises(ValueError, match="Evidência.*ausente"):
        load_evaluation(path, node_id="n1", attempt=1, evaluator="reviewer")


def test_mock_run_materializes_explicit_not_evaluated_records(tmp_path):
    tree, manifest = _execute(tmp_path, ExperimentVariant.A, budget=1)

    record = manifest.attempts[-1]
    assert record.reviewer_decision == "NOT_EVALUATED"
    assert record.vlm_decision == "NOT_EVALUATED"
    assert Path(record.reviewer_path).is_file()
    assert Path(record.vlm_path).is_file()
    node = tree.nodes[record.node_id]
    assert node.meta["reviewer_evaluated"] is False
    assert node.meta["vlm_evaluated"] is False
    assert node.score == 0.4075


def test_review_provider_cannot_claim_visual_evaluation_without_figure(tmp_path):
    tree, manifest = _run_fixture(tmp_path, ExperimentVariant.A)

    def invalid_provider(node, result_path, attempt):
        reviewer = EvaluationRecord(
            node_id=node.id,
            attempt=attempt,
            evaluator="reviewer",
            decision=EvaluationDecision.APPROVED,
            evaluated=True,
            rationale="The result contract and metric were reviewed.",
            criteria={"result_contract": CriterionState.PASS},
            evidence_paths=[str(result_path)],
        )
        vlm = EvaluationRecord(
            node_id=node.id,
            attempt=attempt,
            evaluator="vlm",
            decision=EvaluationDecision.APPROVED,
            evaluated=True,
            rationale="Visual output was nominally approved without evidence.",
            criteria={"visual_consistency": CriterionState.PASS},
        )
        return reviewer, vlm

    with pytest.raises(ValueError, match="sem figura"):
        run_agentic_tree(
            None,
            tree,
            budget=1,
            mode=ExecutionMode.MOCK,
            sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
            manifest=manifest,
            manifest_path=str(tmp_path / "manifest.json"),
            variant=ExperimentVariant.A,
            review_provider=invalid_provider,
        )


def test_variant_policies_isolate_planned_factors():
    b1 = policy_for(ExperimentVariant.B1)
    a = policy_for(ExperimentVariant.A)
    a0 = policy_for(ExperimentVariant.A0)

    assert (b1.automatic_correction, a.automatic_correction) == (True, True)
    assert (b1.effective_branching(3), a.effective_branching(3)) == (1, 3)
    assert (a.uses_tree_search, a0.uses_tree_search) == (True, True)
    assert (a.max_attempts_per_node, a0.max_attempts_per_node) == (3, 1)


def test_b1_executes_a_single_fixed_sequence(tmp_path):
    tree, manifest = _execute(
        tmp_path,
        ExperimentVariant.B1,
        budget=4,
        max_depth=3,
    )

    assert len(manifest.attempts) == 4
    assert sorted(node.depth for node in tree.nodes.values()) == [0, 1, 2, 3]
    parent_counts = {
        node.id: len([child for child in tree.nodes.values() if child.parent_id == node.id])
        for node in tree.nodes.values()
    }
    assert max(parent_counts.values()) == 1


@pytest.mark.parametrize("variant", [ExperimentVariant.B1, ExperimentVariant.A])
def test_correction_variants_recover_once(tmp_path, monkeypatch, variant):
    tree, manifest = _run_fixture(tmp_path, variant)
    original = ats_process._mock_result
    calls = {"count": 0}

    def fail_once(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("injected recoverable failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(ats_process, "_mock_result", fail_once)
    run_agentic_tree(
        None,
        tree,
        budget=1,
        branching=2,
        mode=ExecutionMode.MOCK,
        sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
        manifest=manifest,
        manifest_path=str(tmp_path / "manifest.json"),
        variant=variant,
    )

    assert [record.status for record in manifest.attempts] == ["FAILED", "SUCCEEDED"]
    assert [record.attempt for record in manifest.attempts] == [1, 2]


def test_a0_does_not_apply_automatic_correction(tmp_path, monkeypatch):
    tree, manifest = _run_fixture(tmp_path, ExperimentVariant.A0)
    monkeypatch.setattr(
        ats_process,
        "_mock_result",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("injected failure")),
    )

    with pytest.raises(RuntimeError, match="injected failure"):
        run_agentic_tree(
            None,
            tree,
            budget=1,
            branching=2,
            mode=ExecutionMode.MOCK,
            sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
            manifest=manifest,
            manifest_path=str(tmp_path / "manifest.json"),
            variant=ExperimentVariant.A0,
        )

    assert len(manifest.attempts) == 1
    assert manifest.attempts[0].status == "FAILED"


def test_search_stops_cleanly_after_reaching_depth_limit(tmp_path):
    tree, manifest = _execute(
        tmp_path,
        ExperimentVariant.A,
        budget=10,
        max_depth=1,
    )

    assert len(manifest.attempts) == 3
    assert len({record.node_id for record in manifest.attempts}) == 3
    assert tree.frontier == []
    assert all(node.meta.get("terminal_reason") == "max_depth" for node in tree.nodes.values() if node.depth == 1)


def test_comparison_runner_executes_the_three_conditions_without_manual_changes(tmp_path):
    comparison, path = run_variant_comparison(
        "objective.example.yaml",
        str(tmp_path),
        budget=1,
        branching=2,
        max_depth=3,
        max_branching=3,
        mode=ExecutionMode.MOCK,
        campaign_id="protocol-smoke",
    )

    persisted = ComparisonManifest.model_validate_json(path.read_text())
    assert comparison.status == persisted.status == "SUCCEEDED"
    assert [run.variant for run in persisted.runs] == ["B1", "A", "A0"]
    manifests = [load_manifest(run.manifest_path) for run in persisted.runs]
    assert {manifest.budget for manifest in manifests} == {1}
    assert {manifest.branching for manifest in manifests} == {2}
    assert [manifest.effective_branching for manifest in manifests] == [1, 2, 2]
    assert [manifest.automatic_correction for manifest in manifests] == [True, True, False]
