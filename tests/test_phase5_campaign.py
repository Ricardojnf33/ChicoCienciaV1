import json
from collections import Counter

from src.core.campaign import build_campaign_plan, write_campaign_plan


def test_campaign_materializes_pilots_and_full_main_matrix(tmp_path):
    plan = build_campaign_plan(campaign_id="phase5-draft-v1")
    path = write_campaign_plan(tmp_path / "campaign-plan.json", plan)
    payload = json.loads(path.read_text())

    main = [run for run in plan.runs if run.kind == "main"]
    pilots = [run for run in plan.runs if run.kind == "pilot"]
    assert len(plan.runs) == 66
    assert len(main) == 60
    assert len(pilots) == 6
    assert Counter(run.condition for run in main) == Counter(
        {"B0": 15, "B1": 15, "A": 15, "A0": 15}
    )
    assert sum(run.uses_llm for run in plan.runs) == 51
    assert all(run.objective_sha256 for run in plan.runs)
    assert payload["api_calls_performed"] == 0
    assert payload["protocol_frozen"] is False


def test_campaign_is_deterministically_randomized_and_b0_has_zero_llm_cost():
    first = build_campaign_plan(campaign_id="first", randomization_seed=177)
    second = build_campaign_plan(campaign_id="second", randomization_seed=177)

    first_order = [
        (run.condition, run.dataset, run.seed)
        for run in first.runs
        if run.kind == "main"
    ]
    second_order = [
        (run.condition, run.dataset, run.seed)
        for run in second.runs
        if run.kind == "main"
    ]
    assert first_order == second_order
    assert all(
        not run.uses_llm and run.token_limit == 0 and run.cost_limit_usd == 0
        for run in first.runs
        if run.condition == "B0"
    )
    assert first.limits.campaign_token_limit == 2_040_000
    assert first.limits.campaign_cost_limit_usd == 1.53
