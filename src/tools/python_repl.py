import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from src.core.atomic_io import atomic_write_text
from src.core.contracts import ExecutionEvidence


class SandboxUnavailableError(RuntimeError):
    """Raised when a live run cannot obtain OS-level network isolation."""


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
    ):
        self.require_network_isolation = require_network_isolation
        self.cpu_seconds = cpu_seconds
        self.memory_mb = memory_mb
        self.output_mb = output_mb

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

    def _sandbox_arguments(
        self, workdir: Path, *, privileged_launcher: bool
    ) -> list[str]:
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
        ]
        if privileged_launcher:
            # GitHub-hosted runners permit passwordless sudo but can reject
            # unprivileged network namespaces. Root creates the namespaces and
            # bubblewrap drops back to the runner identity before Python starts.
            arguments.extend(
                [
                    "--unshare-pid",
                    "--unshare-net",
                    "--unshare-ipc",
                    "--unshare-uts",
                    "--unshare-cgroup-try",
                    "--gid",
                    str(os.getgid()),
                    "--uid",
                    str(os.getuid()),
                ]
            )
        else:
            arguments.append("--unshare-all")
        arguments.extend(["--cap-drop", "ALL"])
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

    @staticmethod
    def _probe_sandbox(arguments: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [*arguments, sys.executable, "-c", "pass"],
            capture_output=True,
            timeout=5,
            check=False,
        )

    def _sandbox_prefix(self, workdir: Path) -> list[str]:
        arguments = self._sandbox_arguments(workdir, privileged_launcher=False)
        probe = self._probe_sandbox(arguments)
        if probe.returncode == 0:
            return arguments

        sudo = shutil.which("sudo")
        if sudo:
            privileged_arguments = self._sandbox_arguments(
                workdir, privileged_launcher=True
            )
            privileged_prefix = [sudo, "--non-interactive", *privileged_arguments]
            privileged_probe = self._probe_sandbox(privileged_prefix)
            if privileged_probe.returncode == 0:
                return privileged_prefix

        if probe.returncode != 0:
            detail = probe.stderr.decode(errors="replace").strip()[-300:]
            raise SandboxUnavailableError(
                f"isolamento de rede indisponível no host: {detail or probe.returncode}"
            )
        return arguments

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
            sandbox_prefix = self._sandbox_prefix(workdir_path)
            sandbox_backend = (
                "sudo-bwrap" if Path(sandbox_prefix[0]).name == "sudo" else "bwrap"
            )
        else:
            sandbox_backend = "disabled"
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
        prefix = self._sandbox_prefix(workdir_abs) if network_isolated else []
        limits = self._limit_prefix()
        stdout_path = workdir_abs / "stdout.log"
        stderr_path = workdir_abs / "stderr.log"
        started = time.monotonic()
        timed_out = False
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                [*limits, *prefix, sys.executable, str(code_path_abs)],
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
                return_code = 124

        duration = time.monotonic() - started
        evidence = ExecutionEvidence(
            mode="live",
            synthetic=False,
            network_used=False,
            network_isolated=network_isolated,
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
        }
