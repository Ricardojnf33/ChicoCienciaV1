import json
import threading
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import tiktoken
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel, Field, model_validator

from src.core.atomic_io import atomic_write_text
from src.core.contracts import utc_now


class BudgetExceeded(RuntimeError):
    """Raised before transport when the next LLM call cannot fit the run budget."""


class LLMCallUsage(BaseModel):
    call_id: str = Field(min_length=1)
    status: Literal["completed", "failed", "unaccounted"]
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    error: str | None = None


class LLMBudgetSnapshot(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    updated_at: str
    model: str = Field(min_length=1)
    token_limit: int = Field(ge=1)
    cost_limit_usd: float = Field(gt=0)
    max_output_tokens_per_call: int = Field(ge=1)
    input_per_million_usd: float = Field(ge=0)
    cached_input_per_million_usd: float = Field(ge=0)
    output_per_million_usd: float = Field(ge=0)
    started_calls: int = Field(ge=0)
    completed_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)
    rejected_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    reserved_tokens: int = Field(ge=0)
    reserved_cost_usd: float = Field(ge=0)
    stop_reason: str | None = None
    calls: list[LLMCallUsage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_totals(self):
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("total_tokens deve ser input_tokens + output_tokens.")
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("Tokens em cache não podem superar tokens de entrada.")
        return self


class _Reservation(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=1)
    total_tokens: int = Field(ge=1)
    cost_usd: float = Field(ge=0)


class LLMBudgetLedger:
    def __init__(
        self,
        *,
        model: str,
        token_limit: int,
        cost_limit_usd: float,
        max_output_tokens_per_call: int,
        input_per_million_usd: float,
        cached_input_per_million_usd: float,
        output_per_million_usd: float,
        journal_path: str | Path | None = None,
    ):
        if token_limit < 1 or cost_limit_usd <= 0 or max_output_tokens_per_call < 1:
            raise ValueError("Limites de LLM devem ser positivos.")
        self.model = model
        self.token_limit = token_limit
        self.cost_limit_usd = cost_limit_usd
        self.max_output_tokens_per_call = max_output_tokens_per_call
        self.input_per_million_usd = input_per_million_usd
        self.cached_input_per_million_usd = cached_input_per_million_usd
        self.output_per_million_usd = output_per_million_usd
        self.journal_path = Path(journal_path) if journal_path else None
        self._lock = threading.RLock()
        self._reservations: dict[str, _Reservation] = {}
        self._calls: list[LLMCallUsage] = []
        self.started_calls = 0
        self.completed_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0
        self.input_tokens = 0
        self.cached_input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0
        self.stop_reason: str | None = None
        if self.journal_path and self.journal_path.is_file():
            self._restore(self.journal_path)

    def _cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> float:
        uncached_tokens = input_tokens - cached_tokens
        return (
            uncached_tokens * self.input_per_million_usd
            + cached_tokens * self.cached_input_per_million_usd
            + output_tokens * self.output_per_million_usd
        ) / 1_000_000

    def _reserved(self) -> tuple[int, float]:
        return (
            sum(item.total_tokens for item in self._reservations.values()),
            sum(item.cost_usd for item in self._reservations.values()),
        )

    def reserve(self, call_id: str, input_tokens: int) -> None:
        with self._lock:
            if self.stop_reason:
                self.rejected_calls += 1
                self._persist()
                raise BudgetExceeded(f"Orçamento LLM bloqueado: {self.stop_reason}")
            if call_id in self._reservations:
                raise ValueError(f"Reserva duplicada para a chamada {call_id}.")
            output_tokens = self.max_output_tokens_per_call
            projected_tokens = input_tokens + output_tokens
            projected_cost = self._cost(input_tokens, output_tokens)
            reserved_tokens, reserved_cost = self._reserved()
            token_total = self.input_tokens + self.output_tokens + reserved_tokens + projected_tokens
            cost_total = self.cost_usd + reserved_cost + projected_cost
            if token_total > self.token_limit or cost_total > self.cost_limit_usd:
                self.rejected_calls += 1
                self.stop_reason = (
                    "Próxima chamada recusada antes do transporte: "
                    f"projeção={token_total} tokens/US${cost_total:.8f}; "
                    f"limite={self.token_limit} tokens/US${self.cost_limit_usd:.8f}."
                )
                self._persist()
                raise BudgetExceeded(self.stop_reason)
            self._reservations[call_id] = _Reservation(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=projected_tokens,
                cost_usd=projected_cost,
            )
            self.started_calls += 1
            self._persist()

    def complete(
        self,
        call_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
    ) -> None:
        with self._lock:
            reservation = self._reservations.pop(call_id, None)
            if reservation is None:
                raise ValueError(f"Chamada sem reserva ativa: {call_id}.")
            total_tokens = input_tokens + output_tokens
            cost = self._cost(input_tokens, output_tokens, cached_input_tokens)
            self.input_tokens += input_tokens
            self.cached_input_tokens += cached_input_tokens
            self.output_tokens += output_tokens
            self.cost_usd += cost
            self.completed_calls += 1
            self._calls.append(
                LLMCallUsage(
                    call_id=call_id,
                    status="completed",
                    input_tokens=input_tokens,
                    cached_input_tokens=cached_input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost,
                )
            )
            exceeded = (
                total_tokens > reservation.total_tokens
                or cost > reservation.cost_usd + 1e-12
                or self.input_tokens + self.output_tokens > self.token_limit
                or self.cost_usd > self.cost_limit_usd
            )
            if exceeded:
                self.stop_reason = "Uso retornado pelo provedor excedeu a reserva prévia."
            self._persist()
            if exceeded:
                raise BudgetExceeded(self.stop_reason)

    def complete_unaccounted(self, call_id: str) -> None:
        """Charge the full reservation when the provider omits usage metadata."""
        with self._lock:
            reservation = self._reservations.pop(call_id, None)
            if reservation is None:
                raise ValueError(f"Chamada sem reserva ativa: {call_id}.")
            self.input_tokens += reservation.input_tokens
            self.output_tokens += reservation.output_tokens
            self.cost_usd += reservation.cost_usd
            self.completed_calls += 1
            self.stop_reason = "Resposta sem metadados de uso; reserva integral contabilizada."
            self._calls.append(
                LLMCallUsage(
                    call_id=call_id,
                    status="unaccounted",
                    input_tokens=reservation.input_tokens,
                    cached_input_tokens=0,
                    output_tokens=reservation.output_tokens,
                    total_tokens=reservation.total_tokens,
                    cost_usd=reservation.cost_usd,
                    error="MissingUsageMetadata",
                )
            )
            self._persist()

    def fail(self, call_id: str, error: BaseException) -> None:
        with self._lock:
            reservation = self._reservations.pop(call_id, None)
            if reservation is None:
                return
            self.failed_calls += 1
            self._calls.append(
                LLMCallUsage(
                    call_id=call_id,
                    status="failed",
                    input_tokens=0,
                    cached_input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0,
                    error=type(error).__name__,
                )
            )
            self._persist()

    def snapshot(self) -> LLMBudgetSnapshot:
        with self._lock:
            reserved_tokens, reserved_cost = self._reserved()
            return LLMBudgetSnapshot(
                updated_at=utc_now().isoformat(),
                model=self.model,
                token_limit=self.token_limit,
                cost_limit_usd=self.cost_limit_usd,
                max_output_tokens_per_call=self.max_output_tokens_per_call,
                input_per_million_usd=self.input_per_million_usd,
                cached_input_per_million_usd=self.cached_input_per_million_usd,
                output_per_million_usd=self.output_per_million_usd,
                started_calls=self.started_calls,
                completed_calls=self.completed_calls,
                failed_calls=self.failed_calls,
                rejected_calls=self.rejected_calls,
                input_tokens=self.input_tokens,
                cached_input_tokens=self.cached_input_tokens,
                output_tokens=self.output_tokens,
                total_tokens=self.input_tokens + self.output_tokens,
                cost_usd=self.cost_usd,
                reserved_tokens=reserved_tokens,
                reserved_cost_usd=reserved_cost,
                stop_reason=self.stop_reason,
                calls=list(self._calls),
            )

    def _persist(self) -> None:
        if self.journal_path:
            atomic_write_text(self.journal_path, self.snapshot().model_dump_json(indent=2))

    def _restore(self, path: Path) -> None:
        previous = LLMBudgetSnapshot.model_validate_json(path.read_text())
        identity = (
            previous.model,
            previous.token_limit,
            previous.cost_limit_usd,
            previous.max_output_tokens_per_call,
            previous.input_per_million_usd,
            previous.cached_input_per_million_usd,
            previous.output_per_million_usd,
        )
        current = (
            self.model,
            self.token_limit,
            self.cost_limit_usd,
            self.max_output_tokens_per_call,
            self.input_per_million_usd,
            self.cached_input_per_million_usd,
            self.output_per_million_usd,
        )
        if identity != current:
            raise ValueError("Journal de LLM incompatível com os limites atuais.")
        if previous.reserved_tokens or previous.reserved_cost_usd:
            raise ValueError("Journal contém chamada interrompida sem contabilização final.")
        self.started_calls = previous.started_calls
        self.completed_calls = previous.completed_calls
        self.failed_calls = previous.failed_calls
        self.rejected_calls = previous.rejected_calls
        self.input_tokens = previous.input_tokens
        self.cached_input_tokens = previous.cached_input_tokens
        self.output_tokens = previous.output_tokens
        self.cost_usd = previous.cost_usd
        self.stop_reason = previous.stop_reason
        self._calls = list(previous.calls)


class BudgetCallbackHandler(BaseCallbackHandler):
    raise_error = True

    def __init__(self, ledger: LLMBudgetLedger):
        self.ledger = ledger
        self.encoding = tiktoken.encoding_for_model(ledger.model)

    def _message_tokens(self, messages: list[list[Any]]) -> int:
        tokens = 2
        for batch in messages:
            for message in batch:
                content = getattr(message, "content", "")
                if not isinstance(content, str):
                    content = json.dumps(content, sort_keys=True, ensure_ascii=False)
                tokens += 4 + len(self.encoding.encode(content))
        return tokens

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del serialized, kwargs
        self.ledger.reserve(str(run_id), self._message_tokens(messages))

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        del kwargs
        try:
            usage = _response_usage(response)
        except RuntimeError:
            self.ledger.complete_unaccounted(str(run_id))
            raise
        self.ledger.complete(
            str(run_id),
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        )

    def on_llm_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any
    ) -> None:
        del kwargs
        self.ledger.fail(str(run_id), error)


def _response_usage(response: Any) -> dict[str, int]:
    output = getattr(response, "llm_output", None) or {}
    usage = output.get("token_usage") or output.get("usage") or {}
    if not usage:
        try:
            usage = response.generations[0][0].message.usage_metadata or {}
        except (AttributeError, IndexError, TypeError):
            usage = {}
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    cached = usage.get(
        "cached_tokens",
        usage.get("prompt_tokens_details", {}).get(
            "cached_tokens", usage.get("input_token_details", {}).get("cache_read", 0)
        ),
    )
    if input_tokens is None or output_tokens is None:
        raise RuntimeError("Resposta LLM sem contabilidade de tokens; execução interrompida.")
    return {
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "cached_input_tokens": int(cached or 0),
    }
