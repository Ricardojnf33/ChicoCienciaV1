import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.core.atomic_io import atomic_write_text
from src.core.contracts import file_sha256, utc_now

ConditionName = Literal["B0", "B1", "A", "A0"]
DatasetName = Literal["iris", "wine", "digits"]
RunKind = Literal["pilot", "main"]

CONDITIONS: tuple[ConditionName, ...] = ("B0", "B1", "A", "A0")
DATASETS: tuple[DatasetName, ...] = ("iris", "wine", "digits")
SEEDS = (11, 23, 37, 51, 71)
MODEL_SNAPSHOT = "gpt-4o-mini-2024-07-18"


class PricingSnapshot(BaseModel):
    model: str = MODEL_SNAPSHOT
    input_per_million_usd: float = Field(default=0.15, ge=0)
    cached_input_per_million_usd: float = Field(default=0.075, ge=0)
    output_per_million_usd: float = Field(default=0.60, ge=0)
    source: str = "https://developers.openai.com/api/docs/models/gpt-4o-mini"
    observed_on: str = "2026-09-11"


class CampaignLimits(BaseModel):
    attempts_per_run: int = Field(default=6, ge=1)
    corrections_per_node: int = Field(default=2, ge=0)
    wall_time_seconds: int = Field(default=900, ge=1)
    tokens_per_generative_run: int = Field(default=40_000, ge=1)
    cost_per_generative_run_usd: float = Field(default=0.03, gt=0)
    campaign_token_limit: int = Field(default=2_040_000, ge=1)
    campaign_cost_limit_usd: float = Field(default=1.53, gt=0)


class CampaignRunSpec(BaseModel):
    run_id: str = Field(min_length=1)
    kind: RunKind
    sequence: int = Field(ge=1)
    condition: ConditionName
    dataset: DatasetName
    seed: int
    objective_path: str = Field(min_length=1)
    objective_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    uses_llm: bool
    token_limit: int = Field(ge=0)
    cost_limit_usd: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_condition_budget(self):
        if self.condition == "B0" and (
            self.uses_llm or self.token_limit != 0 or self.cost_limit_usd != 0
        ):
            raise ValueError("B0 deve registrar uso e custo de LLM iguais a zero.")
        if self.condition != "B0" and (
            not self.uses_llm or self.token_limit == 0 or self.cost_limit_usd == 0
        ):
            raise ValueError("Condição generativa requer limites positivos de LLM.")
        return self


class EmpiricalCampaignPlan(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    campaign_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    protocol_frozen: bool = False
    api_calls_performed: int = Field(default=0, ge=0)
    randomization_seed: int = 20260911
    model_text: str = MODEL_SNAPSHOT
    model_vision: str = MODEL_SNAPSHOT
    pricing: PricingSnapshot = Field(default_factory=PricingSnapshot)
    limits: CampaignLimits = Field(default_factory=CampaignLimits)
    runs: list[CampaignRunSpec]

    @model_validator(mode="after")
    def validate_matrix(self):
        ids = [run.run_id for run in self.runs]
        if len(ids) != len(set(ids)):
            raise ValueError("O plano contém run_id duplicado.")
        main = [run for run in self.runs if run.kind == "main"]
        pilots = [run for run in self.runs if run.kind == "pilot"]
        expected = {
            (condition, dataset, seed)
            for condition in CONDITIONS
            for dataset in DATASETS
            for seed in SEEDS
        }
        observed = {(run.condition, run.dataset, run.seed) for run in main}
        if len(main) != 60 or observed != expected:
            raise ValueError("Matriz principal deve conter 4 × 3 × 5 = 60 runs.")
        pilot_counts = Counter(run.condition for run in pilots)
        if len(pilots) != 6 or pilot_counts != Counter({"B1": 2, "A": 2, "A0": 2}):
            raise ValueError("Piloto deve conter dois runs de B1, A e A0.")
        if any(run.dataset == "digits" or run.condition == "B0" for run in pilots):
            raise ValueError("Pilotos são generativos e restritos a Iris/Wine.")
        generative_count = sum(run.uses_llm for run in self.runs)
        expected_tokens = generative_count * self.limits.tokens_per_generative_run
        expected_cost = generative_count * self.limits.cost_per_generative_run_usd
        if self.limits.campaign_token_limit != expected_tokens:
            raise ValueError("Teto de tokens não corresponde aos 51 runs generativos.")
        if abs(self.limits.campaign_cost_limit_usd - expected_cost) > 1e-9:
            raise ValueError("Teto monetário não corresponde aos limites por run.")
        return self


def _run_spec(
    *,
    kind: RunKind,
    sequence: int,
    condition: ConditionName,
    dataset: DatasetName,
    seed: int,
    objective_root: Path,
    limits: CampaignLimits,
) -> CampaignRunSpec:
    objective = objective_root / f"{dataset}.yaml"
    if not objective.is_file():
        raise FileNotFoundError(objective)
    uses_llm = condition != "B0"
    return CampaignRunSpec(
        run_id=f"{kind}-{sequence:02d}-{condition.lower()}-{dataset}-s{seed}",
        kind=kind,
        sequence=sequence,
        condition=condition,
        dataset=dataset,
        seed=seed,
        objective_path=str(objective),
        objective_sha256=file_sha256(objective),
        uses_llm=uses_llm,
        token_limit=limits.tokens_per_generative_run if uses_llm else 0,
        cost_limit_usd=limits.cost_per_generative_run_usd if uses_llm else 0,
    )


def build_campaign_plan(
    *,
    campaign_id: str,
    objective_root: str | Path = "objectives",
    randomization_seed: int = 20260911,
) -> EmpiricalCampaignPlan:
    root = Path(objective_root)
    limits = CampaignLimits()
    pilot_matrix: list[tuple[ConditionName, DatasetName, int]] = [
        ("B1", "iris", 11),
        ("A", "wine", 11),
        ("A0", "iris", 23),
        ("B1", "wine", 23),
        ("A", "iris", 37),
        ("A0", "wine", 37),
    ]
    main_matrix = [
        (condition, dataset, seed)
        for dataset in DATASETS
        for seed in SEEDS
        for condition in CONDITIONS
    ]
    random.Random(randomization_seed).shuffle(main_matrix)
    runs = [
        _run_spec(
            kind="pilot",
            sequence=index,
            condition=condition,
            dataset=dataset,
            seed=seed,
            objective_root=root,
            limits=limits,
        )
        for index, (condition, dataset, seed) in enumerate(pilot_matrix, start=1)
    ]
    runs.extend(
        _run_spec(
            kind="main",
            sequence=index,
            condition=condition,
            dataset=dataset,
            seed=seed,
            objective_root=root,
            limits=limits,
        )
        for index, (condition, dataset, seed) in enumerate(main_matrix, start=1)
    )
    return EmpiricalCampaignPlan(
        campaign_id=campaign_id,
        randomization_seed=randomization_seed,
        runs=runs,
    )


def write_campaign_plan(
    path: str | Path, plan: EmpiricalCampaignPlan
) -> Path:
    validated = EmpiricalCampaignPlan.model_validate(plan.model_dump())
    return atomic_write_text(path, validated.model_dump_json(indent=2))
