from src.core.contracts import CanonicalResult, ExecutionEvidence, write_result
from src.core.contracts import ContractError
from src.core.scoring import (
    final_score,
    metric_score,
    novelty_score,
    robustness_score,
    vlm_consistency_score,
)
from src.core.tree import AgenticTree
from pathlib import Path

import pytest


def test_scoring_components(tmp_path):
    rp = tmp_path / "res.json"
    write_result(
        rp,
        CanonicalResult(
            node_id="score-node",
            attempt=1,
            status="SUCCEEDED",
            primary_metric="accuracy",
            metrics={"accuracy": 0.8},
            execution=ExecutionEvidence(
                mode="mock",
                synthetic=True,
                network_used=False,
                return_code=0,
            ),
        ),
    )
    assert metric_score(str(rp), "accuracy") == 0.8
    assert 0.0 <= novelty_score(0.2) <= 1.0
    assert 0.0 <= robustness_score(3, 0.7) <= 1.0
    assert vlm_consistency_score(True) == 1.0
    s = final_score(str(rp), "accuracy", literature_overlap=0.3, replications=2, agreement=0.6, vlm_ok=True)
    assert 0.0 <= s <= 1.0


def test_tree_persist_roundtrip(tmp_path):
    # monta uma árvore mínima a partir do objective.example.yaml
    yaml_path = Path("objective.example.yaml")
    tree = AgenticTree.new(objective_yaml=str(yaml_path))
    # cria filho e persiste
    root = next(iter(tree.nodes.values()))
    tree.expand(root, k=1)
    out = tmp_path / "run.json"
    tree.save_json(str(out))
    # carrega e valida estrutura
    tree2 = AgenticTree.load_json(str(out))
    assert tree2.primary_metric == tree.primary_metric
    assert len(tree2.nodes) >= 1


def test_invalid_result_does_not_promote_tree_node(tmp_path):
    tree = AgenticTree.new(objective_yaml="objective.example.yaml")
    root = next(iter(tree.nodes.values()))
    invalid = tmp_path / "legacy-free-form.json"
    invalid.write_text('{"accuracy": 0.99}')

    with pytest.raises(ContractError):
        tree.update_result(root.id, str(invalid))
    assert root.results_path is None
    assert root.score is None
    assert root.id in tree.frontier
