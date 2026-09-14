from collections import Counter

import pytest

from src.core.campaign import build_campaign_plan, write_campaign_plan
from src.core.contracts import load_manifest
from src.processes.ats_process import ExecutionMode
from src.processes.pilot_process import PilotCampaignManifest, run_pilot_campaign


def _plan(tmp_path):
    plan = build_campaign_plan(
        campaign_id="pilot-rehearsal",
        objective_root="objectives",
    )
    path = write_campaign_plan(tmp_path / "campaign-plan.json", plan)
    return plan, path


def test_mock_rehearsal_executes_six_pilots_and_is_idempotent(tmp_path):
    plan, plan_path = _plan(tmp_path)
    output = tmp_path / "pilots"

    first, manifest_path = run_pilot_campaign(plan_path, output)
    before = manifest_path.read_text()
    attempt_snapshots = {
        record.run_id: load_manifest(record.manifest_path).attempts
        for record in first.runs
    }
    second, second_path = run_pilot_campaign(plan_path, output)

    assert first.status == second.status == "SUCCEEDED"
    assert manifest_path == second_path
    assert Counter(run.condition for run in first.runs) == Counter(
        {"B1": 2, "A": 2, "A0": 2}
    )
    assert first.api_calls_started == first.total_tokens == first.cost_usd == 0
    assert first.call_limit == 144
    assert first.token_limit == 240_000
    assert first.cost_limit_usd == pytest.approx(0.18)
    assert [run.run_id for run in first.runs] == [
        run.run_id for run in plan.runs if run.kind == "pilot"
    ]
    assert before != ""
    for record in second.runs:
        persisted = load_manifest(record.manifest_path)
        assert persisted.status == "SUCCEEDED"
        assert persisted.experiment_seed == record.seed
        assert persisted.variant == record.condition
        assert persisted.llm_call_limit == record.call_limit == 24
        assert persisted.llm_token_limit == record.token_limit == 40_000
        assert persisted.llm_cost_limit_usd == record.cost_limit_usd == 0.03
        assert persisted.attempts == attempt_snapshots[record.run_id]


def test_live_pilots_refuse_missing_separate_authorization_before_factory(tmp_path):
    _, plan_path = _plan(tmp_path)
    factory_called = False

    def forbidden_factory(spec, budget_path):
        nonlocal factory_called
        factory_called = True
        raise AssertionError("factory não deveria ser chamada")

    with pytest.raises(PermissionError, match="autorização literal separada"):
        run_pilot_campaign(
            plan_path,
            tmp_path / "pilots",
            mode=ExecutionMode.LIVE,
            authorization="NOT_AUTHORIZED",
            crew_factory=forbidden_factory,
        )

    assert factory_called is False


def test_resume_refuses_changed_campaign_plan(tmp_path):
    plan, plan_path = _plan(tmp_path)
    output = tmp_path / "pilots"
    run_pilot_campaign(plan_path, output)
    plan.randomization_seed += 1
    write_campaign_plan(plan_path, plan)

    with pytest.raises(ValueError, match="plano ou modo diverge"):
        run_pilot_campaign(plan_path, output)


def test_aggregate_refuses_consumption_above_global_cap(tmp_path):
    _, plan_path = _plan(tmp_path)
    aggregate, _ = run_pilot_campaign(plan_path, tmp_path / "pilots")
    payload = aggregate.model_dump()
    payload["mode"] = "live"
    payload["api_calls_started"] = aggregate.call_limit + 1

    with pytest.raises(ValueError, match="teto de chamadas"):
        PilotCampaignManifest.model_validate(payload)
