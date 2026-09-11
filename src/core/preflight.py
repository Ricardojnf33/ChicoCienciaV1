import platform
import tempfile
from datetime import datetime
from enum import Enum
from importlib.metadata import version
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from src.config.settings import Settings
from src.core.atomic_io import atomic_write_text
from src.core.contracts import utc_now
from src.tools.python_repl import PythonRunnerTool


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class PreflightCheck(BaseModel):
    name: str = Field(min_length=1)
    status: CheckStatus
    detail: str = Field(min_length=1)


class PreflightReport(BaseModel):
    schema_version: str = "1.0"
    created_at: datetime = Field(default_factory=utc_now)
    status: CheckStatus
    api_calls_performed: int = 0
    objective_path: str
    model_text: str
    model_vision: str
    checks: list[PreflightCheck]


def _redact(detail: object, secrets: list[str]) -> str:
    redacted = str(detail)
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "**********")
    return redacted


def run_preflight(
    *,
    settings: Settings,
    objective_path: str,
    require_sandbox: bool,
    runner_factory: Callable[..., PythonRunnerTool] = PythonRunnerTool,
) -> PreflightReport:
    """Run local gates only. This function never calls an OpenAI endpoint."""
    checks: list[PreflightCheck] = []
    secrets = []

    def check(name: str, action: Callable[[], str]) -> None:
        try:
            detail = action()
            checks.append(PreflightCheck(name=name, status=CheckStatus.PASS, detail=detail))
        except Exception as exc:
            checks.append(
                PreflightCheck(
                    name=name,
                    status=CheckStatus.FAIL,
                    detail=_redact(exc, secrets),
                )
            )

    def credential_check() -> str:
        secret = settings.require_openai_api_key()
        secrets.append(secret)
        serialized = settings.model_dump_json()
        if secret in serialized or secret in repr(settings):
            raise ValueError("A credencial apareceu na serialização de Settings.")
        return "OPENAI_API_KEY presente e mascarada; valor não registrado."

    def runtime_check() -> str:
        if platform.python_version_tuple()[:2] != ("3", "11"):
            raise ValueError(f"Python incompatível: {platform.python_version()}")
        __import__("crewai")
        return (
            f"Python {platform.python_version()}; CrewAI {version('crewai')}; "
            f"setuptools {version('setuptools')}."
        )

    def objective_check() -> str:
        path = Path(objective_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        return f"Objetivo legível: {path}."

    def model_check() -> str:
        if not settings.MODEL_TEXT.strip() or not settings.MODEL_VISION.strip():
            raise ValueError("Modelo textual ou visual vazio.")
        return (
            f"Modelo textual={settings.MODEL_TEXT}; modelo visual={settings.MODEL_VISION}."
        )

    def runner_check() -> str:
        runner = runner_factory(require_network_isolation=require_sandbox)
        with tempfile.TemporaryDirectory(prefix="chico-preflight-") as directory:
            result = runner.preflight(directory)
        return (
            "Runner sem nomes sensíveis; limites disponíveis; "
            f"isolamento obrigatório={result['network_isolation_required']}."
        )

    check("credential", credential_check)
    check("runtime", runtime_check)
    check("objective", objective_check)
    check("models", model_check)
    check("runner", runner_check)
    status = (
        CheckStatus.PASS
        if all(item.status is CheckStatus.PASS for item in checks)
        else CheckStatus.FAIL
    )
    return PreflightReport(
        status=status,
        objective_path=objective_path,
        model_text=settings.MODEL_TEXT,
        model_vision=settings.MODEL_VISION,
        checks=checks,
    )


def write_preflight(path: str | Path, report: PreflightReport) -> Path:
    return atomic_write_text(path, report.model_dump_json(indent=2))
