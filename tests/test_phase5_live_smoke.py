from types import SimpleNamespace

import pytest

from src.config.settings import Settings
from src.core.live_smoke import SMOKE_AUTHORIZATION, run_openai_smoke


def _settings():
    return Settings(
        OPENAI_API_KEY="sk-test-smoke-never-send",
        LLM_TOKEN_LIMIT=512,
        LLM_COST_LIMIT_USD=0.001,
        LLM_MAX_OUTPUT_TOKENS=16,
        _env_file=None,
    )


def test_smoke_refuses_missing_authorization_before_model_construction(tmp_path):
    constructed = False

    def forbidden_factory(settings, ledger):
        nonlocal constructed
        constructed = True
        raise AssertionError("factory não deveria ser chamada")

    with pytest.raises(PermissionError, match="nenhuma chamada"):
        run_openai_smoke(
            settings=_settings(),
            authorization="NOT_AUTHORIZED",
            output_path=tmp_path / "smoke.json",
            budget_path=tmp_path / "budget.json",
            model_factory=forbidden_factory,
        )

    assert constructed is False
    assert not (tmp_path / "smoke.json").exists()


def test_smoke_accepts_exactly_one_accounted_call(tmp_path):
    class OneCallModel:
        def __init__(self, ledger):
            self.ledger = ledger

        def invoke(self, prompt):
            assert "CHICO_SMOKE_OK" in prompt
            self.ledger.reserve("only-call", input_tokens=10)
            self.ledger.complete("only-call", input_tokens=10, output_tokens=4)
            return SimpleNamespace(content="CHICO_SMOKE_OK")

    report = run_openai_smoke(
        settings=_settings(),
        authorization=SMOKE_AUTHORIZATION,
        output_path=tmp_path / "smoke.json",
        budget_path=tmp_path / "budget.json",
        model_factory=lambda settings, ledger: OneCallModel(ledger),
    )

    assert report.status == "PASS"
    assert report.api_calls_started == 1
    assert report.api_calls_completed == 1
    assert report.total_tokens == 14
    assert report.response_matches_expected is True
    assert "CHICO_SMOKE_OK" not in (tmp_path / "smoke.json").read_text()


def test_smoke_fails_if_factory_attempts_more_than_one_call(tmp_path):
    class TwoCallModel:
        def __init__(self, ledger):
            self.ledger = ledger

        def invoke(self, prompt):
            for call_id in ("first", "second"):
                self.ledger.reserve(call_id, input_tokens=5)
                self.ledger.complete(call_id, input_tokens=5, output_tokens=2)
            return SimpleNamespace(content="CHICO_SMOKE_OK")

    output = tmp_path / "smoke.json"
    with pytest.raises(RuntimeError, match="sem repetir"):
        run_openai_smoke(
            settings=_settings(),
            authorization=SMOKE_AUTHORIZATION,
            output_path=output,
            budget_path=tmp_path / "budget.json",
            model_factory=lambda settings, ledger: TwoCallModel(ledger),
        )

    assert '"api_calls_started": 2' in output.read_text()
