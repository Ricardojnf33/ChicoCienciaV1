import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.core.atomic_io import atomic_write_text
from src.core.campaign import (
    CampaignRunSpec,
    EmpiricalCampaignPlan,
    load_campaign_plan,
)
from src.core.contracts import (
    RunManifest,
    file_sha256,
    load_manifest,
    save_manifest,
    utc_now,
)
from src.core.tree import AgenticTree
from src.core.llm_budget import LLMBudgetSnapshot
from src.core.variants import ExperimentVariant, policy_for
from src.processes.ats_process import ExecutionMode, run_agentic_tree


PILOT_AUTHORIZATION = "I_AUTHORIZE_SIX_PILOT_RUNS"
CrewFactory = Callable[[CampaignRunSpec, Path], Any]
PilotStatus = Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]


class PilotRunRecord(BaseModel):
    run_id: str = Field(min_length=1)
    condition: Literal["B1", "A", "A0"]
    dataset: Literal["iris", "wine"]
    seed: int
    status: PilotStatus = "PENDING"
    run_directory: str = Field(min_length=1)
    tree_path: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    call_limit: int = Field(gt=0)
    token_limit: int = Field(gt=0)
    cost_limit_usd: float = Field(gt=0)
    llm_started_calls: int = Field(default=0, ge=0)
    llm_total_tokens: int = Field(default=0, ge=0)
    llm_cost_usd: float = Field(default=0, ge=0)
    error: str | None = None

    @model_validator(mode="after")
    def validate_failure(self):
        if self.status == "FAILED" and not self.error:
            raise ValueError("Piloto FAILED requer erro explícito.")
        if self.llm_started_calls > self.call_limit:
            raise ValueError("Piloto excedeu o teto declarado de chamadas.")
        if self.llm_total_tokens > self.token_limit:
            raise ValueError("Piloto excedeu o teto declarado de tokens.")
        if self.llm_cost_usd > self.cost_limit_usd:
            raise ValueError("Piloto excedeu o teto monetário declarado.")
        return self


class PilotCampaignManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    campaign_id: str = Field(min_length=1)
    campaign_plan_path: str = Field(min_length=1)
    campaign_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: Literal["mock", "live"]
    status: PilotStatus = "PENDING"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    api_calls_started: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0, ge=0)
    call_limit: int = Field(gt=0)
    token_limit: int = Field(gt=0)
    cost_limit_usd: float = Field(gt=0)
    runs: list[PilotRunRecord]

    @model_validator(mode="after")
    def validate_pilot_matrix(self):
        ids = [run.run_id for run in self.runs]
        if len(ids) != 6 or len(ids) != len(set(ids)):
            raise ValueError("Manifesto de pilotos exige seis run_id distintos.")
        if self.mode == "mock" and (
            self.api_calls_started or self.total_tokens or self.cost_usd
        ):
            raise ValueError("Ensaio mock deve registrar consumo LLM igual a zero.")
        if self.api_calls_started > self.call_limit:
            raise ValueError("Campanha piloto excedeu o teto de chamadas.")
        if self.total_tokens > self.token_limit:
            raise ValueError("Campanha piloto excedeu o teto de tokens.")
        if self.cost_usd > self.cost_limit_usd:
            raise ValueError("Campanha piloto excedeu o teto monetário.")
        return self


def _save_pilot_manifest(path: Path, manifest: PilotCampaignManifest) -> Path:
    manifest.updated_at = utc_now()
    validated = PilotCampaignManifest.model_validate(manifest.model_dump())
    return atomic_write_text(path, validated.model_dump_json(indent=2))


def _sync_record(record: PilotRunRecord, manifest: RunManifest) -> None:
    record.status = manifest.status
    record.llm_started_calls = manifest.llm_started_calls
    record.llm_total_tokens = manifest.llm_total_tokens
    record.llm_cost_usd = manifest.llm_cost_usd
    record.error = None


def _sync_totals(manifest: PilotCampaignManifest) -> None:
    manifest.api_calls_started = sum(run.llm_started_calls for run in manifest.runs)
    manifest.total_tokens = sum(run.llm_total_tokens for run in manifest.runs)
    manifest.cost_usd = sum(run.llm_cost_usd for run in manifest.runs)


def _validate_plan(plan: EmpiricalCampaignPlan) -> None:
    if plan.protocol_frozen:
        raise ValueError("Pilotos devem preceder o congelamento do protocolo.")
    if plan.api_calls_performed != 0:
        raise ValueError("Plano inicial de pilotos deve registrar zero chamadas.")


def _record_for_spec(spec: CampaignRunSpec, run_dir: Path) -> PilotRunRecord:
    return PilotRunRecord(
        run_id=spec.run_id,
        condition=spec.condition,
        dataset=spec.dataset,
        seed=spec.seed,
        run_directory=str(run_dir),
        tree_path=str(run_dir / "tree.json"),
        manifest_path=str(run_dir / "manifest.json"),
        call_limit=spec.call_limit,
        token_limit=spec.token_limit,
        cost_limit_usd=spec.cost_limit_usd,
    )


def _validate_run_identity(
    manifest: RunManifest,
    spec: CampaignRunSpec,
    *,
    plan_sha256: str,
    mode: ExecutionMode,
) -> None:
    expected = (
        spec.run_id,
        spec.condition,
        spec.seed,
        spec.objective_sha256,
        plan_sha256,
        spec.token_limit,
        spec.cost_limit_usd,
        spec.call_limit,
    )
    observed = (
        manifest.run_id,
        manifest.variant,
        manifest.experiment_seed,
        manifest.objective_sha256,
        manifest.campaign_plan_sha256,
        manifest.llm_token_limit,
        manifest.llm_cost_limit_usd,
        manifest.llm_call_limit,
    )
    if observed != expected:
        raise ValueError(f"Identidade ou limites divergentes no run {spec.run_id}.")
    if any(attempt.mode != mode.value for attempt in manifest.attempts):
        raise ValueError(f"Modo de tentativa divergente no run {spec.run_id}.")


def _execute_pilot_record(
    *,
    plan: EmpiricalCampaignPlan,
    plan_sha256: str,
    spec: CampaignRunSpec,
    record: PilotRunRecord,
    mode: ExecutionMode,
    crew_factory: CrewFactory | None,
    branching: int,
    max_depth: int,
    max_branching: int,
) -> None:
    run_dir = Path(record.run_directory)
    tree_path = Path(record.tree_path)
    manifest_path = Path(record.manifest_path)
    if file_sha256(spec.objective_path) != spec.objective_sha256:
        raise ValueError(f"Objetivo alterado após o plano: {spec.objective_path}")
    run_dir.mkdir(parents=True, exist_ok=True)
    if tree_path.is_file() != manifest_path.is_file():
        raise ValueError(f"Checkpoint parcial inconsistente: {record.run_id}")

    variant = ExperimentVariant(spec.condition)
    if tree_path.is_file():
        tree = AgenticTree.load_json(str(tree_path))
        run_manifest = load_manifest(manifest_path)
        _validate_run_identity(
            run_manifest,
            spec,
            plan_sha256=plan_sha256,
            mode=mode,
        )
        if run_manifest.status == "SUCCEEDED":
            _sync_record(record, run_manifest)
            return
    else:
        tree = AgenticTree.new(
            objective_yaml=spec.objective_path,
            artifact_root=str(run_dir / "artifacts"),
            max_depth=max_depth,
            max_branching=max_branching,
        )
        policy = policy_for(variant)
        run_manifest = RunManifest(
            run_id=spec.run_id,
            objective_path=spec.objective_path,
            objective_sha256=spec.objective_sha256,
            campaign_plan_sha256=plan_sha256,
            primary_metric=tree.primary_metric,
            variant=variant.value,
            budget=plan.limits.attempts_per_run,
            branching=branching,
            effective_branching=policy.effective_branching(branching),
            max_depth=max_depth,
            automatic_correction=policy.automatic_correction,
            experiment_seed=spec.seed,
            llm_model=plan.model_text,
            llm_token_limit=spec.token_limit,
            llm_cost_limit_usd=spec.cost_limit_usd,
            llm_call_limit=spec.call_limit,
        )
        tree.save_json(str(tree_path))
        save_manifest(manifest_path, run_manifest)

    record.status = "RUNNING"
    record.error = None
    try:
        crew = crew_factory(spec, run_dir / "llm-budget.json") if crew_factory else None
        if crew is not None:
            from src.crews.ai_scientist_v2 import budget_for_crew

            budget = budget_for_crew(crew).snapshot()
            if (
                budget.token_limit != spec.token_limit
                or budget.cost_limit_usd != spec.cost_limit_usd
                or budget.call_limit != spec.call_limit
            ):
                raise ValueError("Crew diverge dos limites declarados no piloto.")
        run_agentic_tree(
            crew,
            tree,
            budget=plan.limits.attempts_per_run,
            branching=branching,
            checkpoint_path=str(tree_path),
            mode=mode,
            sqlite_url=f"sqlite:///{run_dir / 'run.db'}",
            manifest=run_manifest,
            manifest_path=str(manifest_path),
            variant=variant,
            experiment_seed=spec.seed,
        )
        tree.save_json(str(tree_path))
        completed = load_manifest(manifest_path)
        _validate_run_identity(
            completed,
            spec,
            plan_sha256=plan_sha256,
            mode=mode,
        )
        _sync_record(record, completed)
    except Exception as exc:
        record.status = "FAILED"
        record.error = f"{type(exc).__name__}: {exc}"
        if manifest_path.is_file():
            persisted = load_manifest(manifest_path)
            record.llm_started_calls = persisted.llm_started_calls
            record.llm_total_tokens = persisted.llm_total_tokens
            record.llm_cost_usd = persisted.llm_cost_usd
        raise


def _new_manifest(
    plan_path: Path,
    output_root: Path,
    mode: ExecutionMode,
) -> PilotCampaignManifest:
    plan = load_campaign_plan(plan_path)
    pilots = [run for run in plan.runs if run.kind == "pilot"]
    campaign_dir = output_root / plan.campaign_id
    return PilotCampaignManifest(
        campaign_id=plan.campaign_id,
        campaign_plan_path=str(plan_path),
        campaign_plan_sha256=file_sha256(plan_path),
        mode=mode.value,
        call_limit=sum(spec.call_limit for spec in pilots),
        token_limit=sum(spec.token_limit for spec in pilots),
        cost_limit_usd=sum(spec.cost_limit_usd for spec in pilots),
        runs=[
            _record_for_spec(spec, campaign_dir / spec.run_id)
            for spec in pilots
        ],
    )


def run_pilot_campaign(
    campaign_plan_path: str | Path,
    output_root: str | Path,
    *,
    mode: ExecutionMode = ExecutionMode.MOCK,
    authorization: str | None = None,
    crew_factory: CrewFactory | None = None,
    branching: int = 2,
    max_depth: int = 3,
    max_branching: int = 3,
) -> tuple[PilotCampaignManifest, Path]:
    """Executa ou retoma somente os seis pilotos declarados no plano."""
    mode = ExecutionMode(mode)
    if mode is ExecutionMode.LIVE and authorization != PILOT_AUTHORIZATION:
        raise PermissionError("Pilotos live exigem autorização literal separada.")
    if mode is ExecutionMode.LIVE and crew_factory is None:
        raise ValueError("Pilotos live exigem crew_factory com orçamento por run.")

    plan_path = Path(campaign_plan_path)
    plan = load_campaign_plan(plan_path)
    _validate_plan(plan)
    plan_sha = file_sha256(plan_path)
    campaign_dir = Path(output_root) / plan.campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    pilot_manifest_path = campaign_dir / "pilot-manifest.json"

    if pilot_manifest_path.is_file():
        aggregate = PilotCampaignManifest.model_validate_json(
            pilot_manifest_path.read_text()
        )
        if (
            aggregate.campaign_plan_sha256 != plan_sha
            or aggregate.mode != mode.value
        ):
            raise ValueError("Retomada recusada: plano ou modo diverge do manifesto.")
    else:
        aggregate = _new_manifest(plan_path, Path(output_root), mode)
        _save_pilot_manifest(pilot_manifest_path, aggregate)

    specs = {run.run_id: run for run in plan.runs if run.kind == "pilot"}
    aggregate.status = "RUNNING"
    _save_pilot_manifest(pilot_manifest_path, aggregate)
    for record in aggregate.runs:
        spec = specs[record.run_id]
        record_path = Path(record.run_directory) / "pilot-run-record.json"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        _save_pilot_manifest(pilot_manifest_path, aggregate)
        try:
            _execute_pilot_record(
                plan=plan,
                plan_sha256=plan_sha,
                spec=spec,
                record=record,
                mode=mode,
                crew_factory=crew_factory,
                branching=branching,
                max_depth=max_depth,
                max_branching=max_branching,
            )
            atomic_write_text(record_path, record.model_dump_json(indent=2))
        except Exception as exc:
            atomic_write_text(record_path, record.model_dump_json(indent=2))
            _sync_totals(aggregate)
            aggregate.status = "FAILED"
            _save_pilot_manifest(pilot_manifest_path, aggregate)
            raise RuntimeError(
                f"Piloto {record.run_id} falhou; consulte {pilot_manifest_path}."
            ) from exc
        _sync_totals(aggregate)
        _save_pilot_manifest(pilot_manifest_path, aggregate)

    _sync_totals(aggregate)
    aggregate.status = "SUCCEEDED"
    _save_pilot_manifest(pilot_manifest_path, aggregate)
    return aggregate, pilot_manifest_path


def run_pilot(
    campaign_plan_path: str | Path,
    run_id: str,
    output_root: str | Path,
    *,
    mode: ExecutionMode = ExecutionMode.MOCK,
    authorization: str | None = None,
    crew_factory: CrewFactory | None = None,
    branching: int = 2,
    max_depth: int = 3,
    max_branching: int = 3,
) -> tuple[PilotRunRecord, Path]:
    """Executa ou retoma uma única identidade piloto da matriz fechada."""
    mode = ExecutionMode(mode)
    if mode is ExecutionMode.LIVE and authorization != PILOT_AUTHORIZATION:
        raise PermissionError("Piloto live exige autorização literal separada.")
    if mode is ExecutionMode.LIVE and crew_factory is None:
        raise ValueError("Piloto live exige crew_factory com orçamento por run.")

    plan_path = Path(campaign_plan_path)
    plan = load_campaign_plan(plan_path)
    _validate_plan(plan)
    try:
        spec = next(
            item for item in plan.runs if item.kind == "pilot" and item.run_id == run_id
        )
    except StopIteration as exc:
        raise ValueError(f"run_id não pertence à matriz piloto: {run_id}") from exc

    run_dir = Path(output_root) / plan.campaign_id / spec.run_id
    record_path = run_dir / "pilot-run-record.json"
    record = _record_for_spec(spec, run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(record_path, record.model_dump_json(indent=2))
    try:
        _execute_pilot_record(
            plan=plan,
            plan_sha256=file_sha256(plan_path),
            spec=spec,
            record=record,
            mode=mode,
            crew_factory=crew_factory,
            branching=branching,
            max_depth=max_depth,
            max_branching=max_branching,
        )
    except Exception as exc:
        atomic_write_text(record_path, record.model_dump_json(indent=2))
        raise RuntimeError(
            f"Piloto {run_id} falhou; consulte {record_path}."
        ) from exc
    atomic_write_text(record_path, record.model_dump_json(indent=2))
    return record, record_path


def _assert_safe_budget_journal(path: Path) -> LLMBudgetSnapshot:
    payload = json.loads(path.read_text())
    forbidden = {"api_key", "authorization", "raw_response", "response_body", "response_text"}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in forbidden:
                    raise ValueError(f"Journal contém campo proibido: {key}")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return LLMBudgetSnapshot.model_validate(payload)


def aggregate_pilot_artifacts(
    campaign_plan_path: str | Path,
    campaign_dir: str | Path,
    output_path: str | Path,
    *,
    mode: ExecutionMode,
) -> tuple[PilotCampaignManifest, Path, Path]:
    """Valida seis bundles independentes e produz relatório agregado e checksums."""
    mode = ExecutionMode(mode)
    plan_path = Path(campaign_plan_path)
    plan = load_campaign_plan(plan_path)
    _validate_plan(plan)
    plan_sha = file_sha256(plan_path)
    root = Path(campaign_dir)
    if root.name != plan.campaign_id:
        raise ValueError("Diretório agregado deve ter o campaign_id como nome.")

    aggregate = _new_manifest(plan_path, root.parent, mode)
    specs = [run for run in plan.runs if run.kind == "pilot"]
    checksums: dict[str, str] = {str(plan_path): plan_sha}
    for spec, record in zip(specs, aggregate.runs, strict=True):
        run_dir = root / spec.run_id
        tree_path = run_dir / "tree.json"
        manifest_path = run_dir / "manifest.json"
        record_path = run_dir / "pilot-run-record.json"
        for required in (tree_path, manifest_path, record_path):
            if not required.is_file():
                raise FileNotFoundError(f"Artefato piloto ausente: {required}")
        persisted_record = PilotRunRecord.model_validate_json(record_path.read_text())
        record_identity = (
            persisted_record.run_id,
            persisted_record.condition,
            persisted_record.dataset,
            persisted_record.seed,
            persisted_record.call_limit,
            persisted_record.token_limit,
            persisted_record.cost_limit_usd,
            persisted_record.status,
        )
        expected_record_identity = (
            spec.run_id,
            spec.condition,
            spec.dataset,
            spec.seed,
            spec.call_limit,
            spec.token_limit,
            spec.cost_limit_usd,
            "SUCCEEDED",
        )
        if record_identity != expected_record_identity:
            raise ValueError(f"Registro piloto inválido: {spec.run_id}")
        run_manifest = load_manifest(manifest_path)
        _validate_run_identity(
            run_manifest,
            spec,
            plan_sha256=plan_sha,
            mode=mode,
        )
        if run_manifest.status != "SUCCEEDED":
            raise ValueError(f"Piloto não concluído: {spec.run_id}")
        if (
            persisted_record.llm_started_calls,
            persisted_record.llm_total_tokens,
            persisted_record.llm_cost_usd,
        ) != (
            run_manifest.llm_started_calls,
            run_manifest.llm_total_tokens,
            run_manifest.llm_cost_usd,
        ):
            raise ValueError(f"Registro e manifesto divergem: {spec.run_id}")
        if mode is ExecutionMode.LIVE:
            budget_path = run_dir / "llm-budget.json"
            if not budget_path.is_file():
                raise FileNotFoundError(f"Journal LLM ausente: {budget_path}")
            budget = _assert_safe_budget_journal(budget_path)
            budget_identity = (
                budget.model,
                budget.call_limit,
                budget.token_limit,
                budget.cost_limit_usd,
                budget.started_calls,
                budget.total_tokens,
                budget.cost_usd,
            )
            manifest_identity = (
                run_manifest.llm_model,
                run_manifest.llm_call_limit,
                run_manifest.llm_token_limit,
                run_manifest.llm_cost_limit_usd,
                run_manifest.llm_started_calls,
                run_manifest.llm_total_tokens,
                run_manifest.llm_cost_usd,
            )
            if budget_identity != manifest_identity:
                raise ValueError(f"Journal e manifesto divergem: {spec.run_id}")
            if budget.reserved_tokens or budget.reserved_cost_usd:
                raise ValueError(f"Piloto terminou com reserva ativa: {spec.run_id}")
            checksums[str(budget_path.relative_to(root))] = file_sha256(budget_path)
        elif (
            run_manifest.llm_started_calls
            or run_manifest.llm_total_tokens
            or run_manifest.llm_cost_usd
        ):
            raise ValueError(f"Piloto mock registrou consumo LLM: {spec.run_id}")

        record.run_directory = str(run_dir)
        record.tree_path = str(tree_path)
        record.manifest_path = str(manifest_path)
        _sync_record(record, run_manifest)
        for artifact in (tree_path, manifest_path, record_path):
            checksums[str(artifact.relative_to(root))] = file_sha256(artifact)

    _sync_totals(aggregate)
    aggregate.status = "SUCCEEDED"
    report_path = Path(output_path)
    _save_pilot_manifest(report_path, aggregate)
    checksum_path = report_path.with_name("pilot-checksums.json")
    atomic_write_text(
        checksum_path,
        json.dumps(dict(sorted(checksums.items())), indent=2, ensure_ascii=False),
    )
    return aggregate, report_path, checksum_path
