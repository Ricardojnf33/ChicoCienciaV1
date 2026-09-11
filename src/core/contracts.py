import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.core.atomic_io import atomic_write_text

ContractMode = Literal["mock", "live", "replay"]
ContractStatus = Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]
VariantName = Literal["B1", "A", "A0"]
EvaluationDecisionName = Literal[
    "APPROVED", "REJECTED", "NEEDS_REVISION", "NOT_EVALUATED"
]


class ContractError(ValueError):
    """Raised when an artifact cannot satisfy the declared contract."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionEvidence(BaseModel):
    mode: ContractMode
    synthetic: bool
    network_used: bool
    return_code: int
    timed_out: bool = False
    duration_seconds: float = Field(default=0.0, ge=0.0)
    stdout_path: str | None = None
    stderr_path: str | None = None
    network_isolated: bool = False


class ArtifactRecord(BaseModel):
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class CanonicalResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    node_id: str = Field(min_length=1)
    attempt: int = Field(ge=1)
    status: Literal["SUCCEEDED"]
    primary_metric: str = Field(min_length=1)
    metrics: dict[str, float]
    execution: ExecutionEvidence
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    source: Literal["canonical", "legacy-adapter"] = "canonical"

    @model_validator(mode="after")
    def validate_success(self):
        if self.primary_metric not in self.metrics:
            raise ValueError("A métrica primária deve existir em metrics.")
        for name, value in self.metrics.items():
            if not math.isfinite(value):
                raise ValueError(f"A métrica {name!r} deve ser finita.")
        primary_value = self.metrics[self.primary_metric]
        if not 0.0 <= primary_value <= 1.0:
            raise ValueError("A métrica primária deve estar no intervalo [0, 1].")
        if self.execution.return_code != 0:
            raise ValueError("Resultado SUCCEEDED requer return_code igual a zero.")
        if self.execution.timed_out:
            raise ValueError("Resultado SUCCEEDED não pode ter excedido o timeout.")
        if self.execution.mode == "mock" and not self.execution.synthetic:
            raise ValueError("Resultado mock deve ser marcado como sintético.")
        if self.execution.mode == "live" and self.execution.synthetic:
            raise ValueError("Resultado live não pode ser marcado como sintético.")
        return self


class AttemptRecord(BaseModel):
    node_id: str = Field(min_length=1)
    attempt: int = Field(ge=1)
    mode: ContractMode
    status: ContractStatus
    directory: str = Field(min_length=1)
    result_path: str | None = None
    result_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    error: str | None = None
    reviewer_path: str | None = None
    reviewer_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    reviewer_decision: EvaluationDecisionName | None = None
    vlm_path: str | None = None
    vlm_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    vlm_decision: EvaluationDecisionName | None = None
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None

    @model_validator(mode="after")
    def validate_terminal_state(self):
        if self.status == "SUCCEEDED" and (
            not self.result_path or not self.result_sha256 or not self.finished_at
        ):
            raise ValueError("Tentativa SUCCEEDED requer resultado, hash e término.")
        if self.status == "FAILED" and (not self.error or not self.finished_at):
            raise ValueError("Tentativa FAILED requer erro e término.")
        review_fields = (
            self.reviewer_path,
            self.reviewer_sha256,
            self.reviewer_decision,
        )
        if any(review_fields) and not all(review_fields):
            raise ValueError("Registro de Reviewer deve conter caminho, hash e decisão.")
        vlm_fields = (self.vlm_path, self.vlm_sha256, self.vlm_decision)
        if any(vlm_fields) and not all(vlm_fields):
            raise ValueError("Registro de VLM deve conter caminho, hash e decisão.")
        return self


class RunManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(min_length=1)
    objective_path: str = Field(min_length=1)
    primary_metric: str = Field(min_length=1)
    variant: VariantName = "A"
    budget: int = Field(default=0, ge=0)
    branching: int = Field(default=2, ge=1)
    effective_branching: int = Field(default=2, ge=1)
    max_depth: int = Field(default=4, ge=0)
    automatic_correction: bool = True
    status: ContractStatus = "PENDING"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    attempts: list[AttemptRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_attempts(self):
        keys = [(item.node_id, item.attempt) for item in self.attempts]
        if len(keys) != len(set(keys)):
            raise ValueError("O manifesto contém tentativas duplicadas.")
        expected_correction = self.variant != "A0"
        if self.automatic_correction != expected_correction:
            raise ValueError("Política de correção divergente da variante.")
        if self.variant == "B1" and self.effective_branching != 1:
            raise ValueError("B1 exige sequência fixa com effective_branching=1.")
        if self.variant != "B1" and self.effective_branching != self.branching:
            raise ValueError("A e A0 devem preservar o branching solicitado.")
        return self


class ComparisonRunRecord(BaseModel):
    run_id: str = Field(min_length=1)
    variant: VariantName
    status: ContractStatus = "PENDING"
    run_directory: str = Field(min_length=1)
    tree_path: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    error: str | None = None

    @model_validator(mode="after")
    def validate_failure(self):
        if self.status == "FAILED" and not self.error:
            raise ValueError("Run comparativo FAILED requer erro explícito.")
        return self


class ComparisonManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    campaign_id: str = Field(min_length=1)
    objective_path: str = Field(min_length=1)
    objective_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: Literal["mock", "live"]
    budget: int = Field(ge=1)
    branching: int = Field(ge=1)
    max_depth: int = Field(ge=0)
    max_branching: int = Field(ge=1)
    status: ContractStatus = "PENDING"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    runs: list[ComparisonRunRecord]

    @model_validator(mode="after")
    def validate_design(self):
        variants = [run.variant for run in self.runs]
        if sorted(variants) != ["A", "A0", "B1"]:
            raise ValueError("Comparação exige exatamente um run de B1, A e A0.")
        run_ids = [run.run_id for run in self.runs]
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Runs comparativos devem ter identidades distintas.")
        return self


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_comparison_manifest(path: str | Path, manifest: ComparisonManifest) -> Path:
    manifest.updated_at = utc_now()
    validated = ComparisonManifest.model_validate(manifest.model_dump())
    return atomic_write_text(path, validated.model_dump_json(indent=2))


def artifact_record(path: str | Path, *, name: str | None = None) -> ArtifactRecord:
    artifact_path = Path(path)
    if not artifact_path.is_file():
        raise ContractError(f"Artefato ausente: {artifact_path}")
    return ArtifactRecord(
        name=name or artifact_path.name,
        path=str(artifact_path),
        sha256=file_sha256(artifact_path),
        size_bytes=artifact_path.stat().st_size,
    )


def write_result(path: str | Path, result: CanonicalResult) -> Path:
    result_path = Path(path)
    return atomic_write_text(result_path, result.model_dump_json(indent=2))


def load_result(
    path: str | Path,
    *,
    node_id: str | None = None,
    attempt: int | None = None,
    mode: ContractMode | None = None,
) -> CanonicalResult:
    result_path = Path(path)
    if not result_path.is_file():
        raise ContractError(f"Resultado ausente: {result_path}")
    try:
        result = CanonicalResult.model_validate_json(result_path.read_text())
    except Exception as exc:
        raise ContractError(f"Resultado inválido em {result_path}: {exc}") from exc
    expected = {"node_id": node_id, "attempt": attempt}
    for field, value in expected.items():
        if value is not None and getattr(result, field) != value:
            raise ContractError(
                f"Identidade inválida: {field}={getattr(result, field)!r}, esperado {value!r}."
            )
    if mode is not None and result.execution.mode != mode:
        raise ContractError(
            f"Modo inválido: {result.execution.mode!r}, esperado {mode!r}."
        )
    for artifact in result.artifacts:
        artifact_path = Path(artifact.path)
        if not artifact_path.is_file():
            raise ContractError(f"Artefato declarado ausente: {artifact.path}")
        if artifact_path.stat().st_size != artifact.size_bytes:
            raise ContractError(f"Tamanho divergente para {artifact.path}")
        if file_sha256(artifact_path) != artifact.sha256:
            raise ContractError(f"Hash divergente para {artifact.path}")
    return result


def canonicalize_attempt(
    attempt_dir: str | Path,
    *,
    node_id: str,
    attempt: int,
    mode: ContractMode,
    primary_metric: str,
) -> Path:
    directory = Path(attempt_dir)
    raw_result_path = directory / "raw_results.json"
    evidence_path = directory / "execution.json"
    artifacts = [
        artifact_record(raw_result_path, name="raw-result"),
        artifact_record(evidence_path, name="execution-evidence"),
    ]
    if mode == "live":
        artifacts.append(artifact_record(directory / "code.py", name="generated-code"))

    try:
        evidence = ExecutionEvidence.model_validate_json(evidence_path.read_text())
    except Exception as exc:
        raise ContractError(f"Evidência de execução inválida: {exc}") from exc
    if evidence.mode != mode:
        raise ContractError(
            f"Modo da evidência inválido: {evidence.mode!r}, esperado {mode!r}."
        )
    for name, artifact_path in (
        ("stdout", evidence.stdout_path),
        ("stderr", evidence.stderr_path),
    ):
        if artifact_path:
            artifacts.append(artifact_record(artifact_path, name=name))

    adapted = adapt_legacy_result(
        raw_result_path,
        node_id=node_id,
        attempt=attempt,
        mode=mode,
        primary_metric=primary_metric,
    )
    try:
        canonical = CanonicalResult(
            **adapted.model_dump(exclude={"execution", "artifacts"}),
            execution=evidence,
            artifacts=artifacts,
        )
    except Exception as exc:
        raise ContractError(f"Tentativa inválida: {exc}") from exc
    result_path = write_result(directory / "results.json", canonical)
    load_result(result_path, node_id=node_id, attempt=attempt, mode=mode)
    return result_path


def _resolve_legacy_path(data: dict[str, Any], metric_path: str) -> Any:
    current: Any = data
    for part in metric_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ContractError(f"Caminho legado inexistente: {metric_path}")
        current = current[part]
    return current


def adapt_legacy_result(
    path: str | Path,
    *,
    node_id: str,
    attempt: int,
    mode: ContractMode,
    primary_metric: str,
    metric_path: str | None = None,
    reduction: Literal["scalar", "max", "mean"] = "scalar",
) -> CanonicalResult:
    legacy_path = Path(path)
    try:
        data = json.loads(legacy_path.read_text(), parse_constant=lambda value: value)
    except Exception as exc:
        raise ContractError(f"JSON legado inválido em {legacy_path}: {exc}") from exc

    selected_path = metric_path or primary_metric
    if metric_path is None and (
        primary_metric not in data or isinstance(data[primary_metric], (dict, list))
    ):
        raise ContractError(
            "Resultado legado aninhado requer metric_path explícito; adaptação automática é ambígua."
        )
    value = _resolve_legacy_path(data, selected_path)
    if reduction == "scalar":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ContractError("O caminho legado não aponta para uma métrica escalar.")
        metric_value = float(value)
    else:
        if not isinstance(value, list) or not value:
            raise ContractError("A redução legada requer uma lista numérica não vazia.")
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
            raise ContractError("A lista legada contém valor não numérico.")
        values = [float(item) for item in value]
        metric_value = max(values) if reduction == "max" else sum(values) / len(values)

    try:
        return CanonicalResult(
            node_id=node_id,
            attempt=attempt,
            status="SUCCEEDED",
            primary_metric=primary_metric,
            metrics={primary_metric: metric_value},
            execution=ExecutionEvidence(
                mode=mode,
                synthetic=mode == "mock",
                network_used=mode == "live",
                return_code=0,
            ),
            artifacts=[artifact_record(legacy_path, name="legacy-source")],
            source="legacy-adapter",
        )
    except Exception as exc:
        raise ContractError(f"Métrica legada inválida: {exc}") from exc


def save_manifest(path: str | Path, manifest: RunManifest) -> Path:
    manifest_path = Path(path)
    manifest.updated_at = utc_now()
    return atomic_write_text(manifest_path, manifest.model_dump_json(indent=2))


def load_manifest(path: str | Path) -> RunManifest:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ContractError(f"Manifesto ausente: {manifest_path}")
    try:
        return RunManifest.model_validate_json(manifest_path.read_text())
    except Exception as exc:
        raise ContractError(f"Manifesto inválido em {manifest_path}: {exc}") from exc
