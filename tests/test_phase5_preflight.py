import json

from src.config.settings import Settings
from src.core.preflight import CheckStatus, run_preflight, write_preflight


def test_preflight_passes_without_api_call_or_secret_leak(tmp_path):
    secret = "sk-test-preflight-must-remain-hidden"
    report = run_preflight(
        settings=Settings(OPENAI_API_KEY=secret, _env_file=None),
        objective_path="objective.example.yaml",
        require_sandbox=False,
    )
    path = write_preflight(tmp_path / "preflight.json", report)
    serialized = path.read_text()

    assert report.status is CheckStatus.PASS
    assert report.api_calls_performed == 0
    assert secret not in serialized
    assert json.loads(serialized)["checks"][0]["name"] == "credential"


def test_preflight_records_missing_secret_as_failure():
    report = run_preflight(
        settings=Settings(_env_file=None),
        objective_path="objective.example.yaml",
        require_sandbox=False,
    )

    assert report.status is CheckStatus.FAIL
    credential = next(item for item in report.checks if item.name == "credential")
    assert credential.status is CheckStatus.FAIL
    assert "OPENAI_API_KEY" in credential.detail


def test_preflight_rejects_model_without_frozen_tokenizer_mapping():
    report = run_preflight(
        settings=Settings(
            OPENAI_API_KEY="sk-test-model-gate",
            MODEL_TEXT="gpt-4.1-mini",
            _env_file=None,
        ),
        objective_path="objective.example.yaml",
        require_sandbox=False,
    )

    model_check = next(item for item in report.checks if item.name == "models")
    assert report.status is CheckStatus.FAIL
    assert model_check.status is CheckStatus.FAIL
    assert "tokeniser" in model_check.detail


def test_preflight_redacts_secret_from_downstream_failure():
    secret = "sk-test-redaction-sentinel"

    class FailingRunner:
        def __init__(self, **kwargs):
            pass

        def preflight(self, workdir):
            raise RuntimeError(f"provider accidentally returned {secret}")

    report = run_preflight(
        settings=Settings(OPENAI_API_KEY=secret, _env_file=None),
        objective_path="objective.example.yaml",
        require_sandbox=True,
        runner_factory=FailingRunner,
    )

    serialized = report.model_dump_json()
    assert report.status is CheckStatus.FAIL
    assert secret not in serialized
    assert "**********" in serialized


def test_preflight_rejects_budget_that_cannot_fit_one_output_reservation():
    report = run_preflight(
        settings=Settings(
            OPENAI_API_KEY="sk-test-budget-gate",
            LLM_COST_LIMIT_USD=0.000001,
            _env_file=None,
        ),
        objective_path="objective.example.yaml",
        require_sandbox=False,
    )

    budget = next(item for item in report.checks if item.name == "budget")
    assert report.status is CheckStatus.FAIL
    assert budget.status is CheckStatus.FAIL
    assert "teto monetário" in budget.detail
