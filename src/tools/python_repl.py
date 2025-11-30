import subprocess
import sys
from pathlib import Path

class PythonRunnerTool:
    name = "python_runner"

    def run_script(self, code_path: str, workdir: str | None = None, timeout: int = 180):
        # Resolve code_path to absolute path first
        code_path_abs = Path(code_path).resolve()
        
        # Default workdir to parent of code_path
        if workdir:
            workdir_abs = Path(workdir).resolve()
        else:
            workdir_abs = code_path_abs.parent
        
        proc = subprocess.run(
            [sys.executable, str(code_path_abs)],
            cwd=str(workdir_abs),
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
