import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.core.contracts import (
    ArtifactRecord,
    AttemptRecord,
    CanonicalResult,
    ContractError,
    ExecutionEvidence,
    RunManifest,
    adapt_legacy_result,
    artifact_record,
    canonicalize_attempt,
    load_result,
    write_result,
)


def canonical_result(**overrides):
    data = {
        "node_id": "node-1",
        "attempt": 1,
        "status": "SUCCEEDED",
        "primary_metric": "accuracy",
        "metrics": {"accuracy": 0.8},
        "execution": ExecutionEvidence(
            mode="mock",
            synthetic=True,
            network_used=False,
            return_code=0,
        ),
    }
    data.update(overrides)
    return CanonicalResult(**data)


def test_canonical_result_roundtrip_and_identity(tmp_path):
    result_path = write_result(tmp_path / "results.json", canonical_result())
    loaded = load_result(result_path, node_id="node-1", attempt=1, mode="mock")
    assert loaded.metrics["accuracy"] == 0.8

    with pytest.raises(ContractError, match="Identidade inválida"):
        load_result(result_path, node_id="other")


@pytest.mark.parametrize(
    "overrides",
    [
        {"metrics": {"f1": 0.8}},
        {"metrics": {"accuracy": float("nan")}},
        {"metrics": {"accuracy": 1.2}},
        {
            "execution": ExecutionEvidence(
                mode="live",
                synthetic=False,
                network_used=True,
                return_code=1,
            )
        },
    ],
)
def test_invalid_success_contract_is_rejected(overrides):
    with pytest.raises(ValidationError):
        canonical_result(**overrides)


def test_declared_artifact_must_preserve_hash(tmp_path):
    artifact = tmp_path / "code.py"
    artifact.write_text("print('ok')\n")
    record = artifact_record(artifact)
    result_path = write_result(
        tmp_path / "results.json",
        canonical_result(artifacts=[record]),
    )

    artifact.write_text("print('changed')\n")
    with pytest.raises(ContractError, match="divergente"):
        load_result(result_path)


def test_legacy_nested_metric_requires_explicit_path(tmp_path):
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(
        json.dumps({"l2": {"10": {"mean_accuracy": 0.98}}})
    )

    with pytest.raises(ContractError, match="metric_path explícito"):
        adapt_legacy_result(
            legacy_path,
            node_id="iris",
            attempt=1,
            mode="replay",
            primary_metric="accuracy",
        )

    adapted = adapt_legacy_result(
        legacy_path,
        node_id="iris",
        attempt=1,
        mode="replay",
        primary_metric="accuracy",
        metric_path="l2.10.mean_accuracy",
    )
    assert adapted.metrics["accuracy"] == 0.98
    assert adapted.source == "legacy-adapter"


def test_legacy_list_reduction_is_explicit(tmp_path):
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(json.dumps({"hypothesis": {"accuracies": [0.8, 0.9]}}))
    adapted = adapt_legacy_result(
        legacy_path,
        node_id="iris",
        attempt=1,
        mode="replay",
        primary_metric="accuracy",
        metric_path="hypothesis.accuracies",
        reduction="max",
    )
    assert adapted.metrics["accuracy"] == 0.9


def test_manifest_rejects_duplicate_attempts(tmp_path):
    now = datetime.now(timezone.utc)
    attempt = AttemptRecord(
        node_id="node-1",
        attempt=1,
        mode="mock",
        status="SUCCEEDED",
        directory=str(tmp_path),
        result_path=str(tmp_path / "results.json"),
        result_sha256="0" * 64,
        finished_at=now,
    )
    with pytest.raises(ValidationError, match="duplicadas"):
        RunManifest(
            run_id="run-1",
            objective_path="objective.example.yaml",
            primary_metric="accuracy",
            attempts=[attempt, attempt.model_copy()],
        )


def test_artifact_record_rejects_missing_file(tmp_path):
    with pytest.raises(ContractError, match="ausente"):
        artifact_record(tmp_path / "missing")

    with pytest.raises(ValidationError):
        ArtifactRecord(name="x", path="x", sha256="invalid", size_bytes=1)


def test_code_existence_is_not_execution_success(tmp_path):
    attempt_dir = tmp_path / "attempt-1"
    attempt_dir.mkdir()
    (attempt_dir / "code.py").write_text("raise RuntimeError('boom')\n")
    (attempt_dir / "execution.json").write_text(
        ExecutionEvidence(
            mode="live",
            synthetic=False,
            network_used=False,
            return_code=1,
        ).model_dump_json()
    )
    (attempt_dir / "raw_results.json").write_text(json.dumps({"accuracy": 0.9}))

    with pytest.raises(ContractError, match="return_code"):
        canonicalize_attempt(
            attempt_dir,
            node_id="node-1",
            attempt=1,
            mode="live",
            primary_metric="accuracy",
        )


def test_missing_result_is_not_replaced_by_synthetic_data(tmp_path):
    attempt_dir = tmp_path / "attempt-1"
    attempt_dir.mkdir()
    (attempt_dir / "code.py").write_text("print('no result')\n")
    (attempt_dir / "execution.json").write_text(
        ExecutionEvidence(
            mode="live",
            synthetic=False,
            network_used=False,
            return_code=0,
        ).model_dump_json()
    )

    with pytest.raises(ContractError, match="ausente"):
        canonicalize_attempt(
            attempt_dir,
            node_id="node-1",
            attempt=1,
            mode="live",
            primary_metric="accuracy",
        )


def test_valid_live_attempt_becomes_canonical(tmp_path):
    attempt_dir = tmp_path / "attempt-1"
    attempt_dir.mkdir()
    (attempt_dir / "code.py").write_text("print('ok')\n")
    (attempt_dir / "execution.json").write_text(
        ExecutionEvidence(
            mode="live",
            synthetic=False,
            network_used=False,
            return_code=0,
        ).model_dump_json()
    )
    (attempt_dir / "raw_results.json").write_text(json.dumps({"accuracy": 0.87}))

    result_path = canonicalize_attempt(
        attempt_dir,
        node_id="node-1",
        attempt=1,
        mode="live",
        primary_metric="accuracy",
    )
    result = load_result(result_path, node_id="node-1", attempt=1, mode="live")
    assert result.metrics["accuracy"] == 0.87
    assert {artifact.name for artifact in result.artifacts} == {
        "execution-evidence",
        "generated-code",
        "raw-result",
    }


@pytest.mark.parametrize(
    ("path", "metric", "metric_path", "reduction", "expected"),
    [
        (
            "experiments/c7d345b0/experiments/c7d345b0/results.json",
            "accuracy",
            "l2.10.mean_accuracy",
            "scalar",
            0.9800000000000001,
        ),
        (
            "experiments/results.json",
            "f1",
            "average_f1_scores.logreg_l2",
            "scalar",
            0.9730857138960456,
        ),
        (
            "experiments/d5068c16/results.json",
            "accuracy",
            "hypothesis_2.accuracies",
            "max",
            0.9777777777777777,
        ),
    ],
)
def test_historical_metrics_are_preserved(
    path, metric, metric_path, reduction, expected
):
    adapted = adapt_legacy_result(
        path,
        node_id="historical",
        attempt=1,
        mode="replay",
        primary_metric=metric,
        metric_path=metric_path,
        reduction=reduction,
    )
    assert adapted.metrics[metric] == pytest.approx(expected)
