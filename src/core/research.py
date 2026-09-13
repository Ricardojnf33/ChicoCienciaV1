import hashlib
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class HypothesisSpec(BaseModel):
    hypothesis_id: str = Field(pattern=r"^h-[0-9a-f]{8}$")
    statement: str = Field(min_length=8)
    rationale: str = Field(min_length=8)
    falsification_criterion: str = Field(min_length=8)
    source: Literal["objective", "agent", "derived"] = "objective"

    @classmethod
    def from_statement(cls, statement: str, primary_metric: str) -> "HypothesisSpec":
        normalized = " ".join(statement.split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()[:8]
        return cls(
            hypothesis_id=f"h-{digest}",
            statement=normalized,
            rationale="Hipótese declarada no objetivo versionado do experimento.",
            falsification_criterion=(
                f"A evidência não sustenta mudança consistente em {primary_metric}."
            ),
        )


class ExperimentPlan(BaseModel):
    plan_id: str = Field(pattern=r"^p-[0-9a-f]{10}$")
    hypothesis_id: str = Field(pattern=r"^h-[0-9a-f]{8}$")
    decision_key: str = Field(min_length=3, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    description: str = Field(min_length=8)
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_artifacts: list[str] = Field(default_factory=lambda: ["results.json"])

    @model_validator(mode="after")
    def reject_unsafe_parameters(self):
        def is_json_value(value: Any) -> bool:
            if value is None or isinstance(value, (str, int, float, bool)):
                return True
            if isinstance(value, list):
                return all(is_json_value(item) for item in value)
            if isinstance(value, dict):
                return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
            return False

        if not is_json_value(self.parameters):
            raise ValueError("Parâmetros do plano devem ser serializáveis em JSON.")
        if len(self.expected_artifacts) != len(set(self.expected_artifacts)):
            raise ValueError("Artefatos esperados não podem ser duplicados.")
        return self

    @classmethod
    def build(
        cls,
        *,
        hypothesis_id: str,
        decision_key: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> "ExperimentPlan":
        digest = hashlib.sha256(
            f"{hypothesis_id}:{decision_key}".encode()
        ).hexdigest()[:10]
        return cls(
            plan_id=f"p-{digest}",
            hypothesis_id=hypothesis_id,
            decision_key=decision_key,
            description=description,
            parameters=parameters or {},
        )


class ExpansionCandidate(BaseModel):
    hypothesis: HypothesisSpec
    plan: ExperimentPlan

    @model_validator(mode="after")
    def identities_must_match(self):
        if self.hypothesis.hypothesis_id != self.plan.hypothesis_id:
            raise ValueError("Plano e hipótese possuem identidades divergentes.")
        return self
