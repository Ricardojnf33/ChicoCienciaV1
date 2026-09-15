from pathlib import Path

from typer.main import get_command

from src.cli import app


WORKFLOW = (
    Path(__file__).parents[1] / ".github/workflows/phase5-pilots.yml"
).read_text()


def test_pilot_workflow_is_manual_single_use_and_branch_restricted():
    assert "workflow_dispatch:" in WORKFLOW
    assert "push:" not in WORKFLOW
    assert "github.ref == 'refs/heads/feat/mestrado-fase-5'" in WORKFLOW
    assert "github.run_number == 1" in WORKFLOW
    assert "github.run_attempt == 1" in WORKFLOW
    assert "inputs.authorization == 'I_AUTHORIZE_SIX_PILOT_RUNS'" in WORKFLOW
    assert "cancel-in-progress: false" in WORKFLOW


def test_pilot_matrix_is_closed_sequential_and_hard_limited():
    expected = (
        "pilot-01-b1-iris-s11",
        "pilot-02-a-wine-s11",
        "pilot-03-a0-iris-s23",
        "pilot-04-b1-wine-s23",
        "pilot-05-a-iris-s37",
        "pilot-06-a0-wine-s37",
    )
    assert all(WORKFLOW.count(run_id) >= 1 for run_id in expected)
    matrix_block = WORKFLOW.split("matrix:", 1)[1].split("env:", 1)[0]
    assert sum(matrix_block.count(run_id) for run_id in expected) == 6
    assert "max-parallel: 1" in WORKFLOW
    assert "fail-fast: true" in WORKFLOW
    assert "Execute one authorized pilot with hard timeout\n        timeout-minutes: 15" in WORKFLOW
    assert "LLM_CALL_LIMIT" not in WORKFLOW


def test_pilot_workflow_preflights_scans_secrets_and_always_aggregates():
    assert "Run zero-call preflight" in WORKFLOW
    assert "Reject secret persistence" in WORKFLOW
    assert "grep -R --fixed-strings --quiet -- \"$OPENAI_API_KEY\"" in WORKFLOW
    assert "needs: [preflight, pilots]" in WORKFLOW
    assert "always()" in WORKFLOW
    assert "pattern: pilot-*" in WORKFLOW
    assert "aggregate-pilots" in WORKFLOW
    assert "pilot-campaign-report.json" in WORKFLOW
    assert "pilot-checksums.json" in WORKFLOW


def test_aggregate_cli_exposes_mode_as_named_option():
    command = get_command(app).commands["aggregate-pilots"]
    parameter = next(item for item in command.params if item.name == "mode")

    assert "--mode" in parameter.opts
