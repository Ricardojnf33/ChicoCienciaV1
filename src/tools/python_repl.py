import subprocess
import sys
from pathlib import Path

class PythonRunnerTool:
    name = "python_runner"

    def run_script(self, code_path: str, workdir: str | None = None, timeout: int = 180):
        workdir = workdir or str(Path(code_path).parent)
        proc = subprocess.run(
            [sys.executable, code_path],
            cwd=workdir,
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
