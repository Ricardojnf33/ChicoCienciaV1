import hashlib
from pathlib import Path

from typer.main import get_command

from src.cli import app


WORKFLOW = (
    Path(__file__).parents[1] / ".github/workflows/phase5-pilots.yml"
).read_text()
CAMPAIGN_PLAN = (
    Path(__file__).parents[1]
    / "docs/mestrado/evidencias/phase5-campaign-plan.json"
)
CAMPAIGN_PLAN_SHA256 = (
    "eaac40d89cb3206ec27138bd43580a1b5ab6c9c824ff4bc70595d2a4d8badea4"
)


def test_pilot_workflow_is_manual_single_use_and_branch_restricted():
    assert "workflow_dispatch:" in WORKFLOW
    assert "push:" not in WORKFLOW
    assert "github.ref == 'refs/heads/feat/mestrado-fase-5'" in WORKFLOW
    assert "github.run_number == 4" in WORKFLOW
    assert "github.run_number == 2" not in WORKFLOW
    assert "github.run_number == 1" not in WORKFLOW
    assert "github.run_attempt == 1" in WORKFLOW
    assert (
        "inputs.authorization == 'I_AUTHORIZE_PHASE5_RECOVERY_RUN4'"
        in WORKFLOW
    )
    assert "cancel-in-progress: false" in WORKFLOW


def test_pilot_workflow_pins_exact_campaign_plan_bytes():
    actual_sha256 = hashlib.sha256(CAMPAIGN_PLAN.read_bytes()).hexdigest()

    assert actual_sha256 == CAMPAIGN_PLAN_SHA256
    assert f"CAMPAIGN_PLAN_SHA256: {CAMPAIGN_PLAN_SHA256}" in WORKFLOW


def test_recovery_restores_run2_checkpoint_and_keeps_prior_consumption():
    assert "actions: read" in WORKFLOW
    assert "run-id: 35043495688" in WORKFLOW
    assert "name: pilot-01-b1-iris-s11" in WORKFLOW
    assert "Resume pilot 01 with prior consumption preserved" in WORKFLOW
    assert "needs: [preflight, recover_pilot_01, pilots_remaining]" in WORKFLOW


def test_six_pilot_matrix_is_closed_sequential_and_hard_limited():
    expected = (
        "pilot-01-b1-iris-s11",
        "pilot-02-a-wine-s11",
        "pilot-03-a0-iris-s23",
        "pilot-04-b1-wine-s23",
        "pilot-05-a-iris-s37",
        "pilot-06-a0-wine-s37",
    )
    matrix_block = WORKFLOW.split("matrix:", 1)[1].split("env:", 1)[0]

    assert all(matrix_block.count(run_id) == 1 for run_id in expected)
    assert matrix_block.count("recover_ledger: true") == 2
    assert matrix_block.count("recover_ledger: false") == 4
    assert "max-parallel: 1" in WORKFLOW
    assert "fail-fast: true" in WORKFLOW
    assert "Execute one authorized pilot with hard timeout\n        timeout-minutes: 15" in WORKFLOW
    assert "LLM_CALL_LIMIT" not in WORKFLOW


def test_pilot_workflow_preflights_scans_secrets_and_always_aggregates():
    assert "Run zero-call preflight" in WORKFLOW
    assert WORKFLOW.count("Reject secret persistence") == 1
    assert "grep -R --fixed-strings --quiet -- \"$OPENAI_API_KEY\"" in WORKFLOW
    assert "always()" in WORKFLOW
    assert "pattern: pilot-*" in WORKFLOW
    assert "aggregate-pilots" in WORKFLOW
    assert "pilot-campaign-report.json" in WORKFLOW
    assert "pilot-checksums.json" in WORKFLOW


def test_aggregate_cli_exposes_mode_as_named_option():
    command = get_command(app).commands["aggregate-pilots"]
    parameter = next(item for item in command.params if item.name == "mode")

    assert "--mode" in parameter.opts
