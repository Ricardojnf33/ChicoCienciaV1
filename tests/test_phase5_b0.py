import json

import pytest

from src.core.campaign import build_campaign_plan
from src.processes.baseline_process import run_b0


def _b0_spec(dataset: str, seed: int):
    plan = build_campaign_plan(campaign_id="b0-test")
    return next(
        run
        for run in plan.runs
        if run.kind == "main"
        and run.condition == "B0"
        and run.dataset == dataset
        and run.seed == seed
    )


@pytest.mark.parametrize(
    ("dataset", "expected_train", "expected_test", "primary_metric"),
    [
        ("iris", 120, 30, "accuracy"),
        ("wine", 142, 36, "f1_macro"),
        ("digits", 1437, 360, "accuracy"),
    ],
)
def test_b0_uses_reserved_test_once_and_records_zero_llm_cost(
    tmp_path, dataset, expected_train, expected_test, primary_metric
):
    spec = _b0_spec(dataset, 11)
    path = tmp_path / f"{dataset}.json"

    result = run_b0(spec, path)
    payload = json.loads(path.read_text())

    assert result.train_size == expected_train
    assert result.test_size == expected_test
    assert result.test_evaluations == 1
    assert result.primary_metric == primary_metric
    assert 0 <= result.metrics[primary_metric] <= 1
    assert result.llm_tokens == 0
    assert result.llm_cost_usd == 0
    assert payload["dataset_sha256"] == result.dataset_sha256
    assert result.train_indices_sha256 != result.test_indices_sha256


def test_b0_rejects_generative_run_spec(tmp_path):
    plan = build_campaign_plan(campaign_id="invalid-b0-test")
    generative = next(run for run in plan.runs if run.condition == "A")

    with pytest.raises(ValueError, match="somente especificações B0"):
        run_b0(generative, tmp_path / "invalid.json")
