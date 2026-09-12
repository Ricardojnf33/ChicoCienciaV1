import hashlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.config.settings import Settings
from src.core.atomic_io import atomic_write_text
from src.core.contracts import utc_now
from src.core.llm_budget import LLMBudgetLedger
from src.crews.ai_scientist_v2 import build_budget_ledger, build_budgeted_llm

SMOKE_AUTHORIZATION = "I_AUTHORIZE_ONE_OPENAI_CALL"
SMOKE_EXPECTED_RESPONSE = "CHICO_SMOKE_OK"
SMOKE_PROMPT = "Return exactly CHICO_SMOKE_OK and nothing else."
ModelFactory = Callable[[Settings, LLMBudgetLedger], Any]


class LiveSmokeReport(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    created_at: str
    status: Literal["PASS", "FAIL"]
    model: str = Field(min_length=1)
    authorization_validated: bool
    max_retries: int = 0
    api_calls_started: int = Field(ge=0)
    api_calls_completed: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    response_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    response_matches_expected: bool = False
    error_type: str | None = None


def _default_model_factory(settings: Settings, ledger: LLMBudgetLedger):
    return build_budgeted_llm(settings, model=settings.MODEL_TEXT, ledger=ledger)


def run_openai_smoke(
    *,
    settings: Settings,
    authorization: str,
    output_path: str | Path,
    budget_path: str | Path,
    model_factory: ModelFactory = _default_model_factory,
) -> LiveSmokeReport:
    """Perform exactly one budgeted model invocation after explicit authorization."""
    if authorization != SMOKE_AUTHORIZATION:
        raise PermissionError("Autorização explícita inválida; nenhuma chamada iniciada.")
    started = time.monotonic()
    ledger = build_budget_ledger(settings, budget_path=budget_path)
    model = model_factory(settings, ledger)
    response_content = ""
    error: BaseException | None = None
    try:
        response = model.invoke(SMOKE_PROMPT)
        response_content = str(getattr(response, "content", ""))
    except BaseException as exc:
        error = exc
    snapshot = ledger.snapshot()
    matches = response_content.strip() == SMOKE_EXPECTED_RESPONSE
    exact_call = snapshot.started_calls == 1 and snapshot.completed_calls == 1
    passed = error is None and exact_call and matches
    report = LiveSmokeReport(
        created_at=utc_now().isoformat(),
        status="PASS" if passed else "FAIL",
        model=settings.MODEL_TEXT,
        authorization_validated=True,
        api_calls_started=snapshot.started_calls,
        api_calls_completed=snapshot.completed_calls,
        input_tokens=snapshot.input_tokens,
        output_tokens=snapshot.output_tokens,
        total_tokens=snapshot.total_tokens,
        cost_usd=snapshot.cost_usd,
        duration_seconds=time.monotonic() - started,
        response_sha256=(
            hashlib.sha256(response_content.encode()).hexdigest() if response_content else None
        ),
        response_matches_expected=matches,
        error_type=type(error).__name__ if error else None,
    )
    atomic_write_text(output_path, report.model_dump_json(indent=2))
    if not passed:
        raise RuntimeError(
            "Smoke OpenAI falhou; consulte os artefatos sem repetir a chamada."
        ) from error
    return report
