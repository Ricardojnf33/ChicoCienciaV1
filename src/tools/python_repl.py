import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from src.core.atomic_io import atomic_write_text
from src.core.contracts import ExecutionEvidence


class SandboxUnavailableError(RuntimeError):
    """Raised when a live run cannot obtain OS-level network isolation."""


@dataclass(frozen=True)
class SandboxLaunch:
    backend: str
    prefix: tuple[str, ...]
    image_id: str | None = None
    container_name: str | None = None


class PythonRunnerTool:
    name = "python_runner"
    _SAFE_ENV_KEYS = ("LANG", "LC_ALL", "TZ")

    def __init__(
        self,
        *,
        require_network_isolation: bool = True,
        cpu_seconds: int = 120,
        memory_mb: int = 2048,
        output_mb: int = 32,
        runner_image: str | None = None,
    ):
        self.require_network_isolation = require_network_isolation
        self.cpu_seconds = cpu_seconds
        self.memory_mb = memory_mb
        self.output_mb = output_mb
        self.runner_image = runner_image or os.getenv(
            "CHICO_RUNNER_IMAGE", "chico-science-runner:phase5"
        )

    def _sanitized_environment(self) -> dict[str, str]:
        environment = {
            key: os.environ[key]
            for key in self._SAFE_ENV_KEYS
            if key in os.environ
        }
        environment.update(
            {
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLBACKEND": "Agg",
            }
        )
        return environment

    def _bwrap_prefix(self, workdir: Path) -> list[str]:
        executable = shutil.which("bwrap")
        if not executable:
            raise SandboxUnavailableError("bubblewrap não está instalado")
        readonly_paths = {
            Path("/bin"),
            Path("/lib"),
            Path("/lib64"),
            Path("/usr"),
            Path(sys.base_prefix).resolve(),
            Path(sys.prefix).resolve(),
        }
        arguments = [
            executable,
            "--die-with-parent",
            "--unshare-all",
            "--cap-drop",
            "ALL",
        ]
        for source in sorted(readonly_paths, key=lambda path: (len(path.parts), str(path))):
            if source.exists() and not source.is_relative_to(workdir):
                arguments.extend(["--ro-bind", str(source), str(source)])
        loader_cache = Path("/etc/ld.so.cache")
        if loader_cache.is_file():
            arguments.extend(["--ro-bind", str(loader_cache), str(loader_cache)])
        arguments.extend(
            [
                "--dev",
                "/dev",
                "--proc",
                "/proc",
                "--tmpfs",
                "/tmp",
                "--bind",
                str(workdir),
                str(workdir),
                "--chdir",
                str(workdir),
            ]
        )
        return arguments

    def _docker_prefix(self, workdir: Path, *, container_name: str) -> list[str]:
        executable = shutil.which("docker")
        if not executable:
            raise SandboxUnavailableError("Docker não está instalado")
        return [
            executable,
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "128",
            "--memory",
            f"{self.memory_mb}m",
            "--cpus",
            "1.0",
            "--ulimit",
            f"cpu={self.cpu_seconds}:{self.cpu_seconds + 1}",
            "--ulimit",
            f"fsize={self.output_mb * 1024 * 1024}:{self.output_mb * 1024 * 1024}",
            "--ulimit",
            "core=0:0",
            "--ulimit",
            "nofile=128:128",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount",
            f"type=bind,src={workdir},dst=/work",
            "--workdir",
            "/work",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--env",
            "PYTHONUNBUFFERED=1",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "MPLBACKEND=Agg",
            self.runner_image,
            "python",
        ]

    def _run_probe(
        self, command: list[str], *, timeout: int = 30
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=self._sanitized_environment(),
        )

    @staticmethod
    def _isolation_probe_code() -> str:
        return (
            "import os,socket,sys;"
            "import matplotlib,numpy,pandas,PIL,polars,sklearn,yaml;"
            "sys.exit(41) if os.getenv('OPENAI_API_KEY') else None;"
            "s=socket.socket();s.settimeout(.5);"
            "r=0;"
            "\ntry:s.connect(('1.1.1.1',443));r=42"
            "\nexcept OSError:r=0"
            "\nfinally:s.close()"
            "\nsys.exit(r)"
        )

    @staticmethod
    def _probe_detail(result: subprocess.CompletedProcess | None, missing: str) -> str:
        if result is None:
            return missing
        detail = result.stderr.decode(errors="replace").strip()[-300:]
        return detail or str(result.returncode)

    def _docker_image_id(self, executable: str) -> str:
        result = self._run_probe(
            [executable, "image", "inspect", "--format", "{{.Id}}", self.runner_image]
        )
        if result.returncode != 0:
            raise SandboxUnavailableError(
                "imagem do runner indisponível: " + self._probe_detail(result, "sem imagem")
            )
        image_id = result.stdout.decode(errors="replace").strip()
        if not image_id.startswith("sha256:"):
            raise SandboxUnavailableError("Docker retornou identidade de imagem inválida")
        return image_id

    def _sandbox_launch(self, workdir: Path) -> SandboxLaunch:
        probe_code = self._isolation_probe_code()
        bwrap_result = None
        if shutil.which("bwrap"):
            bwrap_prefix = self._bwrap_prefix(workdir)
            bwrap_result = self._run_probe(
                [*bwrap_prefix, sys.executable, "-c", probe_code]
            )
            if bwrap_result.returncode == 0:
                return SandboxLaunch(backend="bwrap", prefix=tuple(bwrap_prefix))

        docker_result = None
        docker = shutil.which("docker")
        if docker:
            image_id = self._docker_image_id(docker)
            container_name = f"chico-runner-{uuid.uuid4().hex}"
            docker_prefix = self._docker_prefix(
                workdir, container_name=container_name
            )
            docker_result = self._run_probe([*docker_prefix, "-c", probe_code])
            if docker_result.returncode == 0:
                return SandboxLaunch(
                    backend="docker",
                    prefix=tuple(docker_prefix),
                    image_id=image_id,
                    container_name=container_name,
                )

        raise SandboxUnavailableError(
            "isolamento de rede indisponível no host; "
            "bubblewrap="
            + self._probe_detail(bwrap_result, "indisponível")
            + "; docker="
            + self._probe_detail(docker_result, "indisponível")
        )

    def _limit_prefix(self) -> list[str]:
        executable = shutil.which("prlimit")
        if not executable:
            raise SandboxUnavailableError("prlimit não está instalado")
        return [
            executable,
            f"--cpu={self.cpu_seconds}:{self.cpu_seconds + 1}",
            f"--as={self.memory_mb * 1024 * 1024}:{self.memory_mb * 1024 * 1024}",
            f"--fsize={self.output_mb * 1024 * 1024}:{self.output_mb * 1024 * 1024}",
            "--core=0:0",
            "--nofile=128:128",
            "--",
        ]

    def preflight(self, workdir: str | Path) -> dict[str, object]:
        """Validate runner boundaries without executing generated project code."""
        workdir_path = Path(workdir).resolve()
        workdir_path.mkdir(parents=True, exist_ok=True)
        self._limit_prefix()
        if self.require_network_isolation:
            launch = self._sandbox_launch(workdir_path)
            sandbox_backend = launch.backend
            sandbox_image_id = launch.image_id
        else:
            sandbox_backend = "disabled"
            sandbox_image_id = None
        sanitized_keys = set(self._sanitized_environment())
        sensitive_keys = {
            key
            for key in os.environ
            if any(marker in key.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
        }
        forwarded_sensitive = sorted(sanitized_keys & sensitive_keys)
        if forwarded_sensitive:
            raise RuntimeError(
                "O ambiente sanitizado encaminharia nomes sensíveis: "
                + ", ".join(forwarded_sensitive)
            )
        return {
            "network_isolation_required": self.require_network_isolation,
            "network_isolation_available": self.require_network_isolation,
            "sandbox_backend": sandbox_backend,
            "sandbox_image_id": sandbox_image_id,
            "resource_limits_available": True,
            "forwarded_sensitive_environment_names": forwarded_sensitive,
        }

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen, grace_seconds: float = 1.0) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=grace_seconds)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

    def _remove_container(self, launch: SandboxLaunch) -> None:
        if launch.backend != "docker" or not launch.container_name:
            return
        executable = shutil.which("docker")
        if not executable:
            return
        subprocess.run(
            [executable, "rm", "--force", launch.container_name],
            capture_output=True,
            timeout=10,
            check=False,
            env=self._sanitized_environment(),
        )

    @staticmethod
    def _tail(path: Path, limit: int = 4000) -> str:
        if not path.is_file():
            return ""
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - limit))
            return stream.read().decode(errors="replace")

    def run_script(
        self,
        code_path: str,
        workdir: str | None = None,
        timeout: int = 180,
        evidence_path: str | None = None,
    ) -> dict[str, object]:
        code_path_abs = Path(code_path).resolve()
        workdir_abs = Path(workdir).resolve() if workdir else code_path_abs.parent
        if not code_path_abs.is_file():
            raise FileNotFoundError(code_path_abs)
        if not code_path_abs.is_relative_to(workdir_abs):
            raise ValueError("O código precisa estar contido no diretório de trabalho.")

        network_isolated = self.require_network_isolation
        launch = self._sandbox_launch(workdir_abs) if network_isolated else None
        if launch is None:
            command = [*self._limit_prefix(), sys.executable, str(code_path_abs)]
            sandbox_backend = "disabled"
            sandbox_image_id = None
        elif launch.backend == "docker":
            container_path = Path("/work") / code_path_abs.relative_to(workdir_abs)
            command = [*launch.prefix, str(container_path)]
            sandbox_backend = launch.backend
            sandbox_image_id = launch.image_id
        else:
            command = [
                *self._limit_prefix(),
                *launch.prefix,
                sys.executable,
                str(code_path_abs),
            ]
            sandbox_backend = launch.backend
            sandbox_image_id = launch.image_id
        stdout_path = workdir_abs / "stdout.log"
        stderr_path = workdir_abs / "stderr.log"
        started = time.monotonic()
        timed_out = False
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                command,
                cwd=str(workdir_abs),
                env=self._sanitized_environment(),
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._terminate_process_group(process)
                if launch is not None:
                    self._remove_container(launch)
                return_code = 124

        duration = time.monotonic() - started
        evidence = ExecutionEvidence(
            mode="live",
            synthetic=False,
            network_used=False,
            network_isolated=network_isolated,
            sandbox_backend=sandbox_backend,
            sandbox_image_id=sandbox_image_id,
            return_code=return_code,
            timed_out=timed_out,
            duration_seconds=duration,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )
        target_evidence = Path(evidence_path) if evidence_path else workdir_abs / "execution.json"
        atomic_write_text(target_evidence, evidence.model_dump_json(indent=2))
        return {
            "returncode": return_code,
            "stdout": self._tail(stdout_path),
            "stderr": self._tail(stderr_path),
            "timed_out": timed_out,
            "duration_seconds": duration,
            "evidence_path": str(target_evidence),
            "network_isolated": network_isolated,
            "sandbox_backend": sandbox_backend,
            "sandbox_image_id": sandbox_image_id,
        }
