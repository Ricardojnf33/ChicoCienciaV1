import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

from src.core.llm_budget import (
    BudgetCallbackHandler,
    BudgetExceeded,
    LLMBudgetLedger,
)
from src.core.contracts import RunManifest, load_manifest
from src.processes.ats_process import _sync_llm_budget


def _ledger(tmp_path, **overrides):
    values = {
        "model": "gpt-4o-mini-2024-07-18",
        "token_limit": 1_000,
        "cost_limit_usd": 0.03,
        "max_output_tokens_per_call": 100,
        "input_per_million_usd": 0.15,
        "cached_input_per_million_usd": 0.075,
        "output_per_million_usd": 0.60,
        "journal_path": tmp_path / "llm-budget.json",
    }
    values.update(overrides)
    return LLMBudgetLedger(**values)


def test_budget_rejects_projected_call_before_transport(tmp_path):
    ledger = _ledger(
        tmp_path,
        token_limit=100,
        max_output_tokens_per_call=80,
    )

    with pytest.raises(BudgetExceeded, match="antes do transporte"):
        ledger.reserve("rejected", input_tokens=30)

    snapshot = ledger.snapshot()
    persisted = json.loads((tmp_path / "llm-budget.json").read_text())
    assert snapshot.started_calls == 0
    assert snapshot.rejected_calls == 1
    assert snapshot.total_tokens == 0
    assert snapshot.reserved_tokens == 0
    assert persisted["stop_reason"] == snapshot.stop_reason

    with pytest.raises(BudgetExceeded, match="Orçamento LLM bloqueado"):
        ledger.reserve("still-blocked", input_tokens=1)


def test_callback_accounts_each_completed_call_and_releases_reservation(tmp_path):
    ledger = _ledger(tmp_path)
    callback = BudgetCallbackHandler(ledger)
    run_id = uuid4()

    callback.on_chat_model_start(
        {},
        [[HumanMessage(content="Planeje um experimento pequeno.")]],
        run_id=run_id,
    )
    callback.on_llm_end(
        SimpleNamespace(
            llm_output={
                "token_usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 5,
                }
            }
        ),
        run_id=run_id,
    )

    snapshot = ledger.snapshot()
    assert snapshot.started_calls == 1
    assert snapshot.completed_calls == 1
    assert snapshot.total_tokens == 17
    assert snapshot.reserved_tokens == 0
    assert snapshot.calls[0].call_id == str(run_id)
    assert snapshot.calls[0].status == "completed"


def test_failed_call_releases_reservation_without_claiming_usage(tmp_path):
    ledger = _ledger(tmp_path)
    callback = BudgetCallbackHandler(ledger)
    run_id = uuid4()
    callback.on_chat_model_start({}, [[HumanMessage(content="x")]], run_id=run_id)

    callback.on_llm_error(TimeoutError("provider timeout"), run_id=run_id)

    snapshot = ledger.snapshot()
    assert snapshot.failed_calls == 1
    assert snapshot.completed_calls == 0
    assert snapshot.total_tokens == 0
    assert snapshot.reserved_tokens == 0
    assert snapshot.calls[0].error == "TimeoutError"


def test_missing_provider_usage_charges_full_reservation_and_stops(tmp_path):
    ledger = _ledger(tmp_path)
    callback = BudgetCallbackHandler(ledger)
    run_id = uuid4()
    callback.on_chat_model_start({}, [[HumanMessage(content="x")]], run_id=run_id)
    reserved = ledger.snapshot().reserved_tokens

    with pytest.raises(RuntimeError, match="sem contabilidade de tokens"):
        callback.on_llm_end(SimpleNamespace(llm_output={}), run_id=run_id)

    snapshot = ledger.snapshot()
    assert snapshot.total_tokens == reserved
    assert snapshot.reserved_tokens == 0
    assert snapshot.calls[0].status == "unaccounted"
    assert snapshot.stop_reason


def test_budget_journal_resumes_only_fully_accounted_calls(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.reserve("first", input_tokens=10)
    ledger.complete("first", input_tokens=10, output_tokens=5)

    restored = _ledger(tmp_path)

    assert restored.snapshot().model_dump(exclude={"updated_at"}) == ledger.snapshot().model_dump(
        exclude={"updated_at"}
    )


def test_run_manifest_receives_durable_budget_totals(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.reserve("manifest-call", input_tokens=10)
    ledger.complete("manifest-call", input_tokens=10, output_tokens=5)
    crew = SimpleNamespace(_chico_llm_budget=ledger)
    manifest = RunManifest(
        run_id="budget-manifest",
        objective_path="objectives/iris.yaml",
        primary_metric="accuracy",
    )
    manifest_path = tmp_path / "manifest.json"

    _sync_llm_budget(manifest, str(manifest_path), crew)

    persisted = load_manifest(manifest_path)
    assert persisted.llm_model == "gpt-4o-mini-2024-07-18"
    assert persisted.llm_total_tokens == 15
    assert persisted.llm_cost_usd > 0
    assert persisted.llm_completed_calls == 1
    assert persisted.llm_budget_path == str(tmp_path / "llm-budget.json")
