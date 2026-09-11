from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.core.atomic_io import atomic_write_text
from src.core.contracts import ContractError, utc_now


class EvaluationDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"
    NOT_EVALUATED = "NOT_EVALUATED"


class CriterionState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"


class EvaluationRecord(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    node_id: str = Field(min_length=1)
    attempt: int = Field(ge=1)
    evaluator: Literal["reviewer", "vlm"]
    decision: EvaluationDecision
    evaluated: bool
    synthetic: bool = False
    rationale: str = Field(min_length=8)
    criteria: dict[str, CriterionState] = Field(default_factory=dict)
    evidence_paths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_semantics(self):
        if self.decision is EvaluationDecision.NOT_EVALUATED:
            if self.evaluated:
                raise ValueError("NOT_EVALUATED exige evaluated=false.")
            if any(value is not CriterionState.NOT_EVALUATED for value in self.criteria.values()):
                raise ValueError("Critérios não avaliados não podem declarar PASS ou FAIL.")
        elif not self.evaluated:
            raise ValueError("Uma decisão substantiva exige evaluated=true.")
        if self.decision is EvaluationDecision.APPROVED and (
            not self.criteria
            or any(value is not CriterionState.PASS for value in self.criteria.values())
        ):
            raise ValueError("APPROVED exige todos os critérios em PASS.")
        if len(self.evidence_paths) != len(set(self.evidence_paths)):
            raise ValueError("Caminhos de evidência não podem ser duplicados.")
        return self


def not_evaluated_record(
    *,
    node_id: str,
    attempt: int,
    evaluator: Literal["reviewer", "vlm"],
    rationale: str,
    synthetic: bool,
) -> EvaluationRecord:
    return EvaluationRecord(
        node_id=node_id,
        attempt=attempt,
        evaluator=evaluator,
        decision=EvaluationDecision.NOT_EVALUATED,
        evaluated=False,
        synthetic=synthetic,
        rationale=rationale,
        criteria={"assessment": CriterionState.NOT_EVALUATED},
    )


def write_evaluation(path: str | Path, evaluation: EvaluationRecord) -> Path:
    return atomic_write_text(path, evaluation.model_dump_json(indent=2))


def load_evaluation(
    path: str | Path,
    *,
    node_id: str,
    attempt: int,
    evaluator: Literal["reviewer", "vlm"],
) -> EvaluationRecord:
    evaluation_path = Path(path)
    if not evaluation_path.is_file():
        raise ContractError(f"Avaliação ausente: {evaluation_path}")
    try:
        record = EvaluationRecord.model_validate_json(evaluation_path.read_text())
    except Exception as exc:
        raise ContractError(f"Avaliação inválida em {evaluation_path}: {exc}") from exc
    expected = {"node_id": node_id, "attempt": attempt, "evaluator": evaluator}
    for field, value in expected.items():
        if getattr(record, field) != value:
            raise ContractError(
                f"Identidade da avaliação inválida: {field}={getattr(record, field)!r}, "
                f"esperado {value!r}."
            )
    for evidence_path in record.evidence_paths:
        if not Path(evidence_path).is_file():
            raise ContractError(f"Evidência da avaliação ausente: {evidence_path}")
    return record
